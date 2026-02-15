from flask import Flask, request, redirect, render_template_string
import os
import pandas as pd
from natsort import natsorted

app = Flask(__name__)

# 덱 파일 경로 설정
DECKS_DIR = "decks"

# 덱 파일 목록 불러오기
def get_deck_files():
    # decks 폴더에 있는 모든 엑셀 파일을 나열하고 정렬하기
    files = [f for f in os.listdir(DECKS_DIR) if f.endswith('.xlsx')]
    sorted_files = natsorted(files)  # natsorted 사용하여 파일명 정렬
    return sorted_files

@app.route('/')
def home():
    # 덱 파일 목록을 받아오기
    decks = get_deck_files()
    
    # 파일 목록을 덱 선택 화면에 표시
    return render_template_string('''
        <h1>덱 선택</h1>
        <ul>
            {% for deck in decks %}
                <li><a href="/deck/{{ deck }}">{{ deck }}</a></li>
            {% endfor %}
        </ul>
    ''', decks=decks)

@app.route('/deck/<deck_name>')
def deck(deck_name):
    deck_path = os.path.join(DECKS_DIR, deck_name)
    
    if not os.path.exists(deck_path):
        return "Deck not found!", 404

    # 엑셀 파일을 데이터프레임으로 읽기
    df = pd.read_excel(deck_path)

    # 데이터를 랜덤으로 섞고 반환 (또는 필요한대로 변경 가능)
    df_shuffled = df.sample(frac=1).reset_index(drop=True)

    # 첫번째 단어만 출력하는 예시
    word = df_shuffled.iloc[0]
    
    return render_template_string('''
        <h1>{{ deck_name }}</h1>
        <p>단어: {{ word }}</p>
        <a href="/">덱 선택으로 돌아가기</a>
    ''', deck_name=deck_name, word=word)

if __name__ == "__main__":
    app.run(debug=True)

