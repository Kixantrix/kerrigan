"""
Authentication module for Task Tracker.

Simple token-based authentication with user registration.
Demonstrates security considerations in agent-built code.
"""

import hashlib
import json
import os
from pathlib import Path


class AuthManager:
    """Manages user authentication and sessions."""
    
    def __init__(self):
        self.data_dir = Path.home() / ".task-tracker"
        self.data_dir.mkdir(exist_ok=True)
        self.users_file = self.data_dir / "users.json"
        self.session_file = self.data_dir / "session.json"
        self._load_users()
    
    def _load_users(self):
        """Load users from storage."""
        if self.users_file.exists():
            with open(self.users_file, "r") as f:
                self.users = json.load(f)
        else:
            self.users = {}
    
    def _save_users(self):
        """Save users to storage."""
        with open(self.users_file, "w") as f:
            json.dump(self.users, f, indent=2)
    
    def _hash_password(self, password):
        """Hash password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def register_user(self, username, password):
        """Register a new user."""
        if username in self.users:
            return False
        
        self.users[username] = {
            "password_hash": self._hash_password(password)
        }
        self._save_users()
        return True
    
    def login(self, username, password):
        """Authenticate user and create session."""
        if username not in self.users:
            return False
        
        password_hash = self._hash_password(password)
        if self.users[username]["password_hash"] != password_hash:
            return False
        
        # Create session
        session = {"username": username}
        with open(self.session_file, "w") as f:
            json.dump(session, f, indent=2)
        
        return True
    
    def logout(self):
        """Remove current session."""
        if self.session_file.exists():
            os.remove(self.session_file)
    
    def is_logged_in(self):
        """Check if user is logged in."""
        return self.session_file.exists()
    
    def get_current_user(self):
        """Get current logged-in username."""
        if not self.is_logged_in():
            return None
        
        with open(self.session_file, "r") as f:
            session = json.load(f)
        
        return session.get("username")
