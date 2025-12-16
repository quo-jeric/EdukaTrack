import jwt
import datetime
import os
from typing import Dict, Optional

SECRET_KEY = os.environ.get("SESSION_SECRET")
if not SECRET_KEY:
    raise RuntimeError("SESSION_SECRET environment variable must be set")

class AuthManager:
    def __init__(self):
        self.active_tokens = {}
        self.user_sessions = {}
        
    def create_token(self, username: str, role: str = "admin", expires_hours: int = 8) -> str:
        payload = {
            'username': username,
            'role': role,
            'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=expires_hours),
            'iat': datetime.datetime.now(datetime.timezone.utc)
        }
        
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
        if isinstance(token, bytes):
            token = token.decode('utf-8')
            
        self.active_tokens[token] = payload
        if username not in self.user_sessions:
            self.user_sessions[username] = []
        self.user_sessions[username].append(token)
        
        return token
    
    def verify_token(self, token: str, required_role: Optional[str] = None) -> Dict:
        if token not in self.active_tokens:
            raise ValueError("Token not found or expired")
        
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            
            if token not in self.active_tokens:
                raise ValueError("Token invalid")
            
            if required_role and payload.get('role') != required_role:
                raise ValueError(f"Required role: {required_role}, got: {payload.get('role')}")
            
            return payload
            
        except jwt.ExpiredSignatureError:
            if token in self.active_tokens:
                del self.active_tokens[token]
            raise ValueError("Token expired")
        except jwt.InvalidTokenError:
            raise ValueError("Invalid token")
    
    def logout(self, token: str) -> bool:
        if token in self.active_tokens:
            username = self.active_tokens[token].get('username')
            if username and username in self.user_sessions:
                self.user_sessions[username] = [t for t in self.user_sessions[username] if t != token]
            del self.active_tokens[token]
            return True
        return False
    
    def logout_all(self, username: str) -> bool:
        if username in self.user_sessions:
            for token in list(self.user_sessions[username]):
                if token in self.active_tokens:
                    del self.active_tokens[token]
            del self.user_sessions[username]
            return True
        return False
    
    def get_active_sessions(self) -> Dict:
        return {
            'total_tokens': len(self.active_tokens),
            'total_users': len(self.user_sessions),
            'users': list(self.user_sessions.keys())
        }
    
    def refresh_token(self, token: str) -> str:
        payload = self.verify_token(token)
        new_token = self.create_token(payload['username'], payload['role'])
        self.logout(token)
        return new_token

auth_manager = AuthManager()
