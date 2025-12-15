import sqlite3
import json
from datetime import datetime
from typing import Dict, Any, Optional

class UsageTracker:
    """Track AI model usage, tokens, and costs"""
    
    def __init__(self, db_path: str = "usage_tracker.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usage_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_id INTEGER,
                user_role TEXT,
                inference_system TEXT,
                model_name TEXT,
                input_tokens INTEGER DEFAULT 0,
                output_tokens INTEGER DEFAULT 0,
                total_tokens INTEGER DEFAULT 0,
                tool_used BOOLEAN DEFAULT FALSE,
                tool_name TEXT,
                session_id TEXT,
                request_type TEXT DEFAULT 'chat'
            )
        """)
        conn.commit()
        conn.close()
    
    def log_usage(self, user_id: int, user_role: str, inference_system: str, 
                  model_name: str, input_tokens: int = 0, output_tokens: int = 0,
                  tool_used: bool = False, tool_name: str = None, 
                  session_id: str = None, request_type: str = 'chat'):
        """Log AI model usage"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        total_tokens = input_tokens + output_tokens
        
        cursor.execute("""
            INSERT INTO usage_logs 
            (user_id, user_role, inference_system, model_name, input_tokens, 
             output_tokens, total_tokens, tool_used, tool_name, session_id, request_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, user_role, inference_system, model_name, input_tokens,
              output_tokens, total_tokens, tool_used, tool_name, session_id, request_type))
        
        conn.commit()
        conn.close()
    
    def get_usage_stats(self, user_id: int = None, days: int = 30) -> Dict[str, Any]:
        """Get usage statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        where_clause = "WHERE timestamp >= datetime('now', '-{} days')".format(days)
        if user_id:
            where_clause += f" AND user_id = {user_id}"
        
        # Total usage
        cursor.execute(f"""
            SELECT 
                COUNT(*) as total_requests,
                SUM(input_tokens) as total_input_tokens,
                SUM(output_tokens) as total_output_tokens,
                SUM(total_tokens) as total_tokens,
                COUNT(CASE WHEN tool_used = 1 THEN 1 END) as tool_requests
            FROM usage_logs {where_clause}
        """)
        
        total_stats = cursor.fetchone()
        
        # By model
        cursor.execute(f"""
            SELECT 
                inference_system,
                model_name,
                COUNT(*) as requests,
                SUM(total_tokens) as tokens
            FROM usage_logs {where_clause}
            GROUP BY inference_system, model_name
            ORDER BY requests DESC
        """)
        
        model_stats = cursor.fetchall()
        
        conn.close()
        
        return {
            "total_requests": total_stats[0] or 0,
            "total_input_tokens": total_stats[1] or 0,
            "total_output_tokens": total_stats[2] or 0,
            "total_tokens": total_stats[3] or 0,
            "tool_requests": total_stats[4] or 0,
            "models": [
                {
                    "system": row[0],
                    "model": row[1],
                    "requests": row[2],
                    "tokens": row[3]
                }
                for row in model_stats
            ]
        }

# Global usage tracker instance
usage_tracker = UsageTracker()