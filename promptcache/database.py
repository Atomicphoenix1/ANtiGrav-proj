import sqlite3
import os
import json
import time

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cachepilot.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp REAL NOT NULL,
            provider TEXT NOT NULL,
            model TEXT NOT NULL,
            endpoint TEXT NOT NULL,
            input_tokens INTEGER DEFAULT 0,
            cached_input_tokens INTEGER DEFAULT 0,
            output_tokens INTEGER DEFAULT 0,
            latency_ms INTEGER DEFAULT 0,
            cost_saved_usd REAL DEFAULT 0.0,
            cost_actual_usd REAL DEFAULT 0.0,
            status_code INTEGER DEFAULT 200,
            client_app TEXT DEFAULT 'Unknown',
            raw_request TEXT DEFAULT '',
            raw_response TEXT DEFAULT ''
        )
    """)
    # Add new columns if table exists without them (migration safety)
    for col in ["client_app", "raw_request", "raw_response"]:
        try:
            cursor.execute(f"ALTER TABLE requests ADD COLUMN {col} TEXT DEFAULT ''")
        except sqlite3.OperationalError:
            pass # Already exists
            
    conn.commit()
    conn.close()

def log_request(provider: str, model: str, endpoint: str, input_tokens: int, 
                cached_input_tokens: int, output_tokens: int, latency_ms: int, 
                status_code: int, client_app: str = "Unknown",
                raw_request: str = "", raw_response: str = ""):
    # Calculate costs (rough estimation based on standard prices as of mid-2026/late-2025)
    # Anthropic Claude 3.5 Sonnet: Write/Creation: $3/M, Read/Cache: $0.30/M, Standard Input: $3/M, Output: $15/M
    # OpenAI GPT-4o: Input: $2.50/M, Cached Input: $1.25/M, Output: $10/M
    
    cost_saved = 0.0
    cost_actual = 0.0
    
    prov_lower = provider.lower()
    model_lower = model.lower()
    
    if "claude-3-5" in model_lower or "claude-3.5" in model_lower:
        input_price = 3.0 / 1_000_000
        cache_read_price = 0.3 / 1_000_000
        output_price = 15.0 / 1_000_000
        non_cached = max(0, input_tokens - cached_input_tokens)
        cost_actual = (non_cached * input_price) + (cached_input_tokens * cache_read_price) + (output_tokens * output_price)
        cost_saved = (cached_input_tokens * (input_price - cache_read_price))
    elif "gpt-4o" in model_lower:
        input_price = 2.50 / 1_000_000
        cache_read_price = 1.25 / 1_000_000
        output_price = 10.0 / 1_000_000
        non_cached = max(0, input_tokens - cached_input_tokens)
        cost_actual = (non_cached * input_price) + (cached_input_tokens * cache_read_price) + (output_tokens * output_price)
        cost_saved = (cached_input_tokens * (input_price - cache_read_price))
    else:
        input_price = 2.0 / 1_000_000
        cache_read_price = 0.5 / 1_000_000
        output_price = 8.0 / 1_000_000
        non_cached = max(0, input_tokens - cached_input_tokens)
        cost_actual = (non_cached * input_price) + (cached_input_tokens * cache_read_price) + (output_tokens * output_price)
        cost_saved = (cached_input_tokens * (input_price - cache_read_price))
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO requests (
            timestamp, provider, model, endpoint, input_tokens, 
            cached_input_tokens, output_tokens, latency_ms, 
            cost_saved_usd, cost_actual_usd, status_code, client_app,
            raw_request, raw_response
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        time.time(), provider, model, endpoint, input_tokens,
        cached_input_tokens, output_tokens, latency_ms,
        cost_saved, cost_actual, status_code, client_app,
        raw_request, raw_response
    ))
    conn.commit()
    conn.close()
    return cost_saved

def get_stats():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Aggregated metrics
    cursor.execute("""
        SELECT 
            COUNT(*) as total_requests,
            SUM(input_tokens) as total_input_tokens,
            SUM(cached_input_tokens) as total_cached_tokens,
            SUM(output_tokens) as total_output_tokens,
            SUM(cost_saved_usd) as total_saved_usd,
            SUM(cost_actual_usd) as total_actual_usd,
            AVG(latency_ms) as avg_latency_ms
        FROM requests
    """)
    row = cursor.fetchone()
    
    stats = {
        "total_requests": row["total_requests"] or 0,
        "total_input_tokens": row["total_input_tokens"] or 0,
        "total_cached_tokens": row["total_cached_tokens"] or 0,
        "total_output_tokens": row["total_output_tokens"] or 0,
        "total_saved_usd": round(row["total_saved_usd"] or 0.0, 4),
        "total_actual_usd": round(row["total_actual_usd"] or 0.0, 4),
        "avg_latency_ms": round(row["avg_latency_ms"] or 0.0, 1)
    }
    
    # Client App breakdown
    cursor.execute("""
        SELECT client_app, COUNT(*) as count, SUM(cost_saved_usd) as saved
        FROM requests
        GROUP BY client_app
    """)
    client_rows = cursor.fetchall()
    stats["clients"] = [{"name": r["client_app"], "count": r["count"], "saved": round(r["saved"] or 0.0, 4)} for r in client_rows]
    
    # Daily cache efficiency & cost savings
    cursor.execute("""
        SELECT 
            strftime('%Y-%m-%d', datetime(timestamp, 'unixepoch')) as day,
            SUM(input_tokens) as input,
            SUM(cached_input_tokens) as cached,
            SUM(cost_saved_usd) as saved
        FROM requests
        GROUP BY day
        ORDER BY day DESC
        LIMIT 7
    """)
    daily_rows = cursor.fetchall()
    daily_stats = []
    for r in daily_rows:
        daily_stats.append({
            "day": r["day"],
            "input": r["input"] or 0,
            "cached": r["cached"] or 0,
            "saved": round(r["saved"] or 0.0, 4)
        })
    stats["daily"] = daily_stats[::-1] # chronological order
    
    conn.close()
    return stats

def get_recent_requests(limit=20):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM requests 
        ORDER BY timestamp DESC 
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    
    result = []
    for r in rows:
        result.append({
            "id": r["id"],
            "timestamp": r["timestamp"],
            "provider": r["provider"],
            "model": r["model"],
            "endpoint": r["endpoint"],
            "input_tokens": r["input_tokens"],
            "cached_input_tokens": r["cached_input_tokens"],
            "output_tokens": r["output_tokens"],
            "latency_ms": r["latency_ms"],
            "cost_saved_usd": round(r["cost_saved_usd"], 4),
            "cost_actual_usd": round(r["cost_actual_usd"], 4),
            "status_code": r["status_code"],
            "client_app": r["client_app"],
            "raw_request": r["raw_request"] or "",
            "raw_response": r["raw_response"] or ""
        })
    return result


# Initialize on import
init_db()
