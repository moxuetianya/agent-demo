# Authentication Module

A secure user authentication system for the agent demo application.

## Features

- **User Registration**: Create new user accounts with secure password hashing
- **User Login**: Authenticate users and generate JWT-like access tokens
- **Token-Based Auth**: Stateless authentication using signed tokens
- **Password Security**: PBKDF2 with SHA256 hashing, password strength validation
- **Password Change**: Allow users to update their passwords
- **Logout**: Token invalidation support

## Quick Start

```python
from auth import register, login, verify_token

# Register a new user
result = register("alice", "SecurePass123")
# Output: {'success': True, 'username': 'alice', 'message': 'User registered successfully'}

# Login
result = login("alice", "SecurePass123")
# Output: {'success': True, 'username': 'alice', 'token': 'eyJhbGci...', 'token_type': 'Bearer', ...}
token = result["token"]

# Verify token
result = verify_token(token)
# Output: {'success': True, 'username': 'alice', 'is_active': True}
```

## API Reference

### Convenience Functions

- `register(username, password)` - Register a new user
- `login(username, password)` - Login and get access token
- `logout(token)` - Logout user
- `verify_token(token)` - Verify access token validity
- `change_password(token, old_password, new_password)` - Change user password

### Classes

#### AuthService
Core authentication service with all business logic.

```python
from auth import AuthService
auth = AuthService()
```

#### AuthEndpoints
REST API endpoints wrapper for easy integration.

```python
from auth import AuthEndpoints
endpoints = AuthEndpoints()
result = endpoints.register("user", "password")
```

#### UserRepository
Data persistence layer for user storage.

```python
from auth import UserRepository
repo = UserRepository()
user = repo.get_user("alice")
```

## Password Requirements

- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit

## Token Format

Tokens use a JWT-like format with:
- Base64URL-encoded header and payload
- HMAC-SHA256 signature
- 24-hour expiration

## Security Features

- PBKDF2 password hashing (100,000 iterations)
- Random salts for each password
- Cryptographically secure token generation
- Timing-attack resistant password comparison
- Token expiration validation

## Testing

Run the test suite:

```bash
python3 test_auth.py
```

All 28 tests covering:
- Registration (success, duplicates, validation)
- Login (success, failure, invalid credentials)
- Token management (generation, verification, expiration)
- Password management (change, validation)
- Edge cases and error handling

## Files

- `auth.py` - Main authentication module (16KB)
- `test_auth.py` - Comprehensive test suite (13KB)
- `.data/users.json` - User data storage (auto-created)

## Integration

The module can be integrated into any Python application. No external dependencies required for basic usage.
