from flask import Flask, render_template_string, request
import pandas as pd
import os
import random

app = Flask(__name__)
DECK_FOLDER = "decks"

def get_deck_list():
    return [f for f in os.listdir(DECK_FOLDER) if f.endswith(".xlsx")]

def load_deck(deck_name):
    df = pd.read_excel(os.path.join(DECK_FOLDER, deck_name))
    df.columns = df.columns.str.strip()
    df = df.dropna(subset=["front", "back"])
    return df

@app.route("/")
def index():
    decks = get_deck_list()
    html = """
    <!doctype html>
    <html>
    <head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family:-apple-system, BlinkMacSystemFont, sans-serif; text-align:center; padding:30px 20px;}
        h2 { font-size:28px; margin-bottom:30px;}
        button { width:85%; max-width:400px; padding:16px; font-size:18px; margin:12px 0;}
    </style>
    </head>
    <body>
    <h2>덱 선택</h2>
    {% for deck in decks %}
        <div><a href="/deck/{{ deck }}"><button>{{ deck }}</button></a></div>
    {% endfor %}
    </body>
    </html>
    """
    return render_template_string(html, decks=decks)

@app.route("/deck/<deck_name>")
def deck_page(deck_name):
    df = load_deck(deck_name)

    # URL 파라미터
    used = request.args.get("used")
    unknown = request.args.get("unknown")
    current = request.args.get("current")
    show = request.args.get("show")
    repeat_mode = request.args.get("repeat")

    used_list = [int(i) for i in used.split(",")] if used else []
    unknown_list = [int(i) for i in unknown.split(",")] if unknown else []

    # 반복 모드: 다시 공부 리스트만
    if repeat_mode == "1":
        remaining = [i for i in unknown_list if i not in used_list]
    else:
        remaining = [i for i in df.index if i not in used_list]

    # 남은 카드 없으면 피니시 화면
    if not remaining:
        return render_template_string(finish_html, deck_name=deck_name, unknown=remaining if repeat_mode=="1" else unknown_list)

    # 남은 카드에서 current 선택
    current_index = int(current) if current else random.choice(remaining)
    card = df.loc[current_index]

    # used 업데이트
    new_used = used_list if show else used_list + [current_index]
    used_string = ",".join(str(i) for i in new_used)
    unknown_string = ",".join(str(i) for i in unknown_list)

    html = """
    <!doctype html>
    <html>
    <head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family:-apple-system, BlinkMacSystemFont, sans-serif; text-align:center; padding:20px; word-break:break-word;}
        .card { font-size:32px; margin-top:70px;}
        .answer { margin-top:30px;}
        .example { margin-top:20px; font-size:16px; max-width:700px; margin-left:auto; margin-right:auto; text-align:center;}
        button { width:85%; max-width:400px; padding:14px; font-size:16px; margin-top:20px;}
    </style>
    </head>
    <body>

    <h4>{{ deck_name }}</h4>

    <div class="card">{{ word }}</div>

    {% if show %}
    <div class="answer">
        <div style="font-size:22px;"><strong>{{ answer }}</strong></div>
        <div style="margin-top:10px; font-size:16px;">{{ explanation | replace('\\n','<br>') | safe }}</div>
        <div class="example">{{ example | replace('\\n','<br>') | safe }}</div>
    </div>
    {% endif %}

    <!-- 항상 4개 버튼 표시 -->
    <a href="/deck/{{ deck_name }}?current={{ current_index }}&used={{ used_string }}&unknown={{ unknown_string }}&show=1">
        <button>정답 보기</button>
    </a>

    <a href="/deck/{{ deck_name }}?current={{ current_index }}&used={{ new_used }}&unknown={{ unknown_string }}&repeat={{ repeat_mode | default(0) }}">
        <button>알고있음</button>
    </a>

    <a href="/deck/{{ deck_name }}?current={{ current_index }}&used={{ used_list }}&unknown={{ unknown_string }},{{ current_index }}&repeat={{ repeat_mode | default(0) }}">
        <button>다시 공부하기</button>
    </a>

    <a href="/"><button>덱 목록으로</button></a>

    </body>
    </html>
    """

    return render_template_string(
        html,
        word=card["front"],
        answer=card["back"],
        explanation=card.get("explanation", ""),
        example=card.get("example", ""),
        deck_name=deck_name,
        show=show,
        used_list=used_list,
        new_used=new_used,
        used_string=used_string,
        unknown_list=unknown_list,
        unknown_string=unknown_string,
        current_index=current_index,
        repeat_mode=repeat_mode
    )

# 피니시 화면
finish_html = """
<!doctype html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body { font-family:-apple-system, BlinkMacSystemFont, sans-serif; text-align:center; padding:60px 20px;}
h1 { font-size:32px; margin-bottom:30px;}
button { width:85%; max-width:400px; padding:16px; font-size:18px; margin-top:20px;}
</style>
</head>
<body>
<h1>Finished</h1>
<a href="/"><button>덱 목록으로</button></a>
</body>
</html>
"""

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

