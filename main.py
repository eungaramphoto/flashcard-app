from fastapi import FastAPI, Request, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
import pandas as pd
import os
import random
from natsort import natsorted

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="super-secret-key")
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

DECK_FOLDER = "decks"

def get_deck_tree():
    def build_tree(current_path):
        tree = {}

        for item in sorted(os.listdir(current_path)):
            full_path = os.path.join(current_path, item)

            # 폴더면 재귀
            if os.path.isdir(full_path):
                tree[item] = build_tree(full_path)

            # 엑셀 파일만 포함
            elif item.lower().endswith(".xlsx"):
                tree[item] = None

        return tree

    return build_tree(DECK_FOLDER)



@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    tree = get_deck_tree()
    return templates.TemplateResponse("home.html", {
        "request": request,
        "tree": tree
    })



@app.get("/study/{deck_path:path}")
def study(request: Request, deck_path: str):

    # 실제 파일 경로 구성
    file_path = os.path.join(DECK_FOLDER, deck_path)

    # 파일 존재 확인
    if not os.path.exists(file_path):
        return HTMLResponse(f"<h2>파일을 찾을 수 없습니다:<br>{file_path}</h2>", status_code=404)

    df = pd.read_excel(file_path)
    total_count = len(df)

    request.session["deck_path"] = deck_path
    
    # 🔹 파일명(확장자 제거) 저장
    file_name = os.path.splitext(os.path.basename(deck_path))[0]
    request.session["file_name"] = file_name
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

    deck_path = request.session.get("deck_path")
    if not deck_path:
        return RedirectResponse(url="/")

    file_path = os.path.join(DECK_FOLDER, deck_path)

    # 파일 존재 확인
    if not os.path.exists(file_path):
        return HTMLResponse(f"<h2>파일을 찾을 수 없습니다:<br>{file_path}</h2>", status_code=404)

    df = pd.read_excel(file_path)

    active_indexes = request.session.get("active_indexes", [])
    current = request.session.get("current", 0)
    round_number = request.session.get("round", 1)

    remember_count = request.session.get("remember_count", 0)
    forget_count = request.session.get("forget_count", 0)

    # 🔹 회차 종료 처리
    if current >= len(active_indexes):

        wrong_indexes = request.session.get("wrong_indexes", [])

        # 모든 단어 완료
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

        # 🔹 회차별 카운트 초기화
        request.session["remember_count"] = 0
        request.session["forget_count"] = 0

        return templates.TemplateResponse("round_change.html", {
            "request": request,
            "round": round_number + 1
        })

    # 🔹 현재 카드 출력
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
        "forget_count": forget_count,
        "file_name": request.session.get("file_name", "")
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

