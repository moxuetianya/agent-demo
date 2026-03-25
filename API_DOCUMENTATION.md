# Agent Demo API Documentation

## Overview

This document describes the REST API endpoints for the Agent Demo authentication system. The API provides user authentication, registration, and management capabilities.

## Base URL

```
http://localhost:8000
```

## Authentication

Most endpoints require authentication using a Bearer token in the Authorization header:

```
Authorization: Bearer <your_access_token>
```

## Endpoints

---

### Authentication Endpoints

#### 1. Register User

Create a new user account.

**Endpoint:** `POST /api/auth/register`

**Request Body:**
```json
{
  "username": "string",     // Required, min 3 characters, alphanumeric only
  "password": "string"      // Required, min 8 chars, upper, lower, digit required
}
```

**Response (Success - 201):**
```json
{
  "success": true,
  "username": "string",
  "message": "User registered successfully"
}
```

**Response (Error - 400):**
```json
{
  "success": false,
  "error": "User 'username' already exists"
}
```

**Error Codes:**
- `400` - Bad Request (weak password, invalid username, user exists)

---

#### 2. Login

Authenticate a user and receive an access token.

**Endpoint:** `POST /api/auth/login`

**Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response (Success - 200):**
```json
{
  "success": true,
  "username": "string",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 86400,
  "message": "Login successful"
}
```

**Response (Error - 401):**
```json
{
  "success": false,
  "error": "Invalid username or password"
}
```

---

#### 3. Logout

Invalidate the current access token.

**Endpoint:** `POST /api/auth/logout`

**Headers:**
```
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "token": "string"  // Optional if provided in header
}
```

**Response (Success - 200):**
```json
{
  "success": true,
  "username": "string",
  "message": "Logout successful"
}
```

**Response (Error - 401):**
```json
{
  "success": false,
  "message": "Invalid token"
}
```

---

#### 4. Verify Token

Validate an access token and get user information.

**Endpoint:** `POST /api/auth/verify`

**Headers:**
```
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "token": "string"
}
```

**Response (Success - 200):**
```json
{
  "success": true,
  "username": "string",
  "is_active": true
}
```

**Response (Error - 401):**
```json
{
  "success": false,
  "error": "Invalid or expired token"
}
```

---

#### 5. Change Password

Update the password for the authenticated user.

**Endpoint:** `POST /api/auth/change-password`

**Headers:**
```
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "old_password": "string",
  "new_password": "string"  // Must meet password requirements
}
```

**Response (Success - 200):**
```json
{
  "success": true,
  "message": "Password changed successfully"
}
```

**Response (Error - 400):**
```json
{
  "success": false,
  "error": "Current password is incorrect"
}
```

**Response (Error - 401):**
```json
{
  "success": false,
  "error": "Invalid or expired token"
}
```

---

### User Endpoints

#### 6. Get Current User

Get information about the currently authenticated user.

**Endpoint:** `GET /api/users/me`

**Headers:**
```
Authorization: Bearer <token>
```

**Response (Success - 200):**
```json
{
  "id": 1,
  "username": "string",
  "email": "user@example.com",
  "first_name": "string",
  "last_name": "string",
  "is_active": true,
  "is_admin": false,
  "created_at": "2024-01-01T00:00:00",
  "last_login": "2024-01-01T00:00:00"
}
```

---

#### 7. List Users

Get a list of all registered users (admin only).

**Endpoint:** `GET /api/users`

**Headers:**
```
Authorization: Bearer <token>
```

**Response (Success - 200):**
```json
{
  "users": [
    {
      "id": 1,
      "username": "string",
      "email": "user@example.com",
      "is_active": true
    }
  ],
  "total": 1
}
```

---

### Project Endpoints

#### 8. Create Project

Create a new project.

**Endpoint:** `POST /api/projects`

**Headers:**
```
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "name": "string",           // Required
  "description": "string",    // Optional
  "status": "active",         // active, archived, deleted
  "start_date": "2024-01-01", // Optional, ISO format
  "end_date": "2024-12-31",   // Optional, ISO format
  "priority": 1,               // 1-5
  "budget": 10000.00          // Optional
}
```

**Response (Success - 201):**
```json
{
  "success": true,
  "project_id": 1,
  "message": "Project created successfully"
}
```

---

#### 9. Get Project

Retrieve a specific project by ID.

**Endpoint:** `GET /api/projects/{project_id}`

**Headers:**
```
Authorization: Bearer <token>
```

**Response (Success - 200):**
```json
{
  "id": 1,
  "name": "string",
  "description": "string",
  "status": "active",
  "owner_id": 1,
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00",
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "priority": 1,
  "budget": 10000.00
}
```

---

#### 10. List Projects

Get all projects accessible to the authenticated user.

**Endpoint:** `GET /api/projects`

**Headers:**
```
Authorization: Bearer <token>
```

**Query Parameters:**
- `owner_id` (optional) - Filter by owner

**Response (Success - 200):**
```json
{
  "projects": [
    {
      "id": 1,
      "name": "string",
      "description": "string",
      "status": "active",
      "membership_role": "owner"
    }
  ]
}
```

---

#### 11. Update Project

Update project information.

**Endpoint:** `PUT /api/projects/{project_id}`

**Headers:**
```
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "name": "string",
  "description": "string",
  "status": "active",
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "priority": 1,
  "budget": 10000.00
}
```

**Response (Success - 200):**
```json
{
  "success": true,
  "message": "Project updated successfully"
}
```

---

#### 12. Delete Project

Delete a project.

**Endpoint:** `DELETE /api/projects/{project_id}`

**Headers:**
```
Authorization: Bearer <token>
```

**Response (Success - 200):**
```json
{
  "success": true,
  "message": "Project deleted successfully"
}
```

---

### Project Members Endpoints

#### 13. Add Project Member

Add a user to a project.

**Endpoint:** `POST /api/projects/{project_id}/members`

**Headers:**
```
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "user_id": 1,
  "role": "member"  // owner, admin, member, viewer
}
```

**Response (Success - 201):**
```json
{
  "success": true,
  "message": "Member added successfully"
}
```

---

#### 14. Remove Project Member

Remove a user from a project.

**Endpoint:** `DELETE /api/projects/{project_id}/members/{user_id}`

**Headers:**
```
Authorization: Bearer <token>
```

**Response (Success - 200):**
```json
{
  "success": true,
  "message": "Member removed successfully"
}
```

---

#### 15. List Project Members

Get all members of a project.

**Endpoint:** `GET /api/projects/{project_id}/members`

**Headers:**
```
Authorization: Bearer <token>
```

**Response (Success - 200):**
```json
{
  "members": [
    {
      "id": 1,
      "username": "string",
      "email": "user@example.com",
      "first_name": "string",
      "last_name": "string",
      "role": "owner",
      "joined_at": "2024-01-01T00:00:00"
    }
  ]
}
```

---

## Data Models

### User

| Field | Type | Description |
|-------|------|-------------|
| id | integer | Unique identifier |
| username | string | Unique username (3-50 chars, alphanumeric) |
| email | string | Email address |
| first_name | string | First name |
| last_name | string | Last name |
| is_active | boolean | Account status |
| is_admin | boolean | Admin privileges |
| created_at | datetime | Account creation timestamp |
| updated_at | datetime | Last update timestamp |
| last_login | datetime | Last login timestamp |

### Project

| Field | Type | Description |
|-------|------|-------------|
| id | integer | Unique identifier |
| name | string | Project name (required) |
| description | string | Project description |
| status | string | active, archived, deleted |
| owner_id | integer | ID of project owner |
| created_at | datetime | Creation timestamp |
| updated_at | datetime | Last update timestamp |
| start_date | date | Project start date |
| end_date | date | Project end date |
| priority | integer | 1 (low) to 5 (high) |
| budget | float | Project budget |

### ProjectMember

| Field | Type | Description |
|-------|------|-------------|
| project_id | integer | Project ID |
| user_id | integer | User ID |
| role | string | owner, admin, member, viewer |
| joined_at | datetime | When user joined |

---

## Error Codes

| HTTP Code | Meaning | Description |
|-----------|---------|-------------|
| 200 | OK | Request succeeded |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Invalid request data |
| 401 | Unauthorized | Invalid or missing authentication |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 409 | Conflict | Resource conflict (e.g., duplicate) |
| 500 | Internal Server Error | Server error |

---

## Password Requirements

Passwords must meet the following criteria:
- Minimum 8 characters
- At least one uppercase letter (A-Z)
- At least one lowercase letter (a-z)
- At least one digit (0-9)

---

## Token Information

- **Type:** JWT-like custom token
- **Algorithm:** HMAC-SHA256
- **Expiration:** 24 hours
- **Format:** `header.payload.signature`

---

## Example Usage

### Register a new user
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "password": "SecurePass123"
  }'
```

### Login
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "password": "SecurePass123"
  }'
```

### Create a project
```bash
curl -X POST http://localhost:8000/api/projects \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "name": "My New Project",
    "description": "A sample project",
    "priority": 3
  }'
```

---

## Rate Limiting

- Authentication endpoints: 5 requests per minute per IP
- Other endpoints: 100 requests per minute per user

---

## Changelog

### Version 1.0.0
- Initial API release
- User authentication endpoints
- Project management endpoints
- Member management endpoints
