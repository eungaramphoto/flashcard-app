from flask import Flask, request, redirect, url_for, render_template_string
import pandas as pd
import os
import random
import urllib.parse

app = Flask(__name__)

DECK_FOLDER = "decks"

# 메인 화면: 덱 선택
@app.route("/")
def index():
    decks = [f for f in os.listdir(DECK_FOLDER) if f.endswith(".xlsx")]
    html = "<h1>덱 선택</h1>"
    for d in decks:
        html += f'<form style="margin:5px;" action="/deck/{urllib.parse.quote(d)}" method="get">'
        html += f'<button type="submit">{d}</button></form>'
    return html

# 덱 단어 학습 화면
@app.route("/deck/<deck_file>")
def deck_page(deck_file):
    path = os.path.join(DECK_FOLDER, deck_file)
    df = pd.read_excel(path)
    df = df.dropna(subset=["front", "back"])

    # 쿼리 파라미터 처리
    current = int(request.args.get("current", 0))
    used = request.args.get("used", "")
    again = request.args.get("again", "")

    # used 리스트 안전 처리
    if used and used != "[]":
        used_list = [int(i) for i in used.split(",")]
    else:
        used_list = []

    if again and again != "[]":
        again_list = [int(i) for i in again.split(",")]
    else:
        again_list = []

    # 학습 리스트
    all_indexes = list(range(len(df)))
    remaining = [i for i in all_indexes if i not in used_list]

    # 모든 단어 끝났으면 다시 공부할 단어 리스트
    if not remaining and again_list:
        remaining = again_list
        used_list = []
        again_list = []

    # 종료 조건
    if not remaining:
        html = "<h1>Finished!</h1>"
        html += '<form action="/" method="get"><button type="submit">덱 선택</button></form>'
        return html

    idx = remaining[0]
    word = df.iloc[idx]

    # HTML 템플릿
    html = f"<h2>{word['front']}</h2>"
    html += f'<form style="display:inline;" action="/deck/{urllib.parse.quote(deck_file)}" method="get">'
    html += f'<input type="hidden" name="current" value="{idx}">'
    html += f'<input type="hidden" name="used" value="{".".join(map(str, used_list))}">'
    html += f'<input type="hidden" name="again" value="{".".join(map(str, again_list))}">'
    html += f'<button type="submit" name="show" value="1">정답 보기</button></form>'

    html += f'<form style="display:inline;" action="/deck/{urllib.parse.quote(deck_file)}" method="get">'
    html += f'<input type="hidden" name="current" value="{idx}">'
    html += f'<input type="hidden" name="used" value="{".".join(map(str, used_list + [idx]))}">'
    html += f'<input type="hidden" name="again" value="{".".join(map(str, again_list))}">'
    html += f'<button type="submit">알고있음</button></form>'

    html += f'<form style="display:inline;" action="/deck/{urllib.parse.quote(deck_file)}" method="get">'
    html += f'<input type="hidden" name="current" value="{idx}">'
    html += f'<input type="hidden" name="used" value="{".".join(map(str, used_list + [idx]))}">'
    html += f'<input type="hidden" name="again" value="{".".join(map(str, again_list + [idx]))}">'
    html += f'<button type="submit">다시 공부하기</button></form>'

    # 정답보기
    show = request.args.get("show")
    if show == "1":
        html += f"<p><b>{word['back']}</b></p>"
        if "explanation" in word:
            html += f"<p>{word['explanation']}</p>"
        if "example" in word:
            html += f"<p>{word['example']}</p>"

    return html

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)

