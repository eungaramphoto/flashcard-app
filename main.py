from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
import pandas as pd
import os
import random

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="flashcard-secret-key")

templates = Jinja2Templates(directory="templates")

DECK_FOLDER = "decks"


# -------------------------------
# 1. 덱 목록 화면
# -------------------------------
@app.get("/")
def index(request: Request):

    if not os.path.exists(DECK_FOLDER):
        os.makedirs(DECK_FOLDER)

    files = sorted(
        [f.replace(".xlsx", "") for f in os.listdir(DECK_FOLDER) if f.endswith(".xlsx")]
    )

    return templates.TemplateResponse(
        "index.html",
        {"request": request, "decks": files}
    )


# -------------------------------
# 2. 학습 시작
# -------------------------------
@app.get("/start/{deck_name}")
def start(deck_name: str, request: Request):

    file_path = os.path.join(DECK_FOLDER, f"{deck_name}.xlsx")

    if not os.path.exists(file_path):
        return RedirectResponse("/", status_code=302)

    df = pd.read_excel(file_path)
    df = df.fillna("")

    # 필수 컬럼 확인
    required_columns = {"id", "front", "back", "explanation", "example"}
    if not required_columns.issubset(df.columns):
        return RedirectResponse("/", status_code=302)

    # ✅ id 비어있는 행 제거
    df = df[df["id"].notna()]
    df = df[df["id"] != ""]

    records = df.to_dict(orient="records")

    if len(records) == 0:
        return RedirectResponse("/", status_code=302)

    random.shuffle(records)

    request.session["deck"] = deck_name
    request.session["words"] = records
    request.session["index"] = 0
    request.session["show_answer"] = False

    return RedirectResponse("/study", status_code=302)


# -------------------------------
# 3. 학습 화면
# -------------------------------
@app.get("/study")
def study(request: Request):

    session = request.session

    if "words" not in session:
        return RedirectResponse("/", status_code=302)

    index = session["index"]
    words = session["words"]

    if index >= len(words):
        return RedirectResponse("/finished", status_code=302)

    word = words[index]

    return templates.TemplateResponse(
        "study.html",
        {
            "request": request,
            "deck": session["deck"],
            "word": word,
            "show_answer": session["show_answer"]
        }
    )


# -------------------------------
# 4. 정답보기
# -------------------------------
@app.get("/show")
def show(request: Request):

    if "words" not in request.session:
        return RedirectResponse("/", status_code=302)

    request.session["show_answer"] = True
    return RedirectResponse("/study", status_code=302)


# -------------------------------
# 5. 다음 단어
# -------------------------------
@app.get("/next")
def next_word(request: Request):

    if "words" not in request.session:
        return RedirectResponse("/", status_code=302)

    request.session["index"] += 1
    request.session["show_answer"] = False

    return RedirectResponse("/study", status_code=302)


# -------------------------------
# 6. 종료 화면
# -------------------------------
@app.get("/finished")
def finished(request: Request):

    request.session.clear()

    return templates.TemplateResponse(
        "finished.html",
        {"request": request}
    )

