from flask import Flask, request, render_template_string
import os
import pandas as pd
import random

app = Flask(__name__)

DECK_FOLDER = "decks"

# 메인 화면: 덱 선택
@app.route("/")
def index():
    decks = [f for f in os.listdir(DECK_FOLDER) if f.endswith(".xlsx")]
    html = """
    <!doctype html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family:-apple-system, BlinkMacSystemFont, sans-serif; text-align:center; padding:50px 20px; }
            h1 { font-size:32px; margin-bottom:30px; }
            .deck-button { font-size:22px; padding:15px 25px; margin:10px; display:block; width:250px; margin-left:auto; margin-right:auto; }
        </style>
    </head>
    <body>
        <h1>덱 선택</h1>
        {% for deck in decks %}
            <form action="/deck/{{deck}}" method="get">
                <button class="deck-button" type="submit">{{deck}}</button>
            </form>
        {% endfor %}
    </body>
    </html>
    """
    return render_template_string(html, decks=decks)

# 카드 학습 화면
@app.route("/deck/<deck_name>")
def deck_page(deck_name):
    # 엑셀 파일 로드
    path = os.path.join(DECK_FOLDER, deck_name)
    df = pd.read_excel(path).dropna(subset=["front","back"])

    # URL 파라미터 안전 처리
    used = request.args.get("used", "")
    unknown = request.args.get("unknown", "")
    current = request.args.get("current")
    show = request.args.get("show")
    repeat_mode = request.args.get("repeat")

    try:
        used_list = [int(i) for i in used.split(",") if i.strip().isdigit()]
    except:
        used_list = []

    try:
        unknown_list = [int(i) for i in unknown.split(",") if i.strip().isdigit()]
    except:
        unknown_list = []

    # 첫 재생 또는 반복 재생 리스트 결정
    all_indices = list(range(len(df)))
    if repeat_mode == "1":
        remaining = [i for i in unknown_list if i not in used_list]
    else:
        remaining = [i for i in all_indices if i not in used_list]

    if not remaining:
        # 첫 재생 후 다시 공부 리스트 반복
        if repeat_mode != "1" and unknown_list:
            remaining = unknown_list
            used_list = []
            unknown_list = []
        else:
            # 모든 단어 학습 완료 -> Finished 화면
            return render_template_string("""
                <!doctype html>
                <html>
                <head>
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <style>
                    body { font-family:-apple-system, BlinkMacSystemFont, sans-serif; text-align:center; padding:60px 20px; }
                    h1 { font-size:32px; margin-bottom:30px; }
                    button { font-size:18px; padding:16px 25px; margin-top:20px; width:85%; max-width:400px; }
                </style>
                </head>
                <body>
                    <h1>Finished!</h1>
                    <form action="/" method="get">
                        <button type="submit">덱 목록으로</button>
                    </form>
                </body>
                </html>
            """)

    # 현재 카드 결정
    if current and current.isdigit():
        idx = int(current)
    else:
        idx = random.choice(remaining)

    card = df.iloc[idx]

    # used/unknown 리스트 업데이트
    new_used = used_list if show else used_list + [idx]
    used_str = ",".join(map(str,new_used))
    unknown_str = ",".join(map(str,unknown_list))

    html = f"""
    <!doctype html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ font-family:-apple-system, BlinkMacSystemFont, sans-serif; text-align:center; padding:30px 20px; }}
            .card {{ font-size:32px; margin-top:60px; }}
            .answer {{ font-size:22px; margin-top:20px; }}
            .example {{ font-size:16px; max-width:700px; margin-left:auto; margin-right:auto; margin-top:15px; text-align:center; }}
            button {{ font-size:18px; padding:14px 20px; margin:10px; width:80%; max-width:350px; display:block; margin-left:auto; margin-right:auto; }}
        </style>
    </head>
    <body>
        <h2>{deck_name}</h2>
        <div class="card">{card['front']}</div>
        <form method="get">
            <input type="hidden" name="used" value="{used_str}">
            <input type="hidden" name="unknown" value="{unknown_str}">
            <button name="show" value="1">정답 보기</button>
            <button name="know" value="1">알고있음</button>
            <button name="review" value="1">다시 공부하기</button>
        </form>
    """

    # 정답보기 눌렀을 때
    if show:
        html += f"""
        <div class="answer"><b>{card['back']}</b></div>
        <div class="answer">{card.get('explanation','')}</div>
        <div class="example">{card.get('example','')}</div>
        """

    # 알고있음 버튼 처리: 바로 다음 카드
    if request.args.get("know"):
        return f'<meta http-equiv="refresh" content="0; url=/deck/{deck_name}?used={used_str}&unknown={unknown_str}">'

    # 다시 공부하기 버튼 처리: unknown 리스트에 추가
    if request.args.get("review"):
        unknown_list.append(idx)
        unknown_str = ",".join(map(str, unknown_list))
        return f'<meta http-equiv="refresh" content="0; url=/deck/{deck_name}?used={used_str}&unknown={unknown_str}">'

    return html

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

