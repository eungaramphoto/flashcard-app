from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
import pandas as pd
import os
import random
from natsort import natsorted

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="super-secret-key")
templates = Jinja2Templates(directory="templates")

DECK_FOLDER = "decks"


def get_deck_list():
    files = [f for f in os.listdir(DECK_FOLDER) if f.endswith(".xlsx")]
    return natsorted(files)


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    decks = get_deck_list()
    return templates.TemplateResponse("home.html", {
        "request": request,
        "decks": decks
    })


@app.get("/study/{deck_name}")
def study(request: Request, deck_name: str):
    file_path = os.path.join(DECK_FOLDER, deck_name)
    df = pd.read_excel(file_path)
    total_count = len(df)

    request.session["deck"] = deck_name
    request.session["total_count"] = total_count
    request.session["round"] = 1
    request.session["current"] = 0

    indexes = list(range(total_count))
    random.shuffle(indexes)

    request.session["active_indexes"] = indexes
    request.session["wrong_indexes"] = []

    request.session["remember_count"] = 0
    request.session["forget_count"] = 0

    return RedirectResponse(url="/card")


@app.get("/card", response_class=HTMLResponse)
def card(request: Request):
    deck_name = request.session.get("deck")
    if not deck_name:
        return RedirectResponse(url="/")

    file_path = os.path.join(DECK_FOLDER, deck_name)
    df = pd.read_excel(file_path)

    active_indexes = request.session.get("active_indexes", [])
    current = request.session.get("current", 0)
    round_number = request.session.get("round", 1)
    total_count = request.session.get("total_count", 0)

    remember_count = request.session.get("remember_count", 0)
    forget_count = request.session.get("forget_count", 0)

    # 🔹 회차 종료 처리
    if current >= len(active_indexes):

        wrong_indexes = request.session.get("wrong_indexes", [])

        if not wrong_indexes:
            return templates.TemplateResponse("complete.html", {
                "request": request,
                "remember_count": remember_count,
                "forget_count": forget_count
            })

        # 다음 회차 준비
        request.session["active_indexes"] = wrong_indexes
        request.session["wrong_indexes"] = []
        request.session["current"] = 0
        request.session["round"] = round_number + 1

        return templates.TemplateResponse("round_change.html", {
            "request": request,
            "round": round_number + 1
        })

    # 🔹 현재 카드
    index = active_indexes[current]
    card_data = df.iloc[index].to_dict()

    progress_total = len(active_indexes)
    progress_percent = int((current / progress_total) * 100)

    return templates.TemplateResponse("card.html", {
        "request": request,
        "card": card_data,
        "round": round_number,
        "current": current + 1,
        "total": progress_total,
        "percent": progress_percent,
        "remember_count": remember_count,
        "forget_count": forget_count
    })


@app.post("/answer")
def answer(request: Request, remembered: str = Form(...)):
    active_indexes = request.session.get("active_indexes", [])
    current = request.session.get("current", 0)
    wrong_indexes = request.session.get("wrong_indexes", [])

    remember_count = request.session.get("remember_count", 0)
    forget_count = request.session.get("forget_count", 0)

    if remembered == "yes":
        remember_count += 1
    else:
        forget_count += 1
        wrong_indexes.append(active_indexes[current])

    request.session["remember_count"] = remember_count
    request.session["forget_count"] = forget_count
    request.session["wrong_indexes"] = wrong_indexes
    request.session["current"] = current + 1

    return RedirectResponse(url="/card", status_code=303)



@app.get("/round-change", response_class=HTMLResponse)
def round_change(request: Request):
    return templates.TemplateResponse("round_change.html", {
        "request": request,
        "round": request.session.get("round")
    })

@app.get("/reset")
def reset(request: Request):
    request.session.clear()
    return RedirectResponse(url="/")

