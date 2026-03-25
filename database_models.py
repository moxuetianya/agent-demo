"""
Database Models for Users and Projects
Python ORM-style classes for database interaction.
"""

import sqlite3
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
from contextlib import contextmanager

DATABASE_FILE = "app.db"


@dataclass
class User:
    """User model representing a user in the system."""
    id: Optional[int] = None
    username: str = ""
    email: Optional[str] = None
    password_hash: str = ""
    salt: str = ""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: bool = True
    is_admin: bool = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    last_login: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @property
    def full_name(self) -> str:
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username


@dataclass
class Project:
    """Project model representing a project in the system."""
    id: Optional[int] = None
    name: str = ""
    description: Optional[str] = None
    status: str = "active"  # active, archived, deleted
    owner_id: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    priority: int = 1
    budget: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ProjectMember:
    """Project membership linking users to projects."""
    id: Optional[int] = None
    project_id: int = 0
    user_id: int = 0
    role: str = "member"  # owner, admin, member, viewer
    joined_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Task:
    """Task model for project tasks."""
    id: Optional[int] = None
    project_id: int = 0
    title: str = ""
    description: Optional[str] = None
    status: str = "todo"  # todo, in_progress, review, done
    priority: int = 2
    assigned_to: Optional[int] = None
    created_by: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    due_date: Optional[str] = None
    completed_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class DatabaseManager:
    """Manager class for database operations."""
    
    def __init__(self, db_file: str = DATABASE_FILE):
        self.db_file = db_file
        self._init_database()
    
    @contextmanager
    def _get_connection(self):
        """Get database connection with row factory."""
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def _init_database(self):
        """Initialize database with schema from SQL file."""
        with self._get_connection() as conn:
            with open('database_schema.sql', 'r') as f:
                conn.executescript(f.read())
    
    # ==================== USER OPERATIONS ====================
    
    def create_user(self, user: User) -> int:
        """Create a new user and return the ID."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """INSERT INTO users (username, email, password_hash, salt, 
                    first_name, last_name, is_active, is_admin)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (user.username, user.email, user.password_hash, user.salt,
                 user.first_name, user.last_name, user.is_active, user.is_admin)
            )
            return cursor.lastrowid
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE id = ?", (user_id,)
            ).fetchone()
            if row:
                return User(**dict(row))
            return None
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE username = ?", (username,)
            ).fetchone()
            if row:
                return User(**dict(row))
            return None
    
    def update_user(self, user: User) -> bool:
        """Update user information."""
        with self._get_connection() as conn:
            conn.execute(
                """UPDATE users SET email = ?, first_name = ?, last_name = ?,
                    is_active = ?, is_admin = ? WHERE id = ?""",
                (user.email, user.first_name, user.last_name, 
                 user.is_active, user.is_admin, user.id)
            )
            return True
    
    def delete_user(self, user_id: int) -> bool:
        """Delete a user."""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
            return True
    
    def list_users(self) -> List[User]:
        """Get all users."""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM users ORDER BY created_at DESC").fetchall()
            return [User(**dict(row)) for row in rows]
    
    # ==================== PROJECT OPERATIONS ====================
    
    def create_project(self, project: Project) -> int:
        """Create a new project and return the ID."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """INSERT INTO projects (name, description, status, owner_id, 
                    start_date, end_date, priority, budget)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (project.name, project.description, project.status, project.owner_id,
                 project.start_date, project.end_date, project.priority, project.budget)
            )
            # Add owner as project member
            project_id = cursor.lastrowid
            conn.execute(
                """INSERT INTO project_members (project_id, user_id, role)
                   VALUES (?, ?, 'owner')""",
                (project_id, project.owner_id)
            )
            return project_id
    
    def get_project_by_id(self, project_id: int) -> Optional[Project]:
        """Get project by ID."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM projects WHERE id = ?", (project_id,)
            ).fetchone()
            if row:
                return Project(**dict(row))
            return None
    
    def update_project(self, project: Project) -> bool:
        """Update project information."""
        with self._get_connection() as conn:
            conn.execute(
                """UPDATE projects SET name = ?, description = ?, status = ?,
                    start_date = ?, end_date = ?, priority = ?, budget = ?
                   WHERE id = ?""",
                (project.name, project.description, project.status,
                 project.start_date, project.end_date, project.priority, 
                 project.budget, project.id)
            )
            return True
    
    def delete_project(self, project_id: int) -> bool:
        """Delete a project."""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
            return True
    
    def list_projects(self, owner_id: Optional[int] = None) -> List[Project]:
        """Get all projects, optionally filtered by owner."""
        with self._get_connection() as conn:
            if owner_id:
                rows = conn.execute(
                    "SELECT * FROM projects WHERE owner_id = ? ORDER BY created_at DESC",
                    (owner_id,)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM projects ORDER BY created_at DESC"
                ).fetchall()
            return [Project(**dict(row)) for row in rows]
    
    def get_user_projects(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all projects for a user (as member or owner)."""
        with self._get_connection() as conn:
            rows = conn.execute(
                """SELECT p.*, pm.role as membership_role
                   FROM projects p
                   JOIN project_members pm ON p.id = pm.project_id
                   WHERE pm.user_id = ?
                   ORDER BY p.created_at DESC""",
                (user_id,)
            ).fetchall()
            return [dict(row) for row in rows]
    
    # ==================== PROJECT MEMBER OPERATIONS ====================
    
    def add_project_member(self, project_id: int, user_id: int, role: str = "member") -> bool:
        """Add a member to a project."""
        with self._get_connection() as conn:
            try:
                conn.execute(
                    """INSERT INTO project_members (project_id, user_id, role)
                       VALUES (?, ?, ?)""",
                    (project_id, user_id, role)
                )
                return True
            except sqlite3.IntegrityError:
                return False  # Already a member
    
    def remove_project_member(self, project_id: int, user_id: int) -> bool:
        """Remove a member from a project."""
        with self._get_connection() as conn:
            conn.execute(
                "DELETE FROM project_members WHERE project_id = ? AND user_id = ?",
                (project_id, user_id)
            )
            return True
    
    def get_project_members(self, project_id: int) -> List[Dict[str, Any]]:
        """Get all members of a project with user details."""
        with self._get_connection() as conn:
            rows = conn.execute(
                """SELECT u.id, u.username, u.email, u.first_name, u.last_name,
                          pm.role, pm.joined_at
                   FROM users u
                   JOIN project_members pm ON u.id = pm.user_id
                   WHERE pm.project_id = ?""",
                (project_id,)
            ).fetchall()
            return [dict(row) for row in rows]
    
    # ==================== STATISTICS ====================
    
    def get_stats(self) -> Dict[str, int]:
        """Get database statistics."""
        with self._get_connection() as conn:
            user_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            project_count = conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
            task_count = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
            
            return {
                "users": user_count,
                "projects": project_count,
                "tasks": task_count
            }


# Demo usage
if __name__ == "__main__":
    print("=== Database Schema Demo ===\n")
    
    db = DatabaseManager()
    
    # Create users
    print("1. Creating users...")
    user1 = User(
        username="bob",
        email="bob@example.com",
        password_hash="hashed_password",
        salt="random_salt",
        first_name="Bob",
        last_name="Developer"
    )
    user1_id = db.create_user(user1)
    print(f"   Created user 'bob' with ID: {user1_id}")
    
    user2 = User(
        username="alice",
        email="alice@example.com",
        password_hash="hashed_password",
        salt="random_salt",
        first_name="Alice",
        last_name="Designer"
    )
    user2_id = db.create_user(user2)
    print(f"   Created user 'alice' with ID: {user2_id}\n")
    
    # Create project
    print("2. Creating project...")
    project = Project(
        name="Website Redesign",
        description="Modernize company website",
        owner_id=user1_id,
        priority=3,
        budget=50000.00
    )
    project_id = db.create_project(project)
    print(f"   Created project with ID: {project_id}\n")
    
    # Add member
    print("3. Adding member to project...")
    db.add_project_member(project_id, user2_id, "admin")
    print(f"   Added 'alice' as admin to project\n")
    
    # Get project members
    print("4. Project members:")
    members = db.get_project_members(project_id)
    for member in members:
        print(f"   - {member['username']} ({member['role']})")
    
    # Get stats
    print("\n5. Database statistics:")
    stats = db.get_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    # Get user's projects
    print("\n6. Bob's projects:")
    projects = db.get_user_projects(user1_id)
    for proj in projects:
        print(f"   - {proj['name']} (role: {proj['membership_role']})")
    
    print("\n=== Demo Complete ===")
