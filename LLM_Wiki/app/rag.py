import os
import re
import math
import logging
from typing import List, Dict, Any, Optional
from google import genai
import httpx
from app.config import settings

logger = logging.getLogger(__name__)

# Configure Google GenAI client
_genai_client: Optional[genai.Client] = None
if settings.GEMINI_API_KEY:
    _genai_client = genai.Client(
        api_key=settings.GEMINI_API_KEY,
        http_options={"api_version": "v1"}
    )


class RAGSystem:
    def __init__(self):
        # In-memory document store
        # Format: [{"path": str, "metadata": dict, "text_content": str, "embedding": List[float]}]
        self.documents: List[Dict[str, Any]] = []

    def parse_markdown(self, filename: str, content: str) -> Dict[str, Any]:
        """
        Parses an Obsidian markdown file to extract frontmatter and content.
        """
        metadata = {
            "title": filename.replace(".md", ""),
            "date": "",
            "asker_id": "",
            "question": "",
            "tags": []
        }

        # Regex to parse frontmatter
        frontmatter_match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", content, re.DOTALL)

        body_content = content
        if frontmatter_match:
            frontmatter_text = frontmatter_match.group(1)
            body_content = frontmatter_match.group(2)

            # Simple YAML parser
            for line in frontmatter_text.split("\n"):
                if ":" in line:
                    key, val = line.split(":", 1)
                    key = key.strip().lower()
                    val = val.strip()
                    if key == "date":
                        metadata["date"] = val
                    elif key == "asker_id":
                        metadata["asker_id"] = val.strip('"').strip("'")
                    elif key == "question":
                        metadata["question"] = val.strip('"').strip("'")
                    elif key == "tags":
                        # clean tag brackets if present like [tag1, tag2]
                        cleaned_val = val.replace("[", "").replace("]", "")
                        metadata["tags"] = [t.strip() for t in cleaned_val.split(",") if t.strip()]

        # If question not in frontmatter, try to parse it from the body
        if not metadata["question"]:
            q_match = re.search(r"# Question\s*\n(.*?)(?=\n#|$)", body_content, re.DOTALL)
            if q_match:
                metadata["question"] = q_match.group(1).strip()

        return {
            "metadata": metadata,
            "text_content": body_content.strip()
        }

    def compute_cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        """
        Computes the cosine similarity between two vectors.
        """
        if not v1 or not v2 or len(v1) != len(v2):
            return 0.0
        dot_product = sum(a * b for a, b in zip(v1, v2))
        magnitude1 = math.sqrt(sum(a * a for a in v1))
        magnitude2 = math.sqrt(sum(b * b for b in v2))
        if magnitude1 * magnitude2 == 0:
            return 0.0
        return dot_product / (magnitude1 * magnitude2)

    async def get_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generates text embedding using Google GenAI (text-embedding-004).
        """
        if not _genai_client:
            logger.warning("GEMINI_API_KEY is not configured. Cannot generate embeddings.")
            return None

        try:
            result = _genai_client.models.embed_content(
                model="text-embedding-004",
                contents=text,
            )
            return result.embeddings[0].values
        except Exception as e:
            logger.error(f"Failed to generate embedding for text: {e}")
            return None

    async def initialize_index(self):
        """
        Fetches all files from GitHub, parses them, embeds them, and stores them in memory.
        """
        from app.github_client import github_client

        logger.info("Initializing RAG Index from GitHub...")
        files = await github_client.list_markdown_files()

        loaded_docs = []
        for file_info in files:
            content = await github_client.download_file_content(file_info["download_url"])
            if content:
                parsed = self.parse_markdown(file_info["name"], content)
                # Combine question + answer context for embedding
                searchable_text = f"\u0627\u0644\u0633\u0624\u0627\u0644: {parsed['metadata']['question']}\n\u0627\u0644\u062c\u0648\u0627\u0628: {parsed['text_content']}"
                embedding = await self.get_embedding(searchable_text)

                if embedding:
                    loaded_docs.append({
                        "path": file_info["path"],
                        "name": file_info["name"],
                        "metadata": parsed["metadata"],
                        "text_content": parsed["text_content"],
                        "embedding": embedding
                    })
                    logger.info(f"Indexed {file_info['name']}")
                else:
                    logger.warning(f"Skipped {file_info['name']} due to missing embedding.")

        self.documents = loaded_docs
        logger.info(f"RAG Index initialization completed. Indexed {len(self.documents)} documents.")

    async def add_document(self, filename: str, path: str, content: str):
        """
        Parses, embeds, and appends a single document to the index.
        """
        parsed = self.parse_markdown(filename, content)
        searchable_text = f"\u0627\u0644\u0633\u0624\u0627\u0644: {parsed['metadata']['question']}\n\u0627\u0644\u062c\u0648\u0627\u0628: {parsed['text_content']}"
        embedding = await self.get_embedding(searchable_text)

        if embedding:
            doc = {
                "path": path,
                "name": filename,
                "metadata": parsed["metadata"],
                "text_content": parsed["text_content"],
                "embedding": embedding
            }
            # Remove existing document with same path if it exists, then append
            self.documents = [d for d in self.documents if d["path"] != path]
            self.documents.append(doc)
            logger.info(f"Added/Updated document in RAG Index: {filename}")
        else:
            logger.error(f"Failed to generate embedding for newly added document: {filename}")

    async def generate_llm_response(self, prompt: str) -> str:
        """
        Generates completions from either Google AI Studio or OpenRouter depending on config.
        """
        if settings.USE_OPENROUTER and settings.OPENROUTER_API_KEY:
            logger.info(f"Querying OpenRouter LLM using model: {settings.OPENROUTER_MODEL}")
            async with httpx.AsyncClient(timeout=30.0) as client:
                try:
                    res = await client.post(
                        "https://openrouter.ai/api/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                            "Content-Type": "application/json",
                            "HTTP-Referer": "https://github.com/Atomicphoenix1/ANtiGrav-proj",
                            "X-Title": "Antigravity LLM Wiki"
                        },
                        json={
                            "model": settings.OPENROUTER_MODEL,
                            "messages": [{"role": "user", "content": prompt}],
                            "temperature": 0.2
                        }
                    )
                    res.raise_for_status()
                    data = res.json()
                    return data["choices"][0]["message"]["content"]
                except Exception as e:
                    logger.error(f"OpenRouter LLM generation error: {e}")
                    raise e
        else:
            logger.info("Querying Google AI Studio (Gemini) directly...")
            if not _genai_client:
                raise ValueError("Neither GEMINI_API_KEY nor OPENROUTER_API_KEY is configured.")
            try:
                response = _genai_client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=prompt,
                    config={
                        "temperature": 0.2,
                    }
                )
                return response.text
            except Exception as e:
                logger.error(f"Gemini LLM generation error: {e}")
                raise e

    async def search_and_answer(self, query: str, similarity_threshold: float = 0.6) -> Dict[str, Any]:
        """
        Searches documents in memory, retrieves matching ones, and asks Gemini to answer with citations.
        """
        # 1. Generate query embedding
        query_embedding = await self.get_embedding(query)
        if not query_embedding or not self.documents:
            return {
                "answer": "\u0639\u0630\u0631\u064b\u0627\u060c \u0644\u0645 \u064a\u062a\u0645 \u0627\u0644\u0639\u062b\u0648\u0631 \u0639\u0644\u0649 \u0641\u062a\u0627\u0648\u0649 \u0633\u0627\u0628\u0642\u0629 \u0645\u0634\u0627\u0628\u0647\u0629 \u0641\u064a \u0642\u0627\u0639\u062f\u0629 \u0627\u0644\u0628\u064a\u0627\u0646\u0627\u062a.",
                "citations": [],
                "found_match": False
            }

        # 2. Calculate similarities
        matches = []
        for doc in self.documents:
            sim = self.compute_cosine_similarity(query_embedding, doc["embedding"])
            if sim >= similarity_threshold:
                matches.append((sim, doc))

        # Sort matches by similarity descending
        matches.sort(key=lambda x: x[0], reverse=True)

        if not matches:
            return {
                "answer": "\u0644\u0645 \u064a\u062a\u0645 \u0627\u0644\u0639\u062b\u0648\u0631 \u0639\u0644\u0649 \u0641\u062a\u0627\u0648\u0649 \u0633\u0627\u0628\u0642\u0629 \u0645\u0634\u0627\u0628\u0647\u0629 \u0641\u064a \u0642\u0627\u0639\u062f\u0629 \u0627\u0644\u0628\u064a\u0627\u0646\u0627\u062a.",
                "citations": [],
                "found_match": False
            }

        # 3. Compile context — use top 3 matches
        top_matches = matches[:3]
        context_parts = []
        citations = []

        for i, (score, doc) in enumerate(top_matches, 1):
            source_name = doc["metadata"]["title"]
            context_parts.append(
                f"[\u0627\u0644\u0645\u0635\u062f\u0631 {i}: {source_name}]\n"
                f"\u0627\u0644\u0633\u0624\u0627\u0644: {doc['metadata']['question']}\n"
                f"\u0627\u0644\u062c\u0648\u0627\u0628:\n{doc['text_content']}\n"
                f"---"
            )
            citations.append({
                "source": source_name,
                "score": round(score, 3),
                "date": doc["metadata"]["date"]
            })

        context_str = "\n\n".join(context_parts)

        # 4. Formulate Prompt
        prompt = (
            "\u0623\u0646\u062a \u0645\u0633\u0627\u0639\u062f \u0630\u0643\u0627\u0621 \u0627\u0635\u0637\u0646\u0627\u0639\u064a \u0645\u062a\u062e\u0635\u0635 \u0641\u064a \u0627\u0644\u0641\u062a\u0627\u0648\u0649 \u0627\u0644\u0634\u0631\u0639\u064a\u0629 \u0648\u0645\u0648\u062b\u0642 \u0644\u0642\u0627\u0639\u062f\u0629 \u0628\u064a\u0627\u0646\u0627\u062a \u0627\u0644\u0641\u062a\u0627\u0648\u0649 \u0627\u0644\u062e\u0627\u0635\u0629 \u0628\u0627\u0644\u0645\u0641\u062a\u064a.\n"
            "\u0645\u0647\u0645\u062a\u0643 \u0647\u064a \u0627\u0644\u0625\u062c\u0627\u0628\u0629 \u0628\u062f\u0642\u0629 \u0648\u0628\u0623\u0633\u0644\u0648\u0628 \u0627\u0644\u0645\u0641\u062a\u064a \u0639\u0644\u0649 \u0633\u0624\u0627\u0644 \u0627\u0644\u0633\u0627\u0626\u0644 \u0628\u0646\u0627\u0621\u064b \u0639\u0644\u0649 \u0627\u0644\u0641\u062a\u0627\u0648\u0649 \u0627\u0644\u0633\u0627\u0628\u0642\u0629 \u0627\u0644\u0645\u0648\u062c\u0648\u062f\u0629 \u0641\u064a \u0627\u0644\u0633\u064a\u0627\u0642 \u0623\u062f\u0646\u0627\u0647 \u0641\u0642\u0637.\n\n"
            "\u0642\u0648\u0627\u0639\u062f \u0645\u0647\u0645\u0629 \u062c\u062f\u0627\u064b:\n"
            "1. \u064a\u062c\u0628 \u0623\u0646 \u062a\u0633\u062a\u0646\u062f \u0641\u064a \u0625\u062c\u0627\u0628\u062a\u0643 \u062d\u0635\u0631\u0627\u064b \u0639\u0644\u0649 \u0627\u0644\u0641\u062a\u0627\u0648\u0649 \u0627\u0644\u0645\u0632\u0648\u062f\u0629 \u0641\u064a \u0627\u0644\u0633\u064a\u0627\u0642.\n"
            "2. \u064a\u062c\u0628 \u0623\u0646 \u062a\u0630\u0643\u0631 \u0627\u0644\u0645\u0631\u0627\u062c\u0639 \u0648\u0627\u0644\u0645\u0635\u0627\u062f\u0631 \u0628\u0648\u0636\u0648\u062d \u0641\u064a \u0646\u0647\u0627\u064a\u0629 \u0625\u062c\u0627\u0628\u062a\u0643 (\u0645\u062b\u0627\u0644: \u0645\u0633\u062a\u0646\u062f\u0627\u064b \u0625\u0644\u0649 \u0645\u0644\u0641: [\u0627\u0633\u0645 \u0627\u0644\u0645\u0644\u0641]).\n"
            "3. \u0625\u0630\u0627 \u0644\u0645 \u062a\u062c\u062f \u0625\u062c\u0627\u0628\u0629 \u0645\u0628\u0627\u0634\u0631\u0629 \u0623\u0648 \u0645\u0634\u0627\u0628\u0647\u0629 \u062c\u062f\u0627\u064b \u0641\u064a \u0627\u0644\u0633\u064a\u0627\u0642\u060c \u0623\u062c\u0628 \u0628\u0648\u0636\u0648\u062d \u0628\u0623\u0646\u0643 \u0644\u0645 \u062a\u0639\u062b\u0631 \u0639\u0644\u0649 \u0641\u062a\u0648\u0649 \u0633\u0627\u0628\u0642\u0629 \u0645\u0634\u0627\u0628\u0647\u0629\u060c \u0648\u062a\u062c\u0646\u0628 \u0627\u062e\u062a\u0631\u0627\u0639 \u0625\u062c\u0627\u0628\u0627\u062a \u0645\u0646 \u0639\u0646\u062f\u0643.\n"
            "4. \u0623\u062c\u0628 \u0628\u0627\u0644\u0644\u063a\u0629 \u0627\u0644\u0639\u0631\u0628\u064a\u0629 \u0627\u0644\u0641\u0635\u062d\u0649 \u0648\u0628\u0643\u0644 \u0623\u062f\u0628 \u0648\u0627\u062d\u062a\u0631\u0627\u0645.\n\n"
            f"\u0627\u0644\u0633\u064a\u0627\u0642 \u0645\u0646 \u0641\u062a\u0627\u0648\u0649 \u0627\u0644\u0645\u0641\u062a\u064a \u0627\u0644\u0633\u0627\u0628\u0642\u0629:\n{context_str}\n\n"
            f"\u0633\u0624\u0627\u0644 \u0627\u0644\u0633\u0627\u0626\u0644 \u0627\u0644\u062c\u062f\u064a\u062f:\n{query}\n\n"
            "\u0627\u0644\u0625\u062c\u0627\u0628\u0629 \u0627\u0644\u0645\u0648\u062b\u0642\u0629 \u0645\u0639 \u0627\u0644\u0645\u0635\u0627\u062f\u0631:"
        )

        try:
            answer = await self.generate_llm_response(prompt)
            return {
                "answer": answer.strip(),
                "citations": citations,
                "found_match": True
            }
        except Exception as e:
            logger.error(f"Error generating answer for query '{query}': {e}")
            return {
                "answer": "\u062d\u062f\u062b \u062e\u0637\u0623 \u0623\u062b\u0646\u0627\u0621 \u0627\u0644\u0627\u062a\u0635\u0627\u0644 \u0628\u0627\u0644\u0630\u0643\u0627\u0621 \u0627\u0644\u0627\u0635\u0637\u0646\u0627\u0639\u064a \u0644\u062a\u0648\u0644\u064a\u062f \u0627\u0644\u0625\u062c\u0627\u0628\u0629.",
                "citations": citations,
                "found_match": True  # We found matches, but LLM completion failed
            }


rag_system = RAGSystem()
