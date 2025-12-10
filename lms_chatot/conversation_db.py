from typing import List, Dict, Optional
import json
import os
from datetime import datetime

class ConversationDB:
    """Simple file-based conversation storage"""
    
    def __init__(self, db_path: str = "conversations.json"):
        self.db_path = db_path
        self.conversations = self._load()
    
    def _load(self) -> Dict:
        if os.path.exists(self.db_path):
            with open(self.db_path, 'r') as f:
                return json.load(f)
        return {}
    
    def _save(self):
        with open(self.db_path, 'w') as f:
            json.dump(self.conversations, f, indent=2)
    
    def add_message(self, session_id: str, role: str, content: str, metadata: Dict = None):
        if session_id not in self.conversations:
            self.conversations[session_id] = {
                "created_at": datetime.now().isoformat(),
                "messages": [],
                "context": {}
            }
        
        self.conversations[session_id]["messages"].append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        })
        self._save()
    
    def get_messages(self, session_id: str) -> List[Dict]:
        return self.conversations.get(session_id, {}).get("messages", [])
    
    def update_context(self, session_id: str, context: Dict):
        if session_id not in self.conversations:
            self.conversations[session_id] = {"created_at": datetime.now().isoformat(), "messages": [], "context": {}}
        self.conversations[session_id]["context"].update(context)
        self._save()
    
    def get_context(self, session_id: str) -> Dict:
        return self.conversations.get(session_id, {}).get("context", {})

conversation_db = ConversationDB()
