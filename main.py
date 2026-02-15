from flask import Flask, render_template, request, redirect, url_for
import os
import pandas as pd
import random
from urllib.parse import unquote
from natsort import natsorted

app = Flask(__name__)

DECK_FOLDER = "decks"

# 덱 목록 가져오기
def get_decks():
    deck_files = os.listdir(DECK_FOLDER)
    deck_files = [f for f in deck_files if f.endswith(".xlsx")]
    return natsorted(deck_files)

# 메인페이지: 덱 선택 화면
@app.route('/')
def index():
    decks = get_decks()
    return render_template('index.html', decks=decks)

# 학습 화면
@app.route('/deck/<filename>')
def deck(filename):
    filename = unquote(filename)
    filepath = os.path.join(DECK_FOLDER, filename)

    try:
        df = pd.read_excel(filepath, engine='openpyxl')
    except Exception as e:
        return f"엑셀 파일 읽기 오류: {e}", 500

    # 모든 단어 리스트
    front_list = df['front'].tolist()
    back_list = df['back'].tolist()
    explanation_list = df['explanation'].tolist()
    example_list = df['example'].tolist()

    # 남은 단어가 없으면 피니시 화면
    if not front_list:
        return redirect(url_for('finish'))

    # 랜덤 인덱스 선택
    idx = random.randrange(len(front_list))
    word = front_list[idx]
    back = back_list[idx]
    explanation = explanation_list[idx]
    example = example_list[idx]

    # 현재 단어 제거 (중복 방지)
    df = df.drop(idx)
    temp_file = os.path.join(DECK_FOLDER, f"_temp_{filename}")
    df.to_excel(temp_file, index=False, engine='openpyxl')

    return render_template('learning.html',
                           filename=filename,
                           word=word,
                           back=back,
                           explanation=explanation,
                           example=example)

# 정답보기
@app.route('/answer/<filename>/<word>')
def answer(filename, word):
    filename = unquote(filename)
    filepath = os.path.join(DECK_FOLDER, filename)
    df = pd.read_excel(filepath, engine='openpyxl')

    row = df[df['front'] == word].iloc[0]
    return render_template('answer.html',
                           word=row['front'],
                           back=row['back'],
                           explanation=row['explanation'],
                           example=row['example'])

# 피니시 화면
@app.route('/finish')
def finish():
    return render_template('finish.html')

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

