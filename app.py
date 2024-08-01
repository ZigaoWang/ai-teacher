import openai
import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template, session
from flask_session import Session
import markdown
from bs4 import BeautifulSoup
from docx import Document
import time

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

def read_docx(file_path):
    """读取 docx 文件内容 Read content from a docx file"""
    doc = Document(file_path)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return '\n'.join(full_text)

@app.route('/')
def home():
    if 'conversation' not in session:
        session['conversation'] = []
    return render_template('index.html', messages=session['conversation'])

@app.route('/new_session', methods=['POST'])
def new_session():
    session.clear()  # 清空会话和缓存
    session['conversation'] = []
    return jsonify({'message': 'New session started.'})

@app.route('/ask', methods=['POST'])
def ask():
    if 'conversation' not in session:
        session['conversation'] = []

    user_input = request.json.get('question')
    if not user_input:
        return jsonify({'error': 'No question provided'}), 400

    messages = session['conversation']
    messages.append({"role": "user", "content": user_input})

    response = get_response_from_openai(messages)
    messages.append({"role": "assistant", "content": response})

    session['conversation'] = messages
    return jsonify({'response': response})

@app.route('/load_data', methods=['POST'])
def load_data():
    if 'data_loaded' not in session:
        directory = 'data'  # .docx 文件所在目录 Directory containing the .docx files
        combined_content_list = process_all_docx_files(directory)
        combined_content = '\n'.join(combined_content_list)
        session['combined_content'] = combined_content

        # 分块处理 combined_content
        chunk_size = 10000  # 每块的最大字符数
        chunks = [combined_content[i:i + chunk_size] for i in range(0, len(combined_content), chunk_size)]

        for index, chunk in enumerate(chunks):
            openai_messages = [
                {"role": "system", "content": f"以下是一些中考英语真题内容的一部分：\n{chunk}"},
                {"role": "user", "content": f"请阅读以上内容，并回复'训练数据 #{index + 1} 输入完毕'。不要回复别的。"}
            ]
            response = get_response_from_openai(openai_messages)
            print(response)  # Print AI's response to verify it outputs '训练数据输入完毕'

        session['data_loaded'] = True

    return jsonify({'message': 'Data loaded successfully'})

def process_all_docx_files(directory):
    """处理所有的 docx 文件 Process all docx files"""
    combined_content = []
    for filename in os.listdir(directory):
        if filename.endswith('.docx'):
            file_path = os.path.join(directory, filename)
            print(f"Processing file: {file_path}")
            content = read_docx(file_path)
            combined_content.append(content)
    return combined_content

def get_response_from_openai(messages):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=4096,
            temperature=0.5,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == '__main__':
    app.run(debug=True)