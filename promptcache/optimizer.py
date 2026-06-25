import copy
import logging

logger = logging.getLogger("cachepilot.optimizer")

def optimize_anthropic_payload(payload: dict) -> dict:
    """
    Optimizes Anthropic messages payload by injecting cache_control blocks.
    Anthropic allows up to 4 cache breakpoints ('ephemeral' cache type).
    """
    optimized = copy.deepcopy(payload)
    
    # 1. Standardize and cache system prompt
    system = optimized.get("system")
    system_has_cache = False
    
    if system:
        # Convert string system prompt to block format if needed
        if isinstance(system, str):
            system_blocks = [{"type": "text", "text": system}]
        elif isinstance(system, list):
            system_blocks = copy.deepcopy(system)
        else:
            system_blocks = []
            
        if system_blocks:
            # Set cache_control on the last block of the system prompt
            last_block = system_blocks[-1]
            if isinstance(last_block, dict):
                if last_block.get("type") in ["text", "document"]:
                    last_block["cache_control"] = {"type": "ephemeral"}
                    system_has_cache = True
            optimized["system"] = system_blocks

    # 2. Cache tools definition
    tools = optimized.get("tools")
    tools_has_cache = False
    if tools and isinstance(tools, list) and len(tools) > 0:
        # Anthropic allows setting cache_control on tool declarations directly
        # Inject to the last tool to cache the whole tools block
        try:
            tools[-1]["cache_control"] = {"type": "ephemeral"}
            tools_has_cache = True
        except Exception as e:
            logger.warning(f"Failed to inject cache to tools: {e}")

    # 3. Cache messages history
    messages = optimized.get("messages", [])
    if isinstance(messages, list) and len(messages) > 0:
        # Identify user message indexes to place caching checkpoints
        # Best practice is to cache messages at checkpoints (e.g. every few turns)
        # to ensure prompt prefix stays cached.
        user_message_indices = [
            i for i, msg in enumerate(messages) 
            if msg.get("role") == "user" and isinstance(msg.get("content"), (str, list))
        ]
        
        # We have up to 4 breakpoints total. If system and tools are cached, we have 2 remaining.
        available_breakpoints = 4 - (1 if system_has_cache else 0) - (1 if tools_has_cache else 0)
        
        if available_breakpoints > 0 and len(user_message_indices) > 0:
            # We want to cache historical checkpoints. 
            # E.g., if there are many turns, place a cache checkpoint near the middle, and one closer to the end,
            # but leave the very last user message uncached (unless it's the only one) to allow the cache
            # to be hit when a new turn begins.
            
            checkpoints_to_set = []
            if len(user_message_indices) >= 4:
                # If history is long, set one at ~1/3rd, one at ~2/3rds
                idx1 = user_message_indices[len(user_message_indices) // 3]
                idx2 = user_message_indices[(len(user_message_indices) * 2) // 3]
                checkpoints_to_set = [idx1, idx2]
            elif len(user_message_indices) >= 2:
                # If shorter, set one at the second to last user message
                idx = user_message_indices[-2]
                checkpoints_to_set = [idx]
            else:
                # Only 1 user message, set it there
                checkpoints_to_set = [user_message_indices[0]]
                
            # Keep only the number of checkpoints we can afford
            checkpoints_to_set = checkpoints_to_set[-available_breakpoints:]
            
            for idx in checkpoints_to_set:
                msg = messages[idx]
                content = msg.get("content")
                if isinstance(content, str):
                    # Convert string content to block content list to add cache_control
                    msg["content"] = [
                        {"type": "text", "text": content, "cache_control": {"type": "ephemeral"}}
                    ]
                elif isinstance(content, list) and len(content) > 0:
                    # Inject cache_control into the last block of the content list
                    last_c_block = content[-1]
                    if isinstance(last_c_block, dict):
                        last_c_block["cache_control"] = {"type": "ephemeral"}

    return optimized


def optimize_openai_payload(payload: dict) -> dict:
    """
    OpenAI handles prompt caching automatically at the backend level.
    To maximize hit rate, prompts must match exactly prefix-wise.
    We ensure system prompts, system instructions, and tool definitions are aligned.
    We also can trim / summarize old conversations to keep history prefix stable.
    """
    # Currently OpenAI automatic caching is fully handled by OpenAI server,
    # we just pass through or perform optional history management.
    return payload


def compress_history(messages: list, limit: int = 20) -> list:
    """
    Compresses conversation history by summarizing or removing oldest turns
    to optimize token counts and caching boundaries.
    """
    if len(messages) <= limit:
        return messages
        
    # Keep the system instruction, first user greeting if any, and last N turns
    # For agents, keeping the last 14 turns is usually more than enough context
    keep_turns = limit - 1
    system_messages = [m for m in messages if m.get("role") == "system"]
    chat_messages = [m for m in messages if m.get("role") != "system"]
    
    if len(chat_messages) > keep_turns:
        # Slice off old messages (ensure we start on a user message boundary)
        trimmed = chat_messages[-keep_turns:]
        if trimmed[0].get("role") == "assistant" and len(trimmed) > 1:
            trimmed = trimmed[1:]
        return system_messages + trimmed
        
    return messages
