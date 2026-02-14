from flask import Flask, request, redirect, render_template_string
import os
import pandas as pd
import random

app = Flask(__name__)
DECK_FOLDER = "decks"

@app.route("/")
def index():
    decks = [f for f in os.listdir(DECK_FOLDER) if f.endswith(".xlsx")]
    return render_template_string("""
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { font-family: Arial, sans-serif; text-align:center; margin:50px auto; }
            h1 { font-size:28px; margin-bottom:30px; }
            button { font-size:20px; padding:15px 30px; margin:12px auto; display:block; max-width:300px; width:80%; border-radius:6px; }
        </style>
    </head>
    <body>
        <h1>덱 선택</h1>
        {% for deck in decks %}
            <form method="get" action="/deck/{{deck}}">
                <button type="submit">{{deck}}</button>
            </form>
        {% endfor %}
    </body>
    </html>
    """, decks=decks)

@app.route("/deck/<deck_name>")
def deck_page(deck_name):
    path = os.path.join(DECK_FOLDER, deck_name)
    df = pd.read_excel(path).dropna(subset=["front","back"])
    words = df.to_dict(orient="records")

    used = request.args.get("used","")
    show = request.args.get("show")
    current = request.args.get("current")

    def parse_list(param):
        try:
            return [int(i) for i in param.split(",") if i.strip().isdigit()]
        except:
            return []

    used_list = parse_list(used)
    total_indices = list(range(len(words)))
    remaining = [i for i in total_indices if i not in used_list]

    if not remaining:
        return render_template_string("""
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body { font-family: Arial, sans-serif; text-align:center; margin-top:50px; font-size:24px; }
                button { font-size:20px; padding:15px 30px; margin:12px auto; display:block; max-width:300px; width:80%; border-radius:6px; }
            </style>
        </head>
        <body>
            <h2>Finished!</h2>
            <form method="get" action="/">
                <button type="submit">덱 선택으로 돌아가기</button>
            </form>
        </body>
        </html>
        """)

    if current and current.isdigit():
        idx = int(current)
    else:
        idx = random.choice(remaining)

    card = words[idx]
    new_used_list = used_list if show else used_list + [idx]
    used_str = ",".join(map(str,new_used_list))

    return render_template_string("""
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { font-family: Arial, sans-serif; text-align:center; padding:30px; }
            h2 { font-size:28px; margin-bottom:30px; }
            .card { font-size:32px; font-weight:bold; margin:25px auto; }
            .answer { font-size:22px; margin-top:20px; }
            .example { font-size:18px; max-width:700px; margin:15px auto; text-align:center; }
            button { display:block; font-size:20px; padding:15px 25px; margin:12px auto; width:80%; max-width:300px; border-radius:6px; }
        </style>
    </head>
    <body>
        <h2>{{deck_name}}</h2>

        <div class="card">{{card["front"]}}</div>

        {% if show %}
            <div class="answer"><b>{{card["back"]}}</b></div>
            {% if card.get("explanation") %}<div class="answer">{{card["explanation"]}}</div>{% endif %}
            {% if card.get("example") %}<div class="example">{{card["example"]}}</div>{% endif %}
        {% endif %}

        <!-- 정답보기 -->
        <form method="get" action="/deck/{{deck_name}}">
            <input type="hidden" name="used" value="{{used_str}}">
            <input type="hidden" name="current" value="{{idx}}">
            <button name="show" value="1">정답 보기</button>
        </form>

        <!-- 다음 문제 -->
        <form method="get" action="/deck/{{deck_name}}">
            <input type="hidden" name="used" value="{{used_str}}">
            <button>다음 문제</button>
        </form>

        <!-- 덱 선택 -->
        <form method="get" action="/">
            <button>덱 선택</button>
        </form>

    </body>
    </html>
    """, deck_name=deck_name, card=card, used_str=used_str, idx=idx, show=show)

# 피니시 화면
@app.route("/finish")
def finish_page():
    deck_name = request.args.get("deck","")
    return render_template_string("""
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { font-family: Arial, sans-serif; text-align:center; margin-top:50px; font-size:24px; }
            button { font-size:20px; padding:15px 30px; margin:12px auto; display:block; max-width:300px; width:80%; border-radius:6px; }
        </style>
    </head>
    <body>
        <h2>Finished!</h2>
        <form method="get" action="/">
            <button type="submit">덱 선택으로 돌아가기</button>
        </form>
    </body>
    </html>
    """)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

