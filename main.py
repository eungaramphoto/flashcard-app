import os
import random
import sqlite3
import time
import pandas as pd
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, RedirectResponse

DB = "jlpt.db"
DECK_FOLDER = "decks"
SESSION_TIMEOUT = 3600  # 1시간 미접속 시 초기화

app = FastAPI()


# ---------------------------
# DB 초기화
# ---------------------------
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS session (
        id INTEGER PRIMARY KEY,
        deck TEXT,
        round INTEGER,
        active_memory TEXT,
        last_access REAL
    )
    """)

    c.execute("CREATE TABLE IF NOT EXISTS memory_a (word_id INTEGER)")
    c.execute("CREATE TABLE IF NOT EXISTS memory_b (word_id INTEGER)")

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


def reset_session():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("DELETE FROM session")
    c.execute("DELETE FROM memory_a")
    c.execute("DELETE FROM memory_b")
    conn.commit()
    conn.close()


def check_timeout():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT last_access FROM session LIMIT 1")
    row = c.fetchone()
    if row and time.time() - row[0] > SESSION_TIMEOUT:
        reset_session()
    conn.close()


# ---------------------------
# A단계 : 덱 선택
# ---------------------------
@app.get("/", response_class=HTMLResponse)
def deck_select():
    check_timeout()
    decks = [f for f in os.listdir(DECK_FOLDER) if f.endswith(".xlsx")]

    html = "<h2>덱 선택</h2>"
    for deck in decks:
        html += f'<a href="/start/{deck}"><button>{deck}</button></a><br><br>'
    return html


@app.get("/start/{deck}")
def start_deck(deck: str):
    reset_session()

    path = os.path.join(DECK_FOLDER, deck)
    if not os.path.exists(path):
        return RedirectResponse("/", status_code=302)

    df = pd.read_excel(path)

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("DELETE FROM words")

    for _, row in df.iterrows():
        c.execute("INSERT INTO words VALUES (?, ?, ?, ?, ?, ?)",
                  (int(row["id"]), deck,
                   row["front"], row["back"],
                   row["explanation"], row["example"]))
        c.execute("INSERT INTO memory_a VALUES (?)", (int(row["id"]),))

    c.execute("INSERT INTO session VALUES (1, ?, 1, 'A', ?)",
              (deck, time.time()))

    conn.commit()
    conn.close()

    return RedirectResponse("/study", status_code=302)


# ---------------------------
# B단계 : 학습 진행
# ---------------------------
@app.get("/study", response_class=HTMLResponse)
def study():
    check_timeout()
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("SELECT deck, round, active_memory FROM session LIMIT 1")
    session = c.fetchone()

    if not session:
        conn.close()
        return RedirectResponse("/", status_code=302)

    deck, round_num, active = session
    table = "memory_a" if active == "A" else "memory_b"

    c.execute(f"SELECT word_id FROM {table}")
    ids = c.fetchall()

    if not ids:
        other = "memory_b" if active == "A" else "memory_a"
        c.execute(f"SELECT word_id FROM {other}")
        other_ids = c.fetchall()

        if not other_ids:
            conn.close()
            return RedirectResponse("/complete", status_code=302)

        new_active = "B" if active == "A" else "A"
        c.execute("UPDATE session SET active_memory=?, round=?, last_access=?",
                  (new_active, round_num + 1, time.time()))
        conn.commit()
        conn.close()
        return RedirectResponse("/study", status_code=302)

    word_id = random.choice(ids)[0]

    # 호출 즉시 삭제
    c.execute(f"DELETE FROM {table} WHERE word_id=?", (word_id,))
    c.execute("SELECT front FROM words WHERE id=?", (word_id,))
    front = c.fetchone()[0]

    c.execute("UPDATE session SET last_access=?", (time.time(),))
    conn.commit()
    conn.close()

    html = f"""
    <h3>{deck}</h3>
    <h4>{round_num}회차</h4>
    <p style="font-size:30px;">{front}</p>

    <a href="/answer/{word_id}"><button>정답보기</button></a>
    <a href="/known"><button>알고있음</button></a>
    <a href="/retry/{word_id}"><button>다시공부하기</button></a>
    <a href="/"><button>덱 선택화면으로</button></a>
    """

    return html


@app.get("/answer/{word_id}", response_class=HTMLResponse)
def show_answer(word_id: int):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT back, explanation, example FROM words WHERE id=?", (word_id,))
    row = c.fetchone()
    conn.close()

    if not row:
        return RedirectResponse("/study", status_code=302)

    back, exl, exm = row

    html = f"""
    <p><b>{back}</b></p>
    <p>{exl}</p>
    <p>{exm}</p>
    <a href="/study"><button>돌아가기</button></a>
    """

    return html


@app.get("/retry/{word_id}")
def retry(word_id: int):
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("SELECT active_memory FROM session LIMIT 1")
    active = c.fetchone()[0]
    target = "memory_b" if active == "A" else "memory_a"

    c.execute(f"INSERT INTO {target} VALUES (?)", (word_id,))
    conn.commit()
    conn.close()

    return RedirectResponse("/study", status_code=302)


@app.get("/known")
def known():
    return RedirectResponse("/study", status_code=302)


# ---------------------------
# C단계 : 완료
# ---------------------------
@app.get("/complete", response_class=HTMLResponse)
def complete():
    reset_session()
    return """
    <h2>학습완료</h2>
    <a href="/"><button>덱 선택화면으로</button></a>
    """


init_db()

