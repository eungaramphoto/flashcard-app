from flask import Flask, request, redirect
from flask import render_template_string
import pandas as pd
import os
import random

app = Flask(__name__)

DECK_FOLDER = "decks"

# 덱 목록 페이지
@app.route("/")
def index():
    deck_files = [f for f in os.listdir(DECK_FOLDER) if f.endswith(".xlsx")]
    return render_template_string("""
    <html>
    <head>
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <style>
        body { font-family: Arial; text-align: center; margin-top: 50px; }
        button { display: block; margin: 10px auto; padding: 10px 20px; font-size: 16px; }
      </style>
    </head>
    <body>
      <h2>덱 선택</h2>
      {% for deck in deck_files %}
        <form method="get" action="/deck/{{deck}}">
          <button type="submit">{{deck}}</button>
        </form>
      {% endfor %}
    </body>
    </html>
    """, deck_files=deck_files)

# 덱 페이지 초기화
@app.route("/deck/<deck_name>")
def deck_page(deck_name):
    df = pd.read_excel(os.path.join(DECK_FOLDER, deck_name))
    df = df.dropna(subset=["front", "back"])
    words = df.to_dict(orient="records")
    used = request.args.get("used", "")
    unknown = request.args.get("unknown", "")
    current = request.args.get("current", "0")
    round_num = request.args.get("round", "1")
    
    # 현재 단어 순서 결정
    if used:
        used_list = [int(i) for i in used.split(",")]
    else:
        used_list = []
    if unknown:
        unknown_list = [int(i) for i in unknown.split(",")]
    else:
        unknown_list = []

    total_words = list(range(len(words)))
    if current == "0":  # 첫 단어
        remaining = total_words
        random.shuffle(remaining)
        next_index = remaining[0]
    else:
        remaining = [i for i in total_words if i not in used_list]
        if not remaining:
            # 1회독 끝났으면 unknown_list로 2회독 시작
            if unknown_list:
                remaining = unknown_list
                round_num = str(int(round_num)+1)
                unknown_list = []
            else:
                return redirect(f"/finish?deck={deck_name}")
        random.shuffle(remaining)
        next_index = remaining[0]

    current_word = words[next_index]

    return render_template_string("""
    <html>
    <head>
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <style>
        body { font-family: Arial; text-align: center; margin-top: 50px; }
        .card { font-size: 24px; margin: 20px; }
        .example { font-size: 18px; color: gray; }
        button { display: block; margin: 10px auto; padding: 10px 20px; font-size: 16px; }
      </style>
    </head>
    <body>
      <h3>{{deck_name}} - {{round_num}}회독</h3>
      <div class="card">{{current_word["front"]}}</div>

      <form method="get" action="/deck/{{deck_name}}">
        <input type="hidden" name="used" value="{{used_list + [next_index] | join(',')}}">
        <input type="hidden" name="unknown" value="{{unknown_list}}">
        <input type="hidden" name="current" value="{{next_index}}">
        <input type="hidden" name="round" value="{{round_num}}">
        <button type="submit" name="show" value="1">정답보기</button>
      </form>

      <form method="get" action="/deck/{{deck_name}}">
        <input type="hidden" name="used" value="{{used_list + [next_index] | join(',')}}">
        <input type="hidden" name="unknown" value="{{unknown_list}}">
        <input type="hidden" name="current" value="{{next_index}}">
        <input type="hidden" name="round" value="{{round_num}}">
        <button type="submit" name="know" value="1">알고있음</button>
      </form>

      <form method="get" action="/deck/{{deck_name}}">
        <input type="hidden" name="used" value="{{used_list + [next_index] | join(',')}}">
        <input type="hidden" name="unknown" value="{{unknown_list + [next_index] | join(',')}}">
        <input type="hidden" name="current" value="{{next_index}}">
        <input type="hidden" name="round" value="{{round_num}}">
        <button type="submit" name="review" value="1">다시 공부하기</button>
      </form>

      {% if request.args.get('show') %}
        <div class="card">{{current_word["back"]}}</div>
        {% if "explanation" in current_word %}<div class="example">{{current_word["explanation"]}}</div>{% endif %}
        {% if "example" in current_word %}<div class="example">{{current_word["example"]}}</div>{% endif %}
      {% endif %}

    </body>
    </html>
    """, deck_name=deck_name, current_word=current_word,
       used_list=used_list, unknown_list=unknown_list,
       next_index=next_index, round_num=round_num, request=request)

@app.route("/finish")
def finish_page():
    deck_name = request.args.get("deck", "")
    return render_template_string("""
    <html>
    <head>
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <style>
        body { font-family: Arial; text-align: center; margin-top: 50px; font-size: 24px; }
        button { display: block; margin: 10px auto; padding: 10px 20px; font-size: 16px; }
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

