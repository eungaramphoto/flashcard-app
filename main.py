from flask import Flask, request, render_template_string
import os
import pandas as pd
import random

app = Flask(__name__)

DECK_FOLDER = "decks"

# 메인 화면: 덱 선택
@app.route("/")
def index():
    deck_files = [f for f in os.listdir(DECK_FOLDER) if f.endswith(".xlsx")]
    buttons = "".join([f'<form method="get" action="/deck/{f}"><button type="submit">{f}</button></form>' for f in deck_files])
    return f"<h1>덱 선택</h1>{buttons}"

# 단어 학습 화면
@app.route("/deck/<deck_name>")
def deck_page(deck_name):
    deck_path = os.path.join(DECK_FOLDER, deck_name)
    df = pd.read_excel(deck_path).dropna(subset=["front", "back"])
    # 현재 세션에서 사용중인 단어 인덱스 리스트 가져오기
    used = request.args.get("used", "")
    try:
        used_list = [int(i) for i in used.split(",") if i.strip().isdigit()]
    except:
        used_list = []

    # 다시 공부할 단어 리스트 가져오기
    unknown = request.args.get("unknown", "")
    try:
        unknown_list = [int(i) for i in unknown.split(",") if i.strip().isdigit()]
    except:
        unknown_list = []

    # 랜덤으로 다음 단어 선택
    available_indices = [i for i in range(len(df)) if i not in used_list]
    if not available_indices and unknown_list:
        available_indices = unknown_list
        unknown_list = []

    if not available_indices:
        # 모든 단어 학습 완료 -> 피니시 화면
        deck_files = [f for f in os.listdir(DECK_FOLDER) if f.endswith(".xlsx")]
        buttons = "".join([f'<form method="get" action="/deck/{f}"><button type="submit">{f}</button></form>' for f in deck_files])
        return f"<h1>Finished!</h1>{buttons}"

    current_idx = random.choice(available_indices)
    front = df.iloc[current_idx]["front"]
    back = df.iloc[current_idx]["back"]
    explanation = df.iloc[current_idx].get("explanation", "")
    example = df.iloc[current_idx].get("example", "")

    # query string용 used_list, unknown_list 문자열로
    new_used = ",".join(map(str, used_list + [current_idx]))
    unknown_str = ",".join(map(str, unknown_list))

    html = f"""
    <h1>{front}</h1>
    <form method="get">
        <input type="hidden" name="used" value="{new_used}">
        <input type="hidden" name="unknown" value="{unknown_str}">
        <button name="show" value="1">정답보기</button>
        <button name="know" value="1">알고있음</button>
        <button name="review" value="1">다시 공부하기</button>
    </form>
    """
    # 정답보기 눌렀으면 아래 표시
    show = request.args.get("show")
    if show:
        html += f"<hr><b>정답:</b> {back}<br><b>설명:</b> {explanation}<br><b>예문:</b> {example}<br>"

    # 알고있음 눌렀으면 바로 다음 단어로
    if request.args.get("know"):
        return f'<meta http-equiv="refresh" content="0; url=/deck/{deck_name}?used={new_used}&unknown={unknown_str}">'

    # 다시 공부하기 눌렀으면 unknown_list에 추가
    if request.args.get("review"):
        unknown_list.append(current_idx)
        unknown_str = ",".join(map(str, unknown_list))
        return f'<meta http-equiv="refresh" content="0; url=/deck/{deck_name}?used={new_used}&unknown={unknown_str}">'

    return html

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

