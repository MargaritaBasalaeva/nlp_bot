import sqlite3

def init_db():
    conn = sqlite3.connect("feedback.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            text TEXT NOT NULL,
            label TEXT CHECK(label IN ('positive', 'neutral', 'negative')),
            confidence REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def save_feedback_to_db(user_id, text, label, confidence):
    conn = sqlite3.connect("feedback.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO feedback (user_id, text, label, confidence) 
        VALUES (?, ?, ?, ?)""",
        (user_id, text, label, confidence)
    )
    conn.commit()
    conn.close()