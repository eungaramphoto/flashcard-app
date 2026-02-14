import os
import random
import sqlite3
import pandas as pd
from fastapi import FastAPI, HTTPException

app = FastAPI()
DB = "jlpt.db"
DECK_FOLDER = "decks"

# ------------------------
# DB 초기화
# ------------------------
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS decks (
        name TEXT PRIMARY KEY,
        current_round INTEGER DEFAULT 1
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS words (
        id INTEGER,
        deck TEXT,
        front TEXT,
        PRIMARY KEY (id, deck)
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS study_queue (
        id INTEGER,
        deck TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS retry_queue (
        id INTEGER,
        deck TEXT
    )
    """)

    conn.commit()
    conn.close()

# ------------------------
# 덱 로드
# ------------------------
def load_deck(deck_name):
    path = os.path.join(DECK_FOLDER, deck_name)
    if not os.path.exists(path):
        raise HTTPException(404, "Deck not found")

    df = pd.read_excel(path)

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("DELETE FROM words WHERE deck=?", (deck_name,))
    c.execute("DELETE FROM study_queue WHERE deck=?", (deck_name,))
    c.execute("DELETE FROM retry_queue WHERE deck=?", (deck_name,))

    for _, row in df.iterrows():
        c.execute("INSERT INTO words VALUES (?, ?, ?)",
                  (int(row["id"]), deck_name, row["front"]))
        c.execute("INSERT INTO study_queue VALUES (?, ?)",
                  (int(row["id"]), deck_name))

    c.execute("INSERT OR IGNORE INTO decks (name) VALUES (?)", (deck_name,))
    conn.commit()
    conn.close()

# ------------------------
# API
# ------------------------

@app.get("/decks")
def list_decks():
    return os.listdir(DECK_FOLDER)

@app.post("/start/{deck_name}")
def start_deck(deck_name: str):
    load_deck(deck_name)
    return {"message": f"{deck_name} loaded"}

@app.get("/next/{deck_name}")
def next_word(deck_name: str):
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("SELECT id FROM study_queue WHERE deck=?", (deck_name,))
    rows = c.fetchall()

    if not rows:
        # 회독 완료 → retry_queue 이동
        c.execute("SELECT id FROM retry_queue WHERE deck=?", (deck_name,))
        retry_rows = c.fetchall()

        if not retry_rows:
            conn.close()
            return {"message": "All memorized"}

        # retry → study_queue 이동
        for r in retry_rows:
            c.execute("INSERT INTO study_queue VALUES (?, ?)",
                      (r[0], deck_name))
        c.execute("DELETE FROM retry_queue WHERE deck=?", (deck_name,))
        c.execute("UPDATE decks SET current_round = current_round + 1 WHERE name=?", (deck_name,))
        conn.commit()

        conn.close()
        return {"message": "New round started"}

    word_id = random.choice(rows)[0]

    c.execute("SELECT front FROM words WHERE id=? AND deck=?",
              (word_id, deck_name))
    front = c.fetchone()[0]

    conn.close()

    return {
        "id": word_id,
        "front": front
    }

@app.post("/known/{deck_name}/{word_id}")
def mark_known(deck_name: str, word_id: int):
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("DELETE FROM study_queue WHERE id=? AND deck=?",
              (word_id, deck_name))

    conn.commit()
    conn.close()

    return {"result": "removed"}

@app.post("/retry/{deck_name}/{word_id}")
def mark_retry(deck_name: str, word_id: int):
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("DELETE FROM study_queue WHERE id=? AND deck=?",
              (word_id, deck_name))

    c.execute("INSERT INTO retry_queue VALUES (?, ?)",
              (word_id, deck_name))

    conn.commit()
    conn.close()

    return {"result": "queued for retry"}

@app.get("/status/{deck_name}")
def get_status(deck_name: str):
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("SELECT current_round FROM decks WHERE name=?", (deck_name,))
    round_num = c.fetchone()

    c.execute("SELECT COUNT(*) FROM study_queue WHERE deck=?", (deck_name,))
    remaining = c.fetchone()[0]

    conn.close()

    return {
        "round": round_num[0] if round_num else 1,
        "remaining": remaining
    }

# ------------------------
init_db()

