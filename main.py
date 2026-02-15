from flask import Flask, request, render_template_string
import pandas as pd
import os
from natsort import natsorted

app = Flask(__name__)
DECK_FOLDER = './decks'

# HTML 템플릿
INDEX_HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>덱 선택</title>
<style>
body { font-family: Arial, sans-serif; text-align:center; padding:20px; }
a { text-decoration:none; color:#4B0082; font-size:18px; display:block; margin:8px 0; }
</style>
</head>
<body>
<h1>덱 선택</h1>
{% for deck in decks %}
    <a href="/deck/{{ deck }}">{{ deck }}</a>
{% endfor %}
</body>
</html>
"""

DECK_HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{{ deck_name }}</title>
<style>
body { font-family: Arial, sans-serif; text-align:center; padding:20px; }
p { font-size: 20px; line-height: 1.5; }
a { font-size:18px; color:#4B0082; text-decoration:none; display:block; margin-top:20px; }
</style>
</head>
<body>
<h1>{{ deck_name }}</h1>
<p>단어: id {{ word_id }}<br>
front {{ front }}<br>
back {{ back }}<br>
explanation {{ explanation }}<br>
example {{ example }}</p>

{% if next_index is not none %}
    <a href="/deck/{{ deck_name }}?index={{ next_index }}">다음 단어</a>
{% else %}
    <p>Finished.</p>
    <a href="/">덱 선택으로 돌아가기</a>
{% endif %}
</body>
</html>
"""

@app.route('/')
def index():
    files = os.listdir(DECK_FOLDER)
    # 파일명 정렬
    sorted_files = natsorted([f for f in files if f.endswith('.xlsx')])
    return render_template_string(INDEX_HTML, decks=sorted_files)

@app.route('/deck/<deck_name>')
def deck_page(deck_name):
    deck_path = os.path.join(DECK_FOLDER, deck_name)
    if not os.path.exists(deck_path):
        return "Deck not found.", 404

    df = pd.read_excel(deck_path)
    # index query parameter 처리
    index_param = request.args.get('index', 0)
    try:
        idx = int(index_param)
    except:
        idx = 0

    if idx >= len(df):
        next_index = None
        word_data = df.iloc[-1]
    else:
        next_index = idx + 1 if idx + 1 < len(df) else None
        word_data = df.iloc[idx]

    return render_template_string(DECK_HTML,
                                  deck_name=deck_name,
                                  word_id=word_data.get('id', '-'),
                                  front=word_data.get('front', '-'),
                                  back=word_data.get('back', '-'),
                                  explanation=word_data.get('explanation', '-'),
                                  example=word_data.get('example', '-'),
                                  next_index=next_index)
                                  
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)

