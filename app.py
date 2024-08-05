import os
import sys
import uuid
import markdown
import openai
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template, session, redirect, url_for, send_from_directory
from flask_session import Session
from models import db, User
from pathlib import Path
import logging

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables from .env file
load_dotenv()

# Get the OpenAI/Turbo AI API key and base URL from environment variables
api_key = os.getenv('OPENAI_API_KEY')
base_url = os.getenv('OPENAI_BASE_URL')
client = openai.OpenAI(api_key=api_key, base_url=base_url)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///students.db'
app.config['SESSION_TYPE'] = 'filesystem'
db.init_app(app)
Session(app)

with app.app_context():
    db.create_all()

# Configure logging
logging.basicConfig(level=logging.INFO)

def convert_md_to_html(md_text):
    html = markdown.markdown(md_text,
                             extensions=['fenced_code', 'tables', 'toc', 'footnotes', 'attr_list', 'md_in_html'])
    soup = BeautifulSoup(html, 'lxml')
    return soup.prettify()


def get_response_from_openai(messages):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=4096,
            temperature=0.5,
        )
        markdown_content = response.choices[0].message.content.strip()
        html_content = convert_md_to_html(markdown_content)
        return html_content
    except Exception as e:
        logging.error(f"Error in get_response_from_openai: {str(e)}")
        return f"Error: {str(e)}"


def initial_setup_prompt(user):
    initial_prompt = [
        {"role": "system",
         "content": f"你是一位中学的英语老师，你要根据提供的中考真题来教学生。你要当一位很好的中学老师，很耐心，很专业，也很关心学生。你要帮助学生学习英语，跟他对话，让他爱上学习，并且觉得学习有趣，觉得你作为老师很有趣。请根据这些内容生成一道中考形式的英语题目，并用英语与学生互动。你可以用有趣的例子、故事和趣闻来解释概念，但不要偏离主题。学生问你你是谁时，可以简单地介绍自己是由王子高开发的 AI 老师，不要每次都重复。保持对话的流畅和自然。学生的名字是 {user.name}，他的年龄是 {user.age} 岁，他最喜欢的科目是 {user.favorite_subject}，他的学习目标是 {user.learning_goals}，他的兴趣爱好是 {user.hobbies}，他喜欢的学习风格是 {user.preferred_learning_style}，他遇到的学习挑战是 {user.challenges}。请根据这些信息与学生互动，帮助他们提高英语水平。"}
    ]

    response = get_response_from_openai(initial_prompt)
    session['conversation'].append({"role": "assistant", "content": response})


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        name = request.form['name']

        # Check if the username already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return render_template('register.html', error='用户名已注册，请选择其他用户名')

        user = User(username=username, name=name)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            return redirect(url_for('onboarding'))
        else:
            return render_template('login.html', error='用户名或密码错误。请重试，或者注册新账户。')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/onboarding', methods=['GET', 'POST'])
def onboarding():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    if request.method == 'POST':
        user.age = request.form['age']
        user.favorite_subject = request.form['favorite_subject']
        user.learning_goals = request.form['learning_goals']
        user.hobbies = request.form['hobbies']
        user.preferred_learning_style = request.form['preferred_learning_style']
        user.challenges = request.form['challenges']
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('onboarding.html', user=user)


@app.route('/')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    if 'conversation' not in session:
        session['conversation'] = []
        initial_setup_prompt(user)
    return render_template('index.html', messages=[msg for msg in session['conversation'] if msg['role'] != 'system'], user=user)


@app.route('/ask', methods=['POST'])
def ask():
    if 'conversation' not in session:
        session['conversation'] = []

    user_input = request.json.get('question')
    if not user_input:
        return jsonify({'error': 'No question provided'}), 400

    user = User.query.get(session['user_id'])
    messages = session['conversation']
    messages.append({"role": "user", "content": user_input})

    # Include user details in the conversation context
    user_info = f"你是一位中学的英语老师，你要根据提供的中考真题来教学生。你要当一位很好的中学老师，很耐心，很专业，也很关心学生。你要帮助学生学习英语，跟他对话，让他爱上学习，并且觉得学习有趣，觉得你作为老师很有趣。你可以用有趣的例子、故事和趣闻来解释概念，但不要偏离主题。学生问你你是谁时，可以简单地介绍自己是由王子高开发的 AI 老师，不要每次都重复。保持对话的流畅和自然。学生的名字是 {user.name}，他的年龄是 {user.age} 岁，他最喜欢的科目是 {user.favorite_subject}，他的学习目标是 {user.learning_goals}，他的兴趣爱好是 {user.hobbies}，他喜欢的学习风格是 {user.preferred_learning_style}，他遇到的学习挑战是 {user.challenges}。请根据这些信息与学生互动，帮助他们提高英语水平。"
    messages.append({"role": "system", "content": user_info})

    response = get_response_from_openai(messages)
    messages.append({"role": "assistant", "content": response})

    session['conversation'] = messages
    return jsonify({'response': response})


@app.route('/tts', methods=['POST'])
def tts():
    text = request.json.get('text')
    if not text:
        return jsonify({'error': 'No text provided'}), 400

    try:
        unique_filename = f"speech_{uuid.uuid4()}.mp3"
        speech_file_path = Path(__file__).parent / "temp" / unique_filename

        # Ensure the temp directory exists
        os.makedirs(os.path.dirname(speech_file_path), exist_ok=True)

        response = client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=text
        )
        response.stream_to_file(speech_file_path)
        audio_url = f"/temp/{unique_filename}"
    except Exception as e:
        logging.error(f"Error in tts endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 400

    return jsonify({'audio_url': audio_url})


@app.route('/temp/<filename>')
def serve_temp_file(filename):
    return send_from_directory(os.path.join(app.root_path, 'temp'), filename)


@app.route('/stt', methods=['POST'])
def stt():
    if 'audio' not in request.files:
        logging.error("No audio file provided")
        return jsonify({'error': 'No audio file provided'}), 400

    audio_file = request.files['audio']
    audio_path = Path(__file__).parent / "temp" / audio_file.filename

    # Ensure the temp directory exists
    os.makedirs(os.path.dirname(audio_path), exist_ok=True)

    audio_file.save(audio_path)

    try:
        with open(audio_path, "rb") as f:
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                response_format="text"
            )
        logging.info(f"Transcription response: {transcription}")
        text = transcription if isinstance(transcription, str) else transcription['text']
    except Exception as e:
        logging.error(f"Error in stt endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 400

    return jsonify({'text': text})


@app.route('/speech_mode')
def speech_mode():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    if 'conversation' not in session:
        session['conversation'] = []
        initial_setup_prompt(user)
    return render_template('speech_mode.html', messages=[msg for msg in session['conversation'] if msg['role'] != 'system'], user=user)


if __name__ == '__main__':
    app.run(debug=True)