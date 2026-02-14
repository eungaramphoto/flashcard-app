from flask import Flask, request, render_template_string
import os
import pandas as pd
import random

app = Flask(__name__)
DECK_FOLDER = "decks"

# 메인 화면
@app.route("/")
def index():
    decks = [f for f in os.listdir(DECK_FOLDER) if f.endswith(".xlsx")]
    html = """
    <!doctype html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family:-apple-system, BlinkMacSystemFont, sans-serif; text-align:center; padding:50px 20px; font-size:20px;}
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
    path = os.path.join(DECK_FOLDER, deck_name)
    df = pd.read_excel(path).dropna(subset=["front","back"])

    # URL 파라미터
    used = request.args.get("used","")
    again = request.args.get("again","")
    show = request.args.get("show")
    current = request.args.get("current")
    repeat_level = int(request.args.get("level",1))

    # 안전한 리스트 변환
    def parse_list(param):
        try:
            return [int(i) for i in param.split(",") if i.strip().isdigit()]
        except:
            return []
    used_list = parse_list(used)
    again_list = parse_list(again)

    # 첫 재생인지 다시 공부하기 재생인지 판단
    if again_list:
        remaining = [i for i in again_list if i not in used_list]
        level = repeat_level
    else:
        remaining = [i for i in range(len(df)) if i not in used_list]
        level = 1

    # 종료 조건
    if not remaining:
        if again_list:
            # 다음 회독 시작
            remaining = again_list
            used_list = []
            again_list = []
            level += 1
        else:
            # 모든 단어 완료
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
                        <button>덱 목록으로</button>
                    </form>
                </body>
                </html>
            """)

    # 현재 카드 선택
    if current and current.isdigit():
        idx = int(current)
    else:
        idx = random.choice(remaining)

    card = df.iloc[idx]

    # used/again 문자열
    new_used = used_list if show else used_list + [idx]
    used_str = ",".join(map(str,new_used))
    again_str = ",".join(map(str,again_list))

    html = f"""
    <!doctype html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ font-family:-apple-system, BlinkMacSystemFont, sans-serif; text-align:center; padding:50px 20px; }}
            h2 {{ font-size:28px; margin-bottom:30px; }}
            .card {{ font-size:32px; margin-top:60px; }}
            .answer {{ font-size:22px; margin-top:20px; }}
            .example {{ font-size:16px; max-width:700px; margin:20px auto; text-align:center; }}
            button {{ font-size:20px; padding:14px 20px; margin:15px auto; display:block; width:80%; max-width:350px; }}
        </style>
    </head>
    <body>
        <h2>{deck_name} ({level}회독)</h2>
        <div class="card">{card['front']}</div>
        <form method="get">
            <input type="hidden" name="used" value="{used_str}">
            <input type="hidden" name="again" value="{again_str}">
            <input type="hidden" name="level" value="{level}">
            <button name="show" value="1">정답 보기</button>
            <button name="know" value="1">알고있음</button>
            <button name="review" value="1">다시 공부하기</button>
        </form>
    """

    # 정답보기
    if show:
        html += f"""
        <div class="answer"><b>{card['back']}</b></div>
        <div class="answer">{card.get('explanation','')}</div>
        <div class="example">{card.get('example','')}</div>
        """

    # 알고있음 버튼: 바로 다음 카드
    if request.args.get("know"):
        return f'<meta http-equiv="refresh" content="0; url=/deck/{deck_name}?used={used_str}&again={again_str}&level={level}">'

    # 다시 공부하기 버튼: 다시 공부 리스트에 저장
    if request.args.get("review"):
        if idx not in again_list:
            again_list.append(idx)
        again_str = ",".join(map(str,again_list))
        return f'<meta http-equiv="refresh" content="0; url=/deck/{deck_name}?used={used_str}&again={again_str}&level={level}">'

    return html

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

