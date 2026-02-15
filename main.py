from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
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

@app.get("/study/{deck_name}", response_class=HTMLResponse)
def study(request: Request, deck_name: str):
    file_path = os.path.join(DECK_FOLDER, deck_name)
    df = pd.read_excel(file_path)

    cards = df.to_dict(orient="records")
    random.shuffle(cards)

    request.session["cards"] = cards
    request.session["wrong"] = []
    request.session["current"] = 0

    return RedirectResponse(url="/card")

@app.get("/card", response_class=HTMLResponse)
def card(request: Request):
    cards = request.session.get("cards", [])
    current = request.session.get("current", 0)

    if current >= len(cards):
        wrong = request.session.get("wrong", [])
        if not wrong:
            return templates.TemplateResponse("complete.html", {
                "request": request
            })
        request.session["cards"] = wrong
        request.session["wrong"] = []
        request.session["current"] = 0
        return RedirectResponse(url="/card")

    card = cards[current]
    return templates.TemplateResponse("card.html", {
        "request": request,
        "card": card,
        "show_answer": False
    })

@app.post("/answer")
def answer(request: Request, remembered: str = Form(...)):
    cards = request.session.get("cards", [])
    current = request.session.get("current", 0)

    if remembered == "no":
        request.session["wrong"].append(cards[current])

    request.session["current"] = current + 1
    return RedirectResponse(url="/card", status_code=303)

