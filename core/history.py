# core/history.py
import json
import os
from datetime import datetime

HISTORY_FILE = "history.json"

class HistoryManager:
    def __init__(self):
        self.history = self._load_history()

    def _load_history(self):
        if not os.path.exists(HISTORY_FILE):
            return {}
        try:
            with open(HISTORY_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}

    def save_history(self):
        with open(HISTORY_FILE, 'w') as f:
            json.dump(self.history, f, indent=4)

    def add_entry(self, item_data):
        """
        item_data: {
            'imdb_id': str,
            'title': str,
            'year': str,
            'type': str,
            'season': int,  # Optional
            'episode': int, # Optional
            'stream_link': str # Optional (The torrent link)
        }
        """
        imdb_id = item_data.get('imdb_id')
        if not imdb_id: return

        # Add Timestamp of "When you clicked play"
        item_data['last_watched'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Save (Overwrites previous entry for this Show ID)
        self.history[imdb_id] = item_data
        self.save_history()

    def get_sorted_history(self):
        """Returns list of items sorted by most recently watched."""
        items = list(self.history.values())
        # Sort by date string (Descending)
        items.sort(key=lambda x: x.get('last_watched', ''), reverse=True)
        return items
