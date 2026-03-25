#!/usr/bin/env python3
"""
test_auth.py - Unit tests for the authentication module
"""

import unittest
import json
import os
import tempfile
import shutil
from pathlib import Path
from auth import (
    AuthService, UserRepository, AuthEndpoints,
    User, AuthError, UserExistsError, InvalidCredentialsError,
    TokenError, register, login, logout, verify_token
)


class TestAuthService(unittest.TestCase):
    """Test cases for the AuthService class."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_file = Path(self.temp_dir) / "test_users.json"
        self.user_repo = UserRepository(self.db_file)
        self.auth_service = AuthService(self.user_repo)
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_register_success(self):
        """Test successful user registration."""
        result = self.auth_service.register("testuser", "SecurePass123")
        self.assertTrue(result["success"])
        self.assertEqual(result["username"], "testuser")
        self.assertTrue(self.user_repo.user_exists("testuser"))
    
    def test_register_duplicate_user(self):
        """Test registration with duplicate username."""
        self.auth_service.register("testuser", "SecurePass123")
        with self.assertRaises(UserExistsError):
            self.auth_service.register("testuser", "AnotherPass123")
    
    def test_register_weak_password(self):
        """Test registration with weak password."""
        # Too short
        with self.assertRaises(ValueError):
            self.auth_service.register("testuser", "short")
        
        # No uppercase
        with self.assertRaises(ValueError):
            self.auth_service.register("testuser", "lowercase1")
        
        # No lowercase
        with self.assertRaises(ValueError):
            self.auth_service.register("testuser", "UPPERCASE1")
        
        # No digit
        with self.assertRaises(ValueError):
            self.auth_service.register("testuser", "NoDigitsHere")
    
    def test_register_invalid_username(self):
        """Test registration with invalid username."""
        # Too short
        with self.assertRaises(ValueError):
            self.auth_service.register("ab", "SecurePass123")
        
        # Non-alphanumeric
        with self.assertRaises(ValueError):
            self.auth_service.register("user@name", "SecurePass123")
    
    def test_login_success(self):
        """Test successful login."""
        self.auth_service.register("testuser", "SecurePass123")
        result = self.auth_service.login("testuser", "SecurePass123")
        self.assertTrue(result["success"])
        self.assertEqual(result["username"], "testuser")
        self.assertIn("token", result)
        self.assertEqual(result["token_type"], "Bearer")
    
    def test_login_wrong_password(self):
        """Test login with wrong password."""
        self.auth_service.register("testuser", "SecurePass123")
        with self.assertRaises(InvalidCredentialsError):
            self.auth_service.login("testuser", "WrongPassword123")
    
    def test_login_nonexistent_user(self):
        """Test login with non-existent user."""
        with self.assertRaises(InvalidCredentialsError):
            self.auth_service.login("nonexistent", "SecurePass123")
    
    def test_token_verification(self):
        """Test token generation and verification."""
        self.auth_service.register("testuser", "SecurePass123")
        result = self.auth_service.login("testuser", "SecurePass123")
        token = result["token"]
        
        # Verify valid token
        username = self.auth_service._verify_token(token)
        self.assertEqual(username, "testuser")
    
    def test_token_invalid(self):
        """Test verification of invalid token."""
        with self.assertRaises(TokenError):
            self.auth_service._verify_token("invalid.token.here")
    
    def test_logout(self):
        """Test logout functionality."""
        self.auth_service.register("testuser", "SecurePass123")
        result = self.auth_service.login("testuser", "SecurePass123")
        token = result["token"]
        
        result = self.auth_service.logout(token)
        self.assertTrue(result["success"])
    
    def test_change_password_success(self):
        """Test successful password change."""
        self.auth_service.register("testuser", "SecurePass123")
        result = self.auth_service.change_password("testuser", "SecurePass123", "NewPass123!")
        self.assertTrue(result["success"])
        
        # Verify old password doesn't work
        with self.assertRaises(InvalidCredentialsError):
            self.auth_service.login("testuser", "SecurePass123")
        
        # Verify new password works
        result = self.auth_service.login("testuser", "NewPass123!")
        self.assertTrue(result["success"])
    
    def test_change_password_wrong_old(self):
        """Test password change with wrong old password."""
        self.auth_service.register("testuser", "SecurePass123")
        with self.assertRaises(InvalidCredentialsError):
            self.auth_service.change_password("testuser", "WrongOldPass", "NewPass123!")
    
    def test_get_current_user(self):
        """Test getting current user from token."""
        self.auth_service.register("testuser", "SecurePass123")
        result = self.auth_service.login("testuser", "SecurePass123")
        token = result["token"]
        
        user = self.auth_service.get_current_user(token)
        self.assertIsNotNone(user)
        self.assertEqual(user.username, "testuser")
    
    def test_get_current_user_invalid_token(self):
        """Test getting current user with invalid token."""
        user = self.auth_service.get_current_user("invalid.token.here")
        self.assertIsNone(user)
    
    def test_password_validation(self):
        """Test password validation rules."""
        # Valid passwords
        valid, msg = self.auth_service.validate_password("SecurePass123")
        self.assertTrue(valid)
        
        # Invalid passwords
        cases = [
            ("short", "at least 8 characters"),
            ("lowercase1", "at least one uppercase"),
            ("UPPERCASE1", "at least one lowercase"),
            ("NoDigitsHere", "at least one digit"),
        ]
        
        for password, expected_msg in cases:
            valid, msg = self.auth_service.validate_password(password)
            self.assertFalse(valid)
            self.assertIn(expected_msg.lower(), msg.lower())


class TestUserRepository(unittest.TestCase):
    """Test cases for the UserRepository class."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_file = Path(self.temp_dir) / "test_users.json"
        self.repo = UserRepository(self.db_file)
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_save_and_get_user(self):
        """Test saving and retrieving a user."""
        user = User(
            username="testuser",
            password_hash="hash123",
            salt="salt123",
            created_at=1234567890.0
        )
        self.repo.save_user(user)
        
        retrieved = self.repo.get_user("testuser")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.username, "testuser")
        self.assertEqual(retrieved.password_hash, "hash123")
    
    def test_get_nonexistent_user(self):
        """Test retrieving a non-existent user."""
        user = self.repo.get_user("nonexistent")
        self.assertIsNone(user)
    
    def test_user_exists(self):
        """Test user existence check."""
        user = User(
            username="testuser",
            password_hash="hash123",
            salt="salt123",
            created_at=1234567890.0
        )
        self.repo.save_user(user)
        
        self.assertTrue(self.repo.user_exists("testuser"))
        self.assertFalse(self.repo.user_exists("nonexistent"))
    
    def test_list_users(self):
        """Test listing all users."""
        for i in range(3):
            user = User(
                username=f"user{i}",
                password_hash=f"hash{i}",
                salt=f"salt{i}",
                created_at=1234567890.0
            )
            self.repo.save_user(user)
        
        users = self.repo.list_users()
        self.assertEqual(len(users), 3)
        self.assertIn("user0", users)
        self.assertIn("user1", users)
        self.assertIn("user2", users)


class TestAuthEndpoints(unittest.TestCase):
    """Test cases for the AuthEndpoints class."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_file = Path(self.temp_dir) / "test_users.json"
        self.user_repo = UserRepository(self.db_file)
        self.auth_service = AuthService(self.user_repo)
        self.endpoints = AuthEndpoints(self.auth_service)
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_register_endpoint_success(self):
        """Test successful registration via endpoint."""
        result = self.endpoints.register("testuser", "SecurePass123")
        self.assertTrue(result["success"])
        self.assertEqual(result["username"], "testuser")
    
    def test_register_endpoint_failure(self):
        """Test failed registration via endpoint."""
        self.endpoints.register("testuser", "SecurePass123")
        result = self.endpoints.register("testuser", "AnotherPass123")
        self.assertFalse(result["success"])
        self.assertIn("error", result)
    
    def test_login_endpoint_success(self):
        """Test successful login via endpoint."""
        self.endpoints.register("testuser", "SecurePass123")
        result = self.endpoints.login("testuser", "SecurePass123")
        self.assertTrue(result["success"])
        self.assertIn("token", result)
    
    def test_login_endpoint_failure(self):
        """Test failed login via endpoint."""
        result = self.endpoints.login("nonexistent", "SecurePass123")
        self.assertFalse(result["success"])
        self.assertIn("error", result)
    
    def test_verify_token_endpoint(self):
        """Test token verification via endpoint."""
        self.endpoints.register("testuser", "SecurePass123")
        login_result = self.endpoints.login("testuser", "SecurePass123")
        token = login_result["token"]
        
        result = self.endpoints.verify_token(token)
        self.assertTrue(result["success"])
        self.assertEqual(result["username"], "testuser")
    
    def test_verify_token_endpoint_invalid(self):
        """Test invalid token verification via endpoint."""
        result = self.endpoints.verify_token("invalid.token")
        self.assertFalse(result["success"])
        self.assertIn("error", result)
    
    def test_change_password_endpoint(self):
        """Test password change via endpoint."""
        self.endpoints.register("testuser", "SecurePass123")
        login_result = self.endpoints.login("testuser", "SecurePass123")
        token = login_result["token"]
        
        result = self.endpoints.change_password(token, "SecurePass123", "NewPass123!")
        self.assertTrue(result["success"])
    
    def test_change_password_endpoint_invalid_token(self):
        """Test password change with invalid token via endpoint."""
        result = self.endpoints.change_password("invalid.token", "old", "new")
        self.assertFalse(result["success"])


class TestIntegration(unittest.TestCase):
    """Integration tests for the full authentication flow."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_file = Path(self.temp_dir) / "test_users.json"
        os.environ["USERS_DB_FILE"] = str(self.db_file)
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        if "USERS_DB_FILE" in os.environ:
            del os.environ["USERS_DB_FILE"]
    
    def test_full_authentication_flow(self):
        """Test complete authentication flow using convenience functions."""
        # Note: We need to use fresh instances since the module-level singleton
        # uses a different db file
        user_repo = UserRepository(self.db_file)
        auth_service = AuthService(user_repo)
        endpoints = AuthEndpoints(auth_service)
        
        # 1. Register
        result = endpoints.register("alice", "SecurePass123")
        self.assertTrue(result["success"])
        
        # 2. Login
        result = endpoints.login("alice", "SecurePass123")
        self.assertTrue(result["success"])
        token = result["token"]
        
        # 3. Verify token
        result = endpoints.verify_token(token)
        self.assertTrue(result["success"])
        
        # 4. Change password
        result = endpoints.change_password(token, "SecurePass123", "NewSecure456")
        self.assertTrue(result["success"])
        
        # 5. Login with new password
        result = endpoints.login("alice", "NewSecure456")
        self.assertTrue(result["success"])
        
        # 6. Logout
        result = endpoints.logout(token)
        self.assertTrue(result["success"])


if __name__ == "__main__":
    # Run tests with verbose output
    unittest.main(verbosity=2)
