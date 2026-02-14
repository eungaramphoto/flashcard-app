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
    df = pd.read_excel(path).dropna(subset=["front","back"])
    words = df.to_dict(orient="records")

    # URL 파라미터
    used = request.args.get("used", "")
    next_round = request.args.get("next_round", "")
    round_num = int(request.args.get("round", "1"))
    show = request.args.get("show")
    action = request.args.get("action")
    current = request.args.get("current")

    # 안전 리스트 변환
    def parse_list(param):
        try:
            return [int(i) for i in param.split(",") if i.strip().isdigit()]
        except:
            return []

    used_list = parse_list(used)
    next_round_list = parse_list(next_round)
    total_indices = list(range(len(words)))

    # 첫 카드 선택 시 remaining 계산
    if not current or not current.isdigit():
        if round_num == 1:
            current_round_words = [i for i in total_indices if i not in used_list]
        else:
            current_round_words = [i for i in next_round_list if i not in used_list]
        if not current_round_words:
            if next_round_list:
                # 다음 회독 시작
                current_round_words = next_round_list
                used_list = []
                next_round_list = []
                round_num += 1
            else:
                # 피니시
                return redirect(f"/finish?deck={deck_name}")
        idx = random.choice(current_round_words)
    else:
        idx = int(current)

    card = words[idx]

    # 버튼 클릭 처리
    if action == "know":
        used_list.append(idx)
    elif action == "review":
        if idx not in next_round_list:
            next_round_list.append(idx)
        used_list.append(idx)
    else:
        # 정답보기 클릭
        pass

    # 다음 단어를 위해 remaining 계산
    if action in ["know","review","show"]:
        current_round_words = [i for i in (next_round_list if round_num>1 and next_round_list else total_indices) if i not in used_list]
        if current_round_words:
            next_idx = random.choice(current_round_words)
        else:
            # 회독 종료
            if next_round_list:
                next_idx = random.choice(next_round_list)
                used_list = []
                next_round_list = []
                round_num += 1
            else:
                return redirect(f"/finish?deck={deck_name}")
    else:
        next_idx = idx

    # URL 문자열
    used_str = ",".join(map(str, used_list))
    next_round_str = ",".join(map(str, next_round_list))

    return render_template_string("""
    <html>
    <head>
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <style>
        body { font-family: Arial; text-align:center; padding:30px; }
        h2 { font-size:28px; margin-bottom:30px; }
        .card { font-size:32px; margin:20px auto; }
        .answer { font-size:22px; margin-top:15px; }
        .example { font-size:16px; max-width:700px; margin:15px auto; text-align:center; }
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

      <!-- 정답보기 -->
      <form method="get" action="/deck/{{deck_name}}">
        <input type="hidden" name="used" value="{{used_str}}">
        <input type="hidden" name="next_round" value="{{next_round_str}}">
        <input type="hidden" name="current" value="{{next_idx}}">
        <input type="hidden" name="round" value="{{round_num}}">
        <button name="action" value="show">정답 보기</button>
      </form>

      <!-- 알고있음 -->
      <form method="get" action="/deck/{{deck_name}}">
        <input type="hidden" name="used" value="{{used_str}}">
        <input type="hidden" name="next_round" value="{{next_round_str}}">
        <input type="hidden" name="current" value="{{next_idx}}">
        <input type="hidden" name="round" value="{{round_num}}">
        <button name="action" value="know">알고있음</button>
      </form>

      <!-- 다시 공부하기 -->
      <form method="get" action="/deck/{{deck_name}}">
        <input type="hidden" name="used" value="{{used_str}}">
        <input type="hidden" name="next_round" value="{{next_round_str}}">
        <input type="hidden" name="current" value="{{next_idx}}">
        <input type="hidden" name="round" value="{{round_num}}">
        <button name="action" value="review">다시 공부하기</button>
      </form>

      <!-- 덱 선택 -->
      <form method="get" action="/">
        <button>덱 선택</button>
      </form>

    </body>
    </html>
    """, deck_name=deck_name, card=card,
       used_str=used_str, next_round_str=next_round_str,
       next_idx=next_idx, round_num=round_num, show=show)

# 피니시 화면
@app.route("/finish")
def finish_page():
    deck_name = request.args.get("deck","")
    return render_template_string("""
    <html>
    <head>
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <style>
        body { font-family: Arial; text-align:center; margin-top:50px; font-size:24px; }
        button { display:block; margin:10px auto; padding:12px 25px; font-size:18px; }
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

