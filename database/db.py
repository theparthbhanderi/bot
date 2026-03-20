"""
Database module for KINGPARTH Bot
Handles SQLite database operations for memory, premium, and user management.
"""

import sqlite3
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

# Database file path
DB_PATH = os.path.join(os.path.dirname(__file__), 'telegram_bot.db')


def get_connection():
    """
    Get a database connection.
    
    Returns:
        sqlite3.Connection: Database connection object
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Enable column name access
    return conn


def init_database():
    """
    Initialize the database with required tables.
    Creates tables for:
    - user_messages: Stores conversation history
    - user_usage: Tracks API usage for premium system
    - users: Stores user information
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Table to store user messages (memory system)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Table to track user usage (premium system)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            daily_queries INTEGER DEFAULT 0,
            last_query_date DATE DEFAULT CURRENT_DATE,
            is_premium INTEGER DEFAULT 0,
            total_queries INTEGER DEFAULT 0
        )
    ''')
    
    # Table to store user information
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            is_premium INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_seen DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Table for RAG knowledge base
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS knowledge_base (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            embedding BLOB,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Database initialized successfully!")


# ==================== Memory System ====================

def add_message(user_id: int, role: str, content: str):
    """
    Add a message to user's conversation history.
    
    Args:
        user_id: Telegram user ID
        role: Message role ('user' or 'assistant')
        content: Message content
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        'INSERT INTO user_messages (user_id, role, content) VALUES (?, ?, ?)',
        (user_id, role, content)
    )
    
    conn.commit()
    conn.close()


def get_conversation_history(user_id: int, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Get the last N messages from user's conversation history.
    
    Args:
        user_id: Telegram user ID
        limit: Number of recent messages to retrieve (default: 5)
    
    Returns:
        List of message dictionaries with 'role' and 'content'
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT role, content 
        FROM user_messages 
        WHERE user_id = ? 
        ORDER BY timestamp DESC 
        LIMIT ?
    ''', (user_id, limit))
    
    rows = cursor.fetchall()
    conn.close()
    
    # Reverse to get chronological order
    messages = [{'role': row['role'], 'content': row['content']} for row in rows]
    return list(reversed(messages))


def clear_conversation(user_id: int):
    """
    Clear a user's conversation history.
    
    Args:
        user_id: Telegram user ID
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM user_messages WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()


# ==================== Premium System ====================

def init_user_usage(user_id: int):
    """
    Initialize user usage record if not exists.
    
    Args:
        user_id: Telegram user ID
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT OR IGNORE INTO user_usage (user_id, daily_queries, last_query_date)
        VALUES (?, 0, date('now'))
    ''', (user_id,))
    
    conn.commit()
    conn.close()


def check_daily_limit(user_id: int, daily_limit: int = 10) -> bool:
    """
    Check if user has exceeded their daily query limit.
    
    Args:
        user_id: Telegram user ID
        daily_limit: Maximum free queries per day (default: 10)
    
    Returns:
        bool: True if user can query, False if limit exceeded
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Initialize user if not exists
    init_user_usage(user_id)
    
    cursor.execute('''
        SELECT daily_queries, last_query_date, is_premium 
        FROM user_usage 
        WHERE user_id = ?
    ''', (user_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row['is_premium']:
        return True  # Premium users have unlimited access
    
    # Reset daily count if it's a new day
    today = datetime.now().date()
    last_date = datetime.strptime(row['last_query_date'], '%Y-%m-%d').date()
    
    if today > last_date:
        reset_daily_usage(user_id)
        return True
    
    return row['daily_queries'] < daily_limit


def increment_daily_usage(user_id: int):
    """
    Increment the daily query count for a user.
    
    Args:
        user_id: Telegram user ID
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE user_usage 
        SET daily_queries = daily_queries + 1,
            total_queries = total_queries + 1
        WHERE user_id = ?
    ''', (user_id,))
    
    conn.commit()
    conn.close()


def get_daily_usage(user_id: int) -> Dict[str, Any]:
    """
    Get current daily usage for a user.
    
    Args:
        user_id: Telegram user ID
    
    Returns:
        Dictionary with usage statistics
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    init_user_usage(user_id)
    
    cursor.execute('''
        SELECT daily_queries, total_queries, is_premium
        FROM user_usage 
        WHERE user_id = ?
    ''', (user_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    return {
        'daily_queries': row['daily_queries'],
        'total_queries': row['total_queries'],
        'is_premium': bool(row['is_premium'])
    }


def reset_daily_usage(user_id: int):
    """
    Reset daily query count for a user.
    
    Args:
        user_id: Telegram user ID
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE user_usage 
        SET daily_queries = 0, last_query_date = date('now')
        WHERE user_id = ?
    ''', (user_id,))
    
    conn.commit()
    conn.close()


def set_premium_status(user_id: int, is_premium: bool):
    """
    Set premium status for a user.
    
    Args:
        user_id: Telegram user ID
        is_premium: Whether user should have premium status
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE user_usage SET is_premium = ? WHERE user_id = ?
    ''', (1 if is_premium else 0, user_id,))
    
    cursor.execute('''
        UPDATE users SET is_premium = ? WHERE user_id = ?
    ''', (1 if is_premium else 0, user_id,))
    
    conn.commit()
    conn.close()


# ==================== User Management ====================

def add_user(user_id: int, username: str = None, first_name: str = None, last_name: str = None):
    """
    Add or update a user in the database.
    
    Args:
        user_id: Telegram user ID
        username: Telegram username
        first_name: User's first name
        last_name: User's last name
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO users (user_id, username, first_name, last_name)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            username = excluded.username,
            first_name = excluded.first_name,
            last_name = excluded.last_name,
            last_seen = CURRENT_TIMESTAMP
    ''', (user_id, username, first_name, last_name))
    
    conn.commit()
    conn.close()


def get_user(user_id: int) -> Optional[Dict[str, Any]]:
    """
    Get user information.
    
    Args:
        user_id: Telegram user ID
    
    Returns:
        User information dictionary or None
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None


# ==================== Knowledge Base (RAG) ====================

def add_to_knowledge_base(user_id: int, title: str, content: str, embedding: bytes = None):
    """
    Add content to user's knowledge base.
    
    Args:
        user_id: Telegram user ID
        title: Content title
        content: Content text
        embedding: Optional vector embedding
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO knowledge_base (user_id, title, content, embedding)
        VALUES (?, ?, ?, ?)
    ''', (user_id, title, content, embedding))
    
    conn.commit()
    conn.close()


def get_knowledge_base(user_id: int) -> List[Dict[str, Any]]:
    """
    Get all content from user's knowledge base.
    
    Args:
        user_id: Telegram user ID
    
    Returns:
        List of knowledge base entries
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT title, content FROM knowledge_base 
        WHERE user_id = ?
        ORDER BY created_at DESC
    ''', (user_id,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [{'title': row['title'], 'content': row['content']} for row in rows]


# Initialize database on module import
init_database()
