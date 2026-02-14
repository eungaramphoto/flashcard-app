from flask import Flask, request, redirect, render_template_string
import os
import pandas as pd
import random

app = Flask(__name__)
DECK_FOLDER = "decks"

# 덱 선택 화면
@app.route("/")
def index():
    decks = [f for f in os.listdir(DECK_FOLDER) if f.endswith(".xlsx")]
    return render_template_string("""
    <html>
    <head>
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <style>
        body { font-family: Arial; text-align: center; margin-top: 50px; }
        button { display: block; margin: 10px auto; padding: 12px 25px; font-size: 18px; }
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

# 단어 학습 화면
@app.route("/deck/<deck_name>")
def deck_page(deck_name):
    path = os.path.join(DECK_FOLDER, deck_name)
    df = pd.read_excel(path)
    df = df.dropna(subset=["front", "back"])
    words = df.to_dict(orient="records")

    # URL 파라미터 가져오기
    used = request.args.get("used", "")
    again = request.args.get("again", "")
    round_num = int(request.args.get("round", "1"))
    show = request.args.get("show")
    current = request.args.get("current")

    # 안전한 리스트 변환
    def parse_list(param):
        try:
            return [int(i) for i in param.split(",") if i.strip().isdigit()]
        except:
            return []

    used_list = parse_list(used)
    again_list = parse_list(again)
    total_indices = list(range(len(words)))

    # remaining 계산
    if again_list and round_num > 1:
        remaining = [i for i in again_list if i not in used_list]
    else:
        remaining = [i for i in total_indices if i not in used_list]

    # remaining이 비면 다음 회독 또는 피니시
    if not remaining:
        if again_list:
            # 다음 회독 시작
            remaining = again_list
            used_list = []
            again_list = []
            round_num += 1
        else:
            # 피니시 화면
            return render_template_string("""
            <html>
            <head>
              <meta name="viewport" content="width=device-width, initial-scale=1.0">
              <style>
                body { font-family: Arial; text-align: center; margin-top: 50px; font-size: 24px; }
                button { display: block; margin: 10px auto; padding: 12px 25px; font-size: 18px; }
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

    # 현재 단어 선택
    if current and current.isdigit():
        idx = int(current)
    else:
        idx = random.choice(remaining)

    card = words[idx]

    # used/again 문자열
    new_used = used_list if show else used_list + [idx]
    used_str = ",".join(map(str, new_used))
    again_str = ",".join(map(str, again_list))

    # HTML 구조: 카드 + 정답/해설/예문 → 버튼 위쪽
    return render_template_string("""
    <html>
    <head>
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <style>
        body { font-family: Arial; text-align:center; padding:30px; }
        h2 { font-size: 28px; margin-bottom: 30px; }
        .card { font-size: 32px; margin: 20px auto; }
        .answer { font-size: 22px; margin-top: 15px; }
        .example { font-size: 16px; max-width: 700px; margin: 15px auto; text-align:center; }
        button { display:block; font-size:20px; padding:14px 20px; margin:10px auto; width:80%; max-width:350px; }
      </style>
    </head>
    <body>
      <h2>{{deck_name}} ({{round_num}}회독)</h2>

      <div class="card">{{card["front"]}}</div>

      {% if show %}
        <div class="answer"><b>{{card["back"]}}</b></div>
        {% if card.get("explanation") %}<div class="answer">{{card["explanation"]}}</div>{% endif %}
        {% if card.get("example") %}<div class="example">{{card["example"]}}</div>{% endif %}
      {% endif %}

      <form method="get" action="/deck/{{deck_name}}">
        <input type="hidden" name="used" value="{{used_str}}">
        <input type="hidden" name="again" value="{{again_str}}">
        <input type="hidden" name="current" value="{{idx}}">
        <input type="hidden" name="round" value="{{round_num}}">
        <button name="show" value="1">정답 보기</button>
      </form>

      <form method="get" action="/deck/{{deck_name}}">
        <input type="hidden" name="used" value="{{used_str}}">
        <input type="hidden" name="again" value="{{again_str}}">
        <input type="hidden" name="current" value="{{idx}}">
        <input type="hidden" name="round" value="{{round_num}}">
        <button name="know" value="1">알고있음</button>
      </form>

      <form method="get" action="/deck/{{deck_name}}">
        <input type="hidden" name="used" value="{{used_str}}">
        <input type="hidden" name="again" value="{{again_str}},{{idx}}">
        <input type="hidden" name="current" value="{{idx}}">
        <input type="hidden" name="round" value="{{round_num}}">
        <button name="review" value="1">다시 공부하기</button>
      </form>

      <form method="get" action="/">
        <button>덱 선택</button>
      </form>

    </body>
    </html>
    """, deck_name=deck_name, card=card,
       used_str=used_str, again_str=again_str, idx=idx,
       round_num=round_num, show=show)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

