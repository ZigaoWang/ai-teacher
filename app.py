import openai
import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_session import Session
import markdown
from bs4 import BeautifulSoup
import uuid

# Load environment variables from .env file
load_dotenv()

# Get the OpenAI API key from environment variables
api_key = os.getenv('OPENAI_API_KEY')
client = openai.OpenAI(api_key=api_key)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

def convert_md_to_html(md_text):
    html = markdown.markdown(md_text, extensions=['fenced_code', 'tables', 'toc', 'footnotes', 'attr_list', 'md_in_html'])
    soup = BeautifulSoup(html, 'lxml')

    for code in soup.find_all('code'):
        parent = code.parent
        if parent.name == 'pre':
            language = code.get('class', [''])[0].replace('language-', '') or 'text'
            code['class'] = f'language-{language}'
            copy_button_html = f'''
            <div class="code-header">
                <span class="language-label">{language}</span>
                <button class="copy-button" onclick="copyToClipboard(this)">
                    <svg aria-hidden="true" height="16" viewBox="0 0 16 16" version="1.1" width="16" data-view-component="true" class="octicon octicon-copy js-clipboard-copy-icon">
                        <path d="M0 6.75C0 5.784.784 5 1.75 5h1.5a.75.75 0 0 1 0 1.5h-1.5a.25.25 0 0 0-.25.25v7.5c0 .138.112.25.25.25h7.5a.25.25 0 0 0 .25-.25v-1.5a.75.75 0 0 1 1.5 0v1.5A1.75 1.75 0 0 1 9.25 16h-7.5A1.75 1.75 0 0 1 0 14.25Z"></path>
                        <path d="M5 1.75C5 .784 5.784 0 6.75 0h7.5C15.216 0 16 .784 16 1.75v7.5A1.75 1.75 0 0 1 14.25 11h-7.5A1.75 1.75 0 0 1 5 9.25Zm1.75-.25a.25.25 0 0 0-.25.25v7.5c0 .138.112.25.25.25h7.5a.25.25 0 0 0 .25-.25v-7.5a.25.25 0 0 0-.25-.25Z"></path>
                    </svg>
                </button>
            </div>
            '''
            parent.insert_before(BeautifulSoup(copy_button_html, 'lxml'))

    return soup.prettify()

@app.route('/')
def home():
    if 'conversations' not in session:
        session['conversations'] = {}
    return render_template('index.html', chat_id=None, messages=[], conversations=session['conversations'])

@app.route('/chat/<chat_id>')
def chat(chat_id):
    if 'conversations' not in session or chat_id not in session['conversations']:
        return redirect(url_for('home'))
    return render_template('index.html', chat_id=chat_id, messages=session['conversations'][chat_id]['messages'], conversations=session['conversations'])

@app.route('/new_chat', methods=['POST', 'GET'])
def new_chat():
    chat_id = str(uuid.uuid4())
    session['conversations'][chat_id] = {'messages': [], 'title': ''}
    if request.method == 'POST':
        return jsonify({'chat_id': chat_id})
    else:
        return redirect(url_for('chat', chat_id=chat_id))

@app.route('/delete_chat/<chat_id>', methods=['POST'])
def delete_chat(chat_id):
    if 'conversations' in session and chat_id in session['conversations']:
        del session['conversations'][chat_id]
    return jsonify({'success': True})

@app.route('/ask/<chat_id>', methods=['POST'])
def ask(chat_id):
    if 'conversations' not in session or chat_id not in session['conversations']:
        return jsonify({'error': 'Chat not found'}), 404

    user_input = request.json.get('question')
    if not user_input:
        return jsonify({'error': 'No question provided'}), 400

    messages = session['conversations'][chat_id]['messages']
    messages.append({"role": "user", "content": user_input})

    openai_messages = [
        {"role": "system", "content": "你是一位中学的英语老师，你要根据提供的中考真题来教学生。你要当一位很好的中学老师，很耐心，很专业，也很关心学生。你要帮助学生学习英语，跟他对话，让他爱上学习，并且觉得学习有趣，觉得你作为老师很有趣。"},
        *messages
    ]

    response = get_response_from_openai(openai_messages)
    messages.append({"role": "assistant", "content": response})

    session['conversations'][chat_id]['title'] = generate_title(messages)

    session['conversations'][chat_id]['messages'] = messages
    # Move the most recent conversation to the top
    session['conversations'] = {chat_id: session['conversations'][chat_id], **{k: v for k, v in session['conversations'].items() if k != chat_id}}
    return jsonify({'response': response})

def get_response_from_openai(messages):
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=1500,
            temperature=0.5,
        )
        return convert_md_to_html(response.choices[0].message.content.strip())
    except Exception as e:
        return f"Error: {str(e)}"

def generate_title(messages):
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages + [{"role": "user", "content": "Provide a short and descriptive title for this "
                                                             "conversation. Make it short, so 8 words max. And don't "
                                                             "include anything else. Do not include Title: at the "
                                                             "beginning."}],
            max_tokens=10,
            temperature=0.5,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return "Untitled Conversation"

if __name__ == '__main__':
    app.run(debug=True)