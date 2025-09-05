import aiosqlite
import asyncio
from datetime import datetime
from typing import List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path: str = "bot.db"):
        self.db_path = db_path
    
    async def init_db(self):
        """Initialize database tables"""
        async with aiosqlite.connect(self.db_path) as db:
            # Users table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER UNIQUE NOT NULL,
                    join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Questions table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    category TEXT NOT NULL,
                    text TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_deleted BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            # Answers table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS answers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    votes INTEGER DEFAULT 0,
                    is_pinned BOOLEAN DEFAULT FALSE,
                    is_deleted BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (question_id) REFERENCES questions (id),
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            # Votes table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS votes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    answer_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    value INTEGER NOT NULL CHECK (value IN (1, -1)),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(answer_id, user_id),
                    FOREIGN KEY (answer_id) REFERENCES answers (id),
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            await db.commit()
            logger.info("Database initialized successfully")
    
    async def add_user(self, telegram_id: int) -> int:
        """Add user to database and return user_id"""
        async with aiosqlite.connect(self.db_path) as db:
            # Check if user exists
            cursor = await db.execute(
                "SELECT id FROM users WHERE telegram_id = ?", (telegram_id,)
            )
            user = await cursor.fetchone()
            
            if user:
                return user[0]
            
            # Add new user
            cursor = await db.execute(
                "INSERT INTO users (telegram_id) VALUES (?)", (telegram_id,)
            )
            await db.commit()
            return cursor.lastrowid
    
    async def add_question(self, user_id: int, category: str, text: str) -> int:
        """Add question to database and return question_id"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "INSERT INTO questions (user_id, category, text) VALUES (?, ?, ?)",
                (user_id, category, text)
            )
            await db.commit()
            return cursor.lastrowid
    
    async def get_questions(self, page: int = 0, limit: int = 5) -> List[Tuple]:
        """Get paginated questions"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """SELECT q.id, q.category, q.text, q.created_at, COUNT(a.id) as answer_count
                   FROM questions q
                   LEFT JOIN answers a ON q.id = a.question_id AND a.is_deleted = FALSE
                   WHERE q.is_deleted = FALSE
                   GROUP BY q.id
                   ORDER BY q.created_at DESC
                   LIMIT ? OFFSET ?""",
                (limit, page * limit)
            )
            return await cursor.fetchall()
    
    async def get_question_by_id(self, question_id: int) -> Optional[Tuple]:
        """Get question by ID"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT id, category, text, created_at FROM questions WHERE id = ? AND is_deleted = FALSE",
                (question_id,)
            )
            return await cursor.fetchone()
    
    async def add_answer(self, question_id: int, user_id: int, text: str) -> int:
        """Add answer to database and return answer_id"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "INSERT INTO answers (question_id, user_id, text) VALUES (?, ?, ?)",
                (question_id, user_id, text)
            )
            await db.commit()
            return cursor.lastrowid
    
    async def get_answers(self, question_id: int, page: int = 0, limit: int = 10) -> List[Tuple]:
        """Get paginated answers for a question"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """SELECT id, text, created_at, votes, is_pinned
                   FROM answers
                   WHERE question_id = ? AND is_deleted = FALSE
                   ORDER BY is_pinned DESC, votes DESC, created_at ASC
                   LIMIT ? OFFSET ?""",
                (question_id, limit, page * limit)
            )
            return await cursor.fetchall()
    
    async def get_top_answers(self, page: int = 0, limit: int = 10) -> List[Tuple]:
        """Get top-rated answers across all questions"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """SELECT a.id, a.text, a.votes, a.created_at, q.text as question_text, q.category
                   FROM answers a
                   JOIN questions q ON a.question_id = q.id
                   WHERE a.is_deleted = FALSE AND q.is_deleted = FALSE
                   ORDER BY a.votes DESC, a.created_at DESC
                   LIMIT ? OFFSET ?""",
                (limit, page * limit)
            )
            return await cursor.fetchall()
    
    async def vote_answer(self, answer_id: int, user_id: int, vote_value: int) -> bool:
        """Vote on an answer (1 for upvote, -1 for downvote)"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                # Check if user already voted
                cursor = await db.execute(
                    "SELECT value FROM votes WHERE answer_id = ? AND user_id = ?",
                    (answer_id, user_id)
                )
                existing_vote = await cursor.fetchone()
                
                if existing_vote:
                    if existing_vote[0] == vote_value:
                        return False  # Same vote, no change
                    
                    # Update existing vote
                    await db.execute(
                        "UPDATE votes SET value = ? WHERE answer_id = ? AND user_id = ?",
                        (vote_value, answer_id, user_id)
                    )
                    
                    # Update answer vote count
                    vote_diff = vote_value - existing_vote[0]
                    await db.execute(
                        "UPDATE answers SET votes = votes + ? WHERE id = ?",
                        (vote_diff, answer_id)
                    )
                else:
                    # Add new vote
                    await db.execute(
                        "INSERT INTO votes (answer_id, user_id, value) VALUES (?, ?, ?)",
                        (answer_id, user_id, vote_value)
                    )
                    
                    # Update answer vote count
                    await db.execute(
                        "UPDATE answers SET votes = votes + ? WHERE id = ?",
                        (vote_value, answer_id)
                    )
                
                await db.commit()
                return True
                
            except Exception as e:
                logger.error(f"Error voting on answer: {e}")
                return False
    
    async def delete_question(self, question_id: int) -> bool:
        """Soft delete a question"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute(
                    "UPDATE questions SET is_deleted = TRUE WHERE id = ?",
                    (question_id,)
                )
                await db.commit()
                return True
            except Exception as e:
                logger.error(f"Error deleting question: {e}")
                return False
    
    async def delete_answer(self, answer_id: int) -> bool:
        """Soft delete an answer"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute(
                    "UPDATE answers SET is_deleted = TRUE WHERE id = ?",
                    (answer_id,)
                )
                await db.commit()
                return True
            except Exception as e:
                logger.error(f"Error deleting answer: {e}")
                return False
    
    async def pin_answer(self, answer_id: int, pin: bool = True) -> bool:
        """Pin or unpin an answer"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute(
                    "UPDATE answers SET is_pinned = ? WHERE id = ?",
                    (pin, answer_id)
                )
                await db.commit()
                return True
            except Exception as e:
                logger.error(f"Error pinning answer: {e}")
                return False
    
    async def get_question_count(self) -> int:
        """Get total number of questions"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT COUNT(*) FROM questions WHERE is_deleted = FALSE"
            )
            result = await cursor.fetchone()
            return result[0] if result else 0
    
    async def get_answer_count(self, question_id: int) -> int:
        """Get total number of answers for a question"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT COUNT(*) FROM answers WHERE question_id = ? AND is_deleted = FALSE",
                (question_id,)
            )
            result = await cursor.fetchone()
            return result[0] if result else 0