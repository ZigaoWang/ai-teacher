import openai
import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import markdown
from bs4 import BeautifulSoup

# Load environment variables from .env file
load_dotenv()

# Get the OpenAI API key from environment variables
api_key = os.getenv('OPENAI_API_KEY')
base_url = os.getenv('OPENAI_BASE_URL')
client = openai.OpenAI(api_key=api_key, base_url=base_url)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///students.db'
app.config['SESSION_TYPE'] = 'filesystem'
db = SQLAlchemy(app)
Session(app)


# Database Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    age = db.Column(db.Integer)
    favorite_subject = db.Column(db.String(150))
    learning_goals = db.Column(db.Text)
    hobbies = db.Column(db.String(250))
    preferred_learning_style = db.Column(db.String(150))
    challenges = db.Column(db.Text)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


with app.app_context():
    db.create_all()


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
        return f"Error: {str(e)}"


def initial_setup_prompt(user):
    initial_prompt = [
        {"role": "system",
         "content": f"你是一位中学的英语老师，你要根据提供的中考真题来教学生。你要当一位很好的中学老师，很耐心，很专业，也很关心学生。你要帮助学生学习英语，跟他对话，让他爱上学习，并且觉得学习有趣，觉得你作为老师很有趣。请根据这些内容生成一道中考形式的英语题目，要有不同形式的，请学习中考真题里的风格，谢谢！每次只要一道就行了，一道，不要太多，拿这道题目来来考考你的学生。要当老师！你是一位老师，不是别人。学生问你你是谁，你就说你是由王子高开发的 AI 老师，是帮助你们学习的。你要主动，你要问学生名字，给他们出题目。一次不要说太多，要一点一点来，要想真正的老师。学生的名字是 {user.name}，他的年龄是 {user.age} 岁，他最喜欢的科目是 {user.favorite_subject}，他的学习目标是 {user.learning_goals}，他的兴趣爱好是 {user.hobbies}，他喜欢的学习风格是 {user.preferred_learning_style}，他遇到的学习挑战是 {user.challenges}。"}
    ]

    response = get_response_from_openai(initial_prompt)
    session['conversation'].append({"role": "assistant", "content": response})


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        name = request.form['name']
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
            return 'Invalid credentials'
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
    return render_template('index.html', messages=session['conversation'], user=user)


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
    user_info = f"学生的名字是 {user.name}，他的年龄是 {user.age} 岁，他最喜欢的科目是 {user.favorite_subject}，他的学习目标是 {user.learning_goals}，他的兴趣爱好是 {user.hobbies}，他喜欢的学习风格是 {user.preferred_learning_style}，他遇到的学习挑战是 {user.challenges}。"
    messages.append({"role": "system", "content": user_info})

    response = get_response_from_openai(messages)
    messages.append({"role": "assistant", "content": response})

    session['conversation'] = messages
    return jsonify({'response': response})


if __name__ == '__main__':
    app.run(debug=True)