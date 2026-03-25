#!/usr/bin/env python3
"""
auth.py - User Authentication Module
Provides login and registration endpoints for the agent system.

Features:
- User registration with password hashing
- User login with JWT token generation
- Password validation and security
- Token-based authentication
"""

import hashlib
import hmac
import json
import os
import secrets
import time
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict
from pathlib import Path


# Constants
USERS_DB_FILE = Path(".data/users.json")
JWT_SECRET = os.environ.get("JWT_SECRET", secrets.token_hex(32))
TOKEN_EXPIRY_HOURS = 24


@dataclass
class User:
    """Represents a user in the system."""
    username: str
    password_hash: str
    salt: str
    created_at: float
    last_login: Optional[float] = None
    is_active: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        return cls(**data)


class AuthError(Exception):
    """Base exception for authentication errors."""
    pass


class UserExistsError(AuthError):
    """Raised when trying to register an existing user."""
    pass


class InvalidCredentialsError(AuthError):
    """Raised when login credentials are invalid."""
    pass


class TokenError(AuthError):
    """Raised when token is invalid or expired."""
    pass


class UserRepository:
    """Manages user data persistence."""
    
    def __init__(self, db_file: Path = USERS_DB_FILE):
        self.db_file = db_file
        self._ensure_db_exists()
    
    def _ensure_db_exists(self):
        """Create database directory and file if they don't exist."""
        self.db_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.db_file.exists():
            self._save_users({})
    
    def _load_users(self) -> Dict[str, Dict]:
        """Load all users from database."""
        try:
            with open(self.db_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    
    def _save_users(self, users: Dict[str, Dict]):
        """Save all users to database."""
        with open(self.db_file, 'w') as f:
            json.dump(users, f, indent=2)
    
    def get_user(self, username: str) -> Optional[User]:
        """Get a user by username."""
        users = self._load_users()
        user_data = users.get(username)
        if user_data:
            return User.from_dict(user_data)
        return None
    
    def save_user(self, user: User):
        """Save a user to database."""
        users = self._load_users()
        users[user.username] = user.to_dict()
        self._save_users(users)
    
    def user_exists(self, username: str) -> bool:
        """Check if a user exists."""
        return self.get_user(username) is not None
    
    def list_users(self) -> list:
        """List all registered usernames."""
        users = self._load_users()
        return list(users.keys())


class AuthService:
    """Core authentication service providing registration and login."""
    
    def __init__(self, user_repo: Optional[UserRepository] = None):
        self.user_repo = user_repo or UserRepository()
    
    def _hash_password(self, password: str, salt: Optional[str] = None) -> tuple:
        """
        Hash a password using PBKDF2 with SHA256.
        Returns (hash, salt) tuple.
        """
        if salt is None:
            salt = secrets.token_hex(16)
        
        # Use PBKDF2 for secure password hashing
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            iterations=100000
        ).hex()
        
        return password_hash, salt
    
    def _verify_password(self, password: str, password_hash: str, salt: str) -> bool:
        """Verify a password against its hash."""
        computed_hash, _ = self._hash_password(password, salt)
        return hmac.compare_digest(computed_hash, password_hash)
    
    def _generate_token(self, username: str) -> str:
        """Generate a JWT-like token for authentication."""
        header = json.dumps({"alg": "HS256", "typ": "JWT"})
        
        now = time.time()
        payload = json.dumps({
            "sub": username,
            "iat": now,
            "exp": now + (TOKEN_EXPIRY_HOURS * 3600)
        })
        
        # Base64URL encode header and payload
        import base64
        header_b64 = base64.urlsafe_b64encode(header.encode()).rstrip(b'=').decode()
        payload_b64 = base64.urlsafe_b64encode(payload.encode()).rstrip(b'=').decode()
        
        # Create signature
        message = f"{header_b64}.{payload_b64}"
        signature = hmac.new(
            JWT_SECRET.encode(),
            message.encode(),
            hashlib.sha256
        ).digest()
        signature_b64 = base64.urlsafe_b64encode(signature).rstrip(b'=').decode()
        
        return f"{message}.{signature_b64}"
    
    def _verify_token(self, token: str) -> str:
        """Verify a token and return the username."""
        try:
            parts = token.split('.')
            if len(parts) != 3:
                raise TokenError("Invalid token format")
            
            header_b64, payload_b64, signature_b64 = parts
            
            # Verify signature
            import base64
            message = f"{header_b64}.{payload_b64}"
            expected_sig = hmac.new(
                JWT_SECRET.encode(),
                message.encode(),
                hashlib.sha256
            ).digest()
            expected_sig_b64 = base64.urlsafe_b64encode(expected_sig).rstrip(b'=').decode()
            
            if not hmac.compare_digest(signature_b64, expected_sig_b64):
                raise TokenError("Invalid token signature")
            
            # Decode payload
            # Add padding back for base64 decoding
            padding = 4 - len(payload_b64) % 4
            if padding != 4:
                payload_b64 += '=' * padding
            payload = json.loads(base64.urlsafe_b64decode(payload_b64))
            
            # Check expiration
            if payload.get("exp", 0) < time.time():
                raise TokenError("Token expired")
            
            return payload["sub"]
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            raise TokenError(f"Token validation failed: {e}")
    
    def validate_password(self, password: str) -> tuple[bool, str]:
        """
        Validate password strength.
        Returns (is_valid, message).
        """
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        if not any(c.isupper() for c in password):
            return False, "Password must contain at least one uppercase letter"
        if not any(c.islower() for c in password):
            return False, "Password must contain at least one lowercase letter"
        if not any(c.isdigit() for c in password):
            return False, "Password must contain at least one digit"
        return True, "Password is valid"
    
    def register(self, username: str, password: str) -> Dict[str, Any]:
        """
        Register a new user.
        
        Args:
            username: The desired username
            password: The user's password
            
        Returns:
            Dict with user info and success status
            
        Raises:
            UserExistsError: If username already exists
        """
        # Validate username
        if not username or len(username) < 3:
            raise ValueError("Username must be at least 3 characters long")
        if not username.isalnum():
            raise ValueError("Username must contain only alphanumeric characters")
        
        # Check if user exists
        if self.user_repo.user_exists(username):
            raise UserExistsError(f"User '{username}' already exists")
        
        # Validate password
        is_valid, message = self.validate_password(password)
        if not is_valid:
            raise ValueError(message)
        
        # Hash password and create user
        password_hash, salt = self._hash_password(password)
        user = User(
            username=username,
            password_hash=password_hash,
            salt=salt,
            created_at=time.time()
        )
        
        self.user_repo.save_user(user)
        
        return {
            "success": True,
            "username": username,
            "message": "User registered successfully"
        }
    
    def login(self, username: str, password: str) -> Dict[str, Any]:
        """
        Authenticate a user and generate an access token.
        
        Args:
            username: The username
            password: The user's password
            
        Returns:
            Dict with token and user info
            
        Raises:
            InvalidCredentialsError: If credentials are invalid
        """
        # Get user
        user = self.user_repo.get_user(username)
        if not user:
            raise InvalidCredentialsError("Invalid username or password")
        
        # Verify password
        if not self._verify_password(password, user.password_hash, user.salt):
            raise InvalidCredentialsError("Invalid username or password")
        
        # Update last login
        user.last_login = time.time()
        self.user_repo.save_user(user)
        
        # Generate token
        token = self._generate_token(username)
        
        return {
            "success": True,
            "username": username,
            "token": token,
            "token_type": "Bearer",
            "expires_in": TOKEN_EXPIRY_HOURS * 3600,
            "message": "Login successful"
        }
    
    def logout(self, token: str) -> Dict[str, Any]:
        """
        Logout a user (invalidate token).
        Note: In a production system, this would add the token to a blacklist.
        
        Args:
            token: The user's access token
            
        Returns:
            Dict with logout status
        """
        try:
            username = self._verify_token(token)
            return {
                "success": True,
                "username": username,
                "message": "Logout successful"
            }
        except TokenError:
            return {
                "success": False,
                "message": "Invalid token"
            }
    
    def get_current_user(self, token: str) -> Optional[User]:
        """Get the current user from a token."""
        try:
            username = self._verify_token(token)
            return self.user_repo.get_user(username)
        except TokenError:
            return None
    
    def change_password(self, username: str, old_password: str, new_password: str) -> Dict[str, Any]:
        """
        Change a user's password.
        
        Args:
            username: The username
            old_password: The current password
            new_password: The new password
            
        Returns:
            Dict with status and message
        """
        user = self.user_repo.get_user(username)
        if not user:
            raise InvalidCredentialsError("User not found")
        
        # Verify old password
        if not self._verify_password(old_password, user.password_hash, user.salt):
            raise InvalidCredentialsError("Current password is incorrect")
        
        # Validate new password
        is_valid, message = self.validate_password(new_password)
        if not is_valid:
            raise ValueError(message)
        
        # Hash and save new password
        password_hash, salt = self._hash_password(new_password)
        user.password_hash = password_hash
        user.salt = salt
        self.user_repo.save_user(user)
        
        return {
            "success": True,
            "message": "Password changed successfully"
        }


class AuthEndpoints:
    """
    REST API endpoints for authentication.
    Provides a simple interface for integration with the agent system.
    """
    
    def __init__(self, auth_service: Optional[AuthService] = None):
        self.auth_service = auth_service or AuthService()
    
    def register(self, username: str, password: str) -> Dict[str, Any]:
        """Registration endpoint."""
        try:
            return self.auth_service.register(username, password)
        except (UserExistsError, ValueError) as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def login(self, username: str, password: str) -> Dict[str, Any]:
        """Login endpoint."""
        try:
            return self.auth_service.login(username, password)
        except InvalidCredentialsError as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def logout(self, token: str) -> Dict[str, Any]:
        """Logout endpoint."""
        return self.auth_service.logout(token)
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Token verification endpoint."""
        user = self.auth_service.get_current_user(token)
        if user:
            return {
                "success": True,
                "username": user.username,
                "is_active": user.is_active
            }
        return {
            "success": False,
            "error": "Invalid or expired token"
        }
    
    def change_password(self, token: str, old_password: str, new_password: str) -> Dict[str, Any]:
        """Change password endpoint."""
        user = self.auth_service.get_current_user(token)
        if not user:
            return {
                "success": False,
                "error": "Invalid or expired token"
            }
        try:
            return self.auth_service.change_password(user.username, old_password, new_password)
        except (InvalidCredentialsError, ValueError) as e:
            return {
                "success": False,
                "error": str(e)
            }


# Singleton instance for easy import
auth_endpoints = AuthEndpoints()


# Convenience functions
def register(username: str, password: str) -> Dict[str, Any]:
    """Register a new user."""
    return auth_endpoints.register(username, password)


def login(username: str, password: str) -> Dict[str, Any]:
    """Login a user."""
    return auth_endpoints.login(username, password)


def logout(token: str) -> Dict[str, Any]:
    """Logout a user."""
    return auth_endpoints.logout(token)


def verify_token(token: str) -> Dict[str, Any]:
    """Verify an access token."""
    return auth_endpoints.verify_token(token)


def change_password(token: str, old_password: str, new_password: str) -> Dict[str, Any]:
    """Change user password."""
    return auth_endpoints.change_password(token, old_password, new_password)


if __name__ == "__main__":
    # Simple CLI demo
    print("=== Authentication Module Demo ===\n")
    
    # Test registration
    print("1. Registering user 'alice'...")
    result = register("alice", "SecurePass123")
    print(f"   Result: {result}")
    
    # Test duplicate registration
    print("\n2. Trying to register 'alice' again...")
    result = register("alice", "AnotherPass123")
    print(f"   Result: {result}")
    
    # Test login
    print("\n3. Logging in as 'alice'...")
    result = login("alice", "SecurePass123")
    print(f"   Result: {result}")
    token = result.get("token")
    
    # Test invalid login
    print("\n4. Trying invalid password...")
    result = login("alice", "WrongPassword")
    print(f"   Result: {result}")
    
    # Test token verification
    if token:
        print("\n5. Verifying token...")
        result = verify_token(token)
        print(f"   Result: {result}")
        
        print("\n6. Changing password...")
        result = change_password(token, "SecurePass123", "NewSecurePass456")
        print(f"   Result: {result}")
        
        print("\n7. Logging out...")
        result = logout(token)
        print(f"   Result: {result}")
    
    print("\n=== Demo Complete ===")
