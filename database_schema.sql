-- Database Schema for Users and Projects
-- Compatible with SQLite, PostgreSQL, MySQL

-- ============================================
-- USERS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,  -- Use SERIAL for PostgreSQL, AUTO_INCREMENT for MySQL
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE,
    password_hash VARCHAR(256) NOT NULL,
    salt VARCHAR(32) NOT NULL,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Indexes for users table
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);

-- ============================================
-- PROJECTS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'active',  -- active, archived, deleted
    owner_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    start_date DATE,
    end_date DATE,
    priority INTEGER DEFAULT 1,  -- 1: low, 2: medium, 3: high
    budget DECIMAL(12, 2),
    FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Indexes for projects table
CREATE INDEX IF NOT EXISTS idx_projects_owner ON projects(owner_id);
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
CREATE INDEX IF NOT EXISTS idx_projects_created_at ON projects(created_at);

-- ============================================
-- PROJECT MEMBERS TABLE (Many-to-Many)
-- ============================================
CREATE TABLE IF NOT EXISTS project_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    role VARCHAR(20) DEFAULT 'member',  -- owner, admin, member, viewer
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(project_id, user_id)  -- Prevent duplicate memberships
);

-- Indexes for project_members table
CREATE INDEX IF NOT EXISTS idx_pm_project ON project_members(project_id);
CREATE INDEX IF NOT EXISTS idx_pm_user ON project_members(user_id);

-- ============================================
-- PROJECT TASKS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'todo',  -- todo, in_progress, review, done
    priority INTEGER DEFAULT 2,  -- 1: low, 2: medium, 3: high, 4: urgent
    assigned_to INTEGER,
    created_by INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    due_date DATE,
    completed_at TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (assigned_to) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE
);

-- Indexes for tasks table
CREATE INDEX IF NOT EXISTS idx_tasks_project ON tasks(project_id);
CREATE INDEX IF NOT EXISTS idx_tasks_assigned ON tasks(assigned_to);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date);

-- ============================================
-- AUDIT LOG TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name VARCHAR(50) NOT NULL,
    record_id INTEGER NOT NULL,
    action VARCHAR(20) NOT NULL,  -- INSERT, UPDATE, DELETE
    old_values TEXT,  -- JSON string of old values
    new_values TEXT,  -- JSON string of new values
    performed_by INTEGER,
    performed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (performed_by) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_audit_table ON audit_log(table_name);
CREATE INDEX IF NOT EXISTS idx_audit_record ON audit_log(record_id);
CREATE INDEX IF NOT EXISTS idx_audit_performed_at ON audit_log(performed_at);

-- ============================================
-- TRIGGERS FOR UPDATED_AT
-- ============================================
-- SQLite version
CREATE TRIGGER IF NOT EXISTS update_users_timestamp 
AFTER UPDATE ON users
BEGIN
    UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_projects_timestamp 
AFTER UPDATE ON projects
BEGIN
    UPDATE projects SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_tasks_timestamp 
AFTER UPDATE ON tasks
BEGIN
    UPDATE tasks SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- ============================================
-- SAMPLE DATA (for development/testing)
-- ============================================
-- Uncomment to insert sample data

-- INSERT INTO users (username, email, password_hash, salt, first_name, last_name, is_admin)
-- VALUES ('admin', 'admin@example.com', 'hash_here', 'salt_here', 'System', 'Admin', TRUE);
--
-- INSERT INTO users (username, email, password_hash, salt, first_name, last_name)
-- VALUES ('bob', 'bob@example.com', 'hash_here', 'salt_here', 'Bob', 'Developer');
--
-- INSERT INTO users (username, email, password_hash, salt, first_name, last_name)
-- VALUES ('alice', 'alice@example.com', 'hash_here', 'salt_here', 'Alice', 'Designer');
--
-- INSERT INTO projects (name, description, owner_id, priority, budget)
-- VALUES ('Website Redesign', 'Redesign company website with modern UI', 2, 3, 50000.00);
--
-- INSERT INTO projects (name, description, owner_id, priority)
-- VALUES ('Mobile App', 'Develop iOS and Android mobile app', 2, 2);
--
-- INSERT INTO project_members (project_id, user_id, role)
-- VALUES (1, 2, 'owner'), (1, 3, 'member'), (2, 2, 'owner'), (2, 3, 'admin');
--
-- INSERT INTO tasks (project_id, title, description, assigned_to, created_by, priority, due_date)
-- VALUES (1, 'Create wireframes', 'Design initial wireframes for homepage', 3, 2, 3, '2025-04-15');
--
-- INSERT INTO tasks (project_id, title, description, assigned_to, created_by, priority, due_date)
-- VALUES (1, 'Setup project repo', 'Initialize Git repository', 2, 2, 2, '2025-04-10');
