-- Users table for authentication
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT DEFAULT 'user'
);

-- User profile table for eligibility data
CREATE TABLE IF NOT EXISTS user_profile (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    age INTEGER,
    income REAL,
    category TEXT,  -- SC/ST/OBC/General
    education TEXT,
    occupation TEXT,
    location TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Schemes table
CREATE TABLE IF NOT EXISTS schemes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    income_limit REAL,
    category_required TEXT,
    education_required TEXT,
    occupation_required TEXT,
    benefits TEXT,
    application_link TEXT
);