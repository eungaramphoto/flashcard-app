import os
import random
import sqlite3
import pandas as pd
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, RedirectResponse

DB = "jlpt.db"
DECK_FOLDER = "decks"

app = FastAPI()


# ----------------------
# DB 초기화
# ----------------------
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS words (
        id INTEGER,
        deck TEXT,
        front TEXT,
        back TEXT,
        explanation TEXT,
        example TEXT
    )
    """)
    conn.commit()
    conn.close()


def load_deck(deck):
    path = os.path.join(DECK_FOLDER, deck)
    if not os.path.exists(path):
        return

    df = pd.read_excel(path)

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("DELETE FROM words")

    for _, row in df.iterrows():
        c.execute("INSERT INTO words VALUES (?, ?, ?, ?, ?, ?)",
                  (int(row["id"]), deck,
                   row["front"], row["back"],
                   row["explanation"], row["example"]))

    conn.commit()
    conn.close()


# ----------------------
# A단계 : 덱 선택
# ----------------------
@app.get("/", response_class=HTMLResponse)
def select_deck():
    decks = [f for f in os.listdir(DECK_FOLDER) if f.endswith(".xlsx")]
    html = "<h2>덱 선택</h2>"
    for d in decks:
        html += f'<a href="/start/{d}"><button>{d}</button></a><br><br>'
    return html


@app.get("/start/{deck}")
def start(deck: str):
    load_deck(deck)
    return RedirectResponse("/study", status_code=302)


# ----------------------
# 랜덤 재생
# ----------------------
@app.get("/study", response_class=HTMLResponse)
def study():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT id, front FROM words")
    rows = c.fetchall()
    conn.close()

    if not rows:
        return "<h3>덱을 먼저 선택하세요</h3><a href='/'>돌아가기</a>"

    word_id, front = random.choice(rows)

    return f"""
    <p style="font-size:30px;">{front}</p>

    <a href="/answer/{word_id}"><button>정답보기</button></a>
    <a href="/study"><button>다음 단어</button></a>
    <a href="/"><button>덱 선택화면으로</button></a>
    """


@app.get("/answer/{word_id}", response_class=HTMLResponse)
def answer(word_id: int):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT back, explanation, example FROM words WHERE id=?", (word_id,))
    row = c.fetchone()
    conn.close()

    if not row:
        return RedirectResponse("/study", status_code=302)

    back, exl, exm = row

    return f"""
    <p><b>{back}</b></p>
    <p>{exl}</p>
    <p>{exm}</p>

    <a href="/study"><button>다음 단어</button></a>
    """


init_db()

