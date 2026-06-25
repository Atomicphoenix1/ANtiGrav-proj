import unittest
import sys
import os

# Ensure local imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from optimizer import optimize_anthropic_payload
import database

class TestCachePilot(unittest.TestCase):
    def test_anthropic_system_string_optimization(self):
        """Test that system prompt is wrapped in a block format and cache_control is injected."""
        payload = {
            "model": "claude-3-5-sonnet-20241022",
            "system": "You are a helpful coding assistant.",
            "messages": [
                {"role": "user", "content": "Hello!"}
            ]
        }
        optimized = optimize_anthropic_payload(payload)
        
        # Verify system prompt has been modified
        self.assertIsInstance(optimized["system"], list)
        self.assertEqual(len(optimized["system"]), 1)
        self.assertEqual(optimized["system"][0]["text"], "You are a helpful coding assistant.")
        self.assertEqual(optimized["system"][0]["cache_control"], {"type": "ephemeral"})

    def test_anthropic_multiple_breakpoints(self):
        """Test that breakpoints are set for tools and history when there are multiple messages."""
        payload = {
            "model": "claude-3-5-sonnet-20241022",
            "system": "System instructions...",
            "tools": [
                {
                    "name": "get_weather",
                    "description": "Get current weather details",
                    "input_schema": {"type": "object", "properties": {}}
                }
            ],
            "messages": [
                {"role": "user", "content": "First message"},
                {"role": "assistant", "content": "First response"},
                {"role": "user", "content": "Second message"},
                {"role": "assistant", "content": "Second response"},
                {"role": "user", "content": "Third message"}
            ]
        }
        
        optimized = optimize_anthropic_payload(payload)
        
        # 1. System prompt cached
        self.assertEqual(optimized["system"][0]["cache_control"], {"type": "ephemeral"})
        
        # 2. Tools cached
        self.assertEqual(optimized["tools"][-1]["cache_control"], {"type": "ephemeral"})
        
        # 3. Message history checkpoint cached (second to last user turn)
        # In this list: user indices are 0 (First message), 2 (Second message), 4 (Third message)
        # Should set caching checkpoint at user index 2 (Second message)
        second_user_msg = optimized["messages"][2]
        self.assertIsInstance(second_user_msg["content"], list)
        self.assertEqual(second_user_msg["content"][0]["cache_control"], {"type": "ephemeral"})

    def test_database_logging(self):
        """Verify request logging and database stats function correctly."""
        # Initial stats
        initial_stats = database.get_stats()
        initial_reqs = initial_stats["total_requests"]
        
        # Log a dummy request
        saved = database.log_request(
            provider="Anthropic",
            model="claude-3-5-sonnet-20241022",
            endpoint="/v1/messages",
            input_tokens=10000,
            cached_input_tokens=8000,
            output_tokens=500,
            latency_ms=2500,
            status_code=200
        )
        
        # Expecting cost savings to be logged
        self.assertGreater(saved, 0.0)
        
        # Verify stats updated
        new_stats = database.get_stats()
        self.assertEqual(new_stats["total_requests"], initial_reqs + 1)
        self.assertEqual(new_stats["total_cached_tokens"], initial_stats["total_cached_tokens"] + 8000)

if __name__ == "__main__":
    unittest.main()
