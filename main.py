import os
import random
import pandas as pd
from flask import Flask, render_template_string, request, redirect, url_for

app = Flask(__name__)

# 덱 파일 경로 설정 (파일들이 현재 작업 디렉토리에 있다고 가정)
deck_folder = './decks/'

# 덱 파일 목록을 동적으로 읽어오기 (디렉토리 내 모든 엑셀 파일)
def get_deck_files():
    # 'decks' 폴더 내 모든 파일을 읽고, .xlsx 확장자를 가진 파일만 필터링
    files = [f for f in os.listdir(deck_folder) if f.endswith('.xlsx')]
    # 파일 이름순으로 정렬 (natsort를 사용할 수도 있습니다.)
    sorted_files = sorted(files)
    return sorted_files

# 덱 선택 화면
@app.route('/')
def index():
    # 덱 파일 목록 읽기
    sorted_decks = get_deck_files()
    return render_template_string("""
    <h1>덱 선택</h1>
    <ul>
        {% for deck in sorted_decks %}
        <li><a href="{{ url_for('study', deck_name=deck) }}">{{ deck }}</a></li>
        {% endfor %}
    </ul>
    """, sorted_decks=sorted_decks)

# 학습 화면 (front 단어 표시)
@app.route('/study/<deck_name>', methods=['GET', 'POST'])
def study(deck_name):
    # 선택된 덱 파일 경로
    deck_path = os.path.join(deck_folder, deck_name)
    
    # 엑셀 파일 읽기
    df = pd.read_excel(deck_path)

    # 단어 정보 목록
    words = df.to_dict(orient='records')
    
    # 단어를 랜덤으로 섞어서 저장
    random.shuffle(words)
    
    # 현재 단어 인덱스
    current_word_index = request.args.get('index', 0, type=int)
    
    # 모든 단어가 소진되었으면 피니시 화면으로 넘어가기
    if current_word_index >= len(words):
        return redirect(url_for('finished'))  # 모든 단어가 다 표시된 후 Finish 화면으로 이동
    
    current_word = words[current_word_index]
    
    # 정답 보기 버튼 클릭시 back, explanation, example도 표시
    show_answer = request.args.get('show_answer', False, type=bool)

    return render_template_string("""
    <h1>{{ deck_name }}</h1>
    <p>단어: id {{ current_word['id'] }}<br>front {{ current_word['front'] }}</p>
    
    {% if show_answer %}
        <p>back {{ current_word['back'] }}</p>
        <p>explanation {{ current_word['explanation'] }}</p>
        <p>example {{ current_word['example'] }}</p>
    {% endif %}
    
    <br><br>
    
    <a href="{{ url_for('study', deck_name=deck_name, index=current_word_index + 1) }}">다음 단어</a>
    <br><br>
    
    <a href="{{ url_for('study', deck_name=deck_name, index=current_word_index, show_answer=True) }}">정답 보기</a>
    <br><br>
    
    <a href="{{ url_for('index') }}">덱 선택으로 돌아가기</a>
    """, deck_name=deck_name, current_word=current_word, show_answer=show_answer)

# Finish 화면 (단어가 모두 끝나면 보여짐)
@app.route('/finished')
def finished():
    return render_template_string("""
    <h1>학습 완료!</h1>
    <a href="{{ url_for('index') }}">덱 선택으로 돌아가기</a>
    """)

if __name__ == '__main__':
    app.run(debug=True)

