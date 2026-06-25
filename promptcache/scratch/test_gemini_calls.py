import httpx
import json
import time

PROXY_URL = "http://127.0.0.1:8000/v1/chat/completions"

# Generate a large body of text to trigger Gemini caching (must be >1024 tokens)
large_context = """
Prompt caching is a powerful optimization technique for large language models. It stores the key-value states
of parsed prompt prefixes in a fast memory cache so that subsequent requests with matching prefixes do not need
to re-evaluate them. This is especially beneficial for long system instructions, large documentation libraries,
code repositories, or long multi-turn conversations.
""" * 50  # This will be about 2500 words / ~3500 tokens, well above the 1024 caching threshold.

print("--- Test Call 1: Initiating with large context for caching ---")
payload_1 = {
    "model": "gemini-2.5-flash",
    "messages": [
        {"role": "system", "content": "You are a database analyzer. Use the following context to answer questions."},
        {"role": "user", "content": f"Context documentation: {large_context}\n\nQuestion: Summarize this context in one sentence."}
    ],
    "temperature": 0.0
}

try:
    start_time = time.time()
    response_1 = httpx.post(
        PROXY_URL,
        json=payload_1,
        headers={"User-Agent": "Antigravity IDE/TestClient"},
        timeout=60.0
    )
    latency_1 = time.time() - start_time
    print(f"Status Code: {response_1.status_code}")
    print(f"Latency: {latency_1:.2f} seconds")
    if response_1.status_code == 200:
        res_data = response_1.json()
        print("Response:", res_data["choices"][0]["message"]["content"])
        print("Usage Info:", json.dumps(res_data.get("usage", {}), indent=2))
except Exception as e:
    print(f"Error during call 1: {e}")

print("\n--- Test Call 2: Sending a second call with identical prefix to test cache hit ---")
# Keep system and user context exactly the same, but ask a different question
payload_2 = {
    "model": "gemini-2.5-flash",
    "messages": [
        {"role": "system", "content": "You are a database analyzer. Use the following context to answer questions."},
        {"role": "user", "content": f"Context documentation: {large_context}\n\nQuestion: What is the main benefit of prompt caching according to the text?"}
    ],
    "temperature": 0.0
}

try:
    start_time = time.time()
    response_2 = httpx.post(
        PROXY_URL,
        json=payload_2,
        headers={"User-Agent": "Antigravity IDE/TestClient"},
        timeout=60.0
    )
    latency_2 = time.time() - start_time
    print(f"Status Code: {response_2.status_code}")
    print(f"Latency: {latency_2:.2f} seconds")
    if response_2.status_code == 200:
        res_data = response_2.json()
        print("Response:", res_data["choices"][0]["message"]["content"])
        print("Usage Info:", json.dumps(res_data.get("usage", {}), indent=2))
        print(f"Speedup: {latency_1 / latency_2:.2f}x faster!")
except Exception as e:
    print(f"Error during call 2: {e}")

print("\n--- Test Call 3: Testing History Compression (>20 turns) ---")
# Build a long chat history with 25 turns to trigger history compression (limit is 20)
messages_history = [
    {"role": "system", "content": "You are a helpful assistant."}
]
for i in range(12):
    messages_history.append({"role": "user", "content": f"Ping {i}"})
    messages_history.append({"role": "assistant", "content": f"Pong {i}"})
# Adding 13th turn to make it 27 total messages (1 system + 26 user/assistant)
messages_history.append({"role": "user", "content": "Final message to test compression"})

payload_3 = {
    "model": "gemini-2.5-flash",
    "messages": messages_history,
    "temperature": 0.0
}

try:
    print(f"Sending request with {len(messages_history)} messages.")
    response_3 = httpx.post(
        PROXY_URL,
        json=payload_3,
        headers={"User-Agent": "Antigravity IDE/TestClient"},
        timeout=60.0
    )
    print(f"Status Code: {response_3.status_code}")
    if response_3.status_code == 200:
        res_data = response_3.json()
        print("Response:", res_data["choices"][0]["message"]["content"])
        print("Check proxy server logs to see the 'Compressed OpenAI/Gemini history from 27 to 20 messages' output!")
except Exception as e:
    print(f"Error during call 3: {e}")
