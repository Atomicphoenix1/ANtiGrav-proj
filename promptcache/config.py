import os

# Load API keys from env
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyDWw-nuW8sOAPldx5j6lh6qoyUM1GagNA0")

# Proxy configuration
PORT = int(os.environ.get("PORT", "8000"))
HOST = os.environ.get("HOST", "127.0.0.1")

# Default caching configs
MIN_TOKEN_LIMIT_FOR_CACHE = 1024 # Only cache if prompt total size is above 1024 tokens to save cache space/overhead
MAX_EPHEMERAL_BREAKPOINTS = 4   # Anthropic limit
HISTORY_COMPRESSION_THRESHOLD = 20 # Number of history turns before potential summary/compression
