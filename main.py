from flask import Flask, render_template, request, redirect
import os
import pandas as pd
import random
from urllib.parse import unquote
import natsort

app = Flask(__name__)

# 덱 목록 불러오기 (파일 이름 순 정렬)
def get_decks():
    decks_folder = './decks'
    deck_files = os.listdir(decks_folder)
    deck_files = natsort.natsorted(deck_files)
    return deck_files

# 메인페이지: 덱 선택 화면
@app.route('/')
def index():
    decks = get_decks()
    return render_template('index.html', decks=decks)

# 학습 화면
@app.route('/deck/<filename>')
def deck(filename):
    filename = unquote(filename)
    filepath = os.path.join('decks', filename)

    try:
        df = pd.read_excel(filepath, engine='openpyxl')
    except Exception as e:
        return f"엑셀 파일 읽기 오류: {e}", 500

    # front, back, explanation, example 추출
    front_list = df['front'].tolist()
    back_list = df['back'].tolist()
    explanation_list = df['explanation'].tolist()
    example_list = df['example'].tolist()

    # 단어 랜덤 선택 (한 번만 나오도록)
    remaining_indices = list(range(len(front_list)))
    random_idx = random.choice(remaining_indices)
    word = front_list[random_idx]
    back = back_list[random_idx]
    explanation = explanation_list[random_idx]
    example = example_list[random_idx]

    return render_template('learning.html',
                           filename=filename,
                           word=word,
                           back=back,
                           explanation=explanation,
                           example=example)

# 정답 보기
@app.route('/answer/<filename>/<word>')
def answer(filename, word):
    filename = unquote(filename)
    filepath = os.path.join('decks', filename)
    df = pd.read_excel(filepath, engine='openpyxl')

    row = df[df['front'] == word].iloc[0]
    back = row['back']
    explanation = row['explanation']
    example = row['example']

    return render_template('answer.html',
                           word=word,
                           back=back,
                           explanation=explanation,
                           example=example)

# 피니시 화면
@app.route('/finish')
def finish():
    return render_template('finish.html')

if __name__ == '__main__':
    app.run(debug=True)

