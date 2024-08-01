#
# AI-Teacher
#
# Created by Zigao Wang on August 1, 2024 This project is designed to create an AI-driven interactive teacher for
# middle school students, focusing on English exam preparation. The AI will generate questions, evaluate answers,
# and provide feedback.
#
# 由王子高于2024年8月1日创建
# 该项目旨在为中学生创建一个AI驱动的互动教师，专注于英语考试准备。AI将生成问题，评估答案，并提供反馈。
#

import openai
import os
import json
from dotenv import load_dotenv
from docx import Document
from time import sleep

# 加载环境变量 Load environment variables
load_dotenv()

# 初始化 OpenAI 客户端 Initialize the OpenAI client
from openai import OpenAI

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# 缓存文件路径 Cache file path
CACHE_FILE = 'cache.json'

def read_docx(file_path):
    """读取 docx 文件内容 Read content from a docx file"""
    doc = Document(file_path)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return '\n'.join(full_text)

def send_chunk_to_ai(content, session_id, retries=3):
    """发送文本块到 AI 并确认接收 Send text chunk to AI and confirm receipt"""
    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "你是一位中学的英语老师，你要根据提供的中考真题来教学生。你要当一位很好的中学老师，很耐心，很专业，也很关心学生。你要帮助学生学习英语，跟他对话，让他爱上学习，并且觉得学习有趣，觉得你作为老师很有趣。"},
                    {"role": "user",
                     "content": f"这是中考真题的一部分:\n{content}\n\n请确认你已经接收到这部分内容并回复'Input Success!'。只需要回复'Input Success'，不要回复别的。"}
                ],
                max_tokens=50,
                temperature=0.7,
                timeout=60
            )
            return response.choices[0].message.content.strip()
        except openai.OpenAIError as e:
            print(f"Error on attempt {attempt + 1}: {e}")
            if attempt < retries - 1:
                sleep(2 ** attempt)  # 指数退避 Exponential backoff
            else:
                raise

def generate_question(session_id, retries=3):
    """生成一道中考形式的英语题目 Generate a single exam-style English question"""
    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "你是一位中学的英语老师，你要根据提供的中考真题来教学生"},
                    {"role": "user",
                     "content": "请根据这些内容生成一道中考形式的英语题目，要有不同形式的，请学习中考真题里的风格，谢谢！只要一道就行了，一道，那这道题目来来考考你的学生。要当老师！"}
                ],
                max_tokens=150,
                temperature=0.7,
                timeout=60
            )
            return response.choices[0].message.content.strip()
        except openai.OpenAIError as e:
            print(f"Error on attempt {attempt + 1}: {e}")
            if attempt < retries - 1:
                sleep(2 ** attempt)  # 指数退避 Exponential backoff
            else:
                raise

def evaluate_answer(question, answer, session_id, retries=3):
    """评估学生的回答并提供反馈 Evaluate student's answer and provide feedback"""
    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "你是一位中学的英语老师，你要根据提供的中考真题来教学生。你要当一位很好的中学老师，很耐心，很专业，也很关心学生。你要帮助学生学习英语，跟他对话，让他爱上学习，并且觉得学习有趣，觉得你作为老师很有趣。"},
                    {"role": "user",
                     "content": f"题目：{question}\n学生的答案：{answer}\n请给出评分和反馈。要记住，你是一位中学老师哦！"}
                ],
                max_tokens=150,
                temperature=0.7,
                timeout=60
            )
            return response.choices[0].message.content.strip()
        except openai.OpenAIError as e:
            print(f"Error on attempt {attempt + 1}: {e}")
            if attempt < retries - 1:
                sleep(2 ** attempt)  # 指数退避 Exponential backoff
            else:
                raise

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

def chunk_text(text, chunk_size=1500):
    """将文本分块 Chunk the text"""
    words = text.split()
    for i in range(0, len(words), chunk_size):
        yield ' '.join(words[i:i + chunk_size])

def load_cache():
    """加载缓存 Load cache"""
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_cache(cache):
    """保存缓存 Save cache"""
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f)

def initialize_student_profile(student_name):
    """初始化学生档案 Initialize student profile"""
    profile = {
        "name": student_name,
        "preferences": {},
        "progress": {}
    }
    return profile

def update_student_profile(profile, key, value):
    """更新学生档案 Update student profile"""
    profile[key] = value
    return profile

if __name__ == '__main__':
    directory = 'data'  # .docx 文件所在目录 Directory containing the .docx files
    student_name = input("请输入学生的名字: ")

    # 加载缓存 Load cache
    cache = load_cache()
    session_id = cache.get('session_id', None)
    processed_chunks = cache.get('processed_chunks', [])
    student_profile = cache.get('student_profile', initialize_student_profile(student_name))

    combined_content_list = process_all_docx_files(directory)
    combined_content = '\n'.join(combined_content_list)

    # 发送文本块到 AI 并确认接收 Send chunks to AI and confirm receipt
    for chunk in chunk_text(combined_content):
        if chunk not in processed_chunks:
            confirmation = send_chunk_to_ai(chunk, session_id)
            print(f"AI Response: {confirmation}")
            if confirmation == 'Input Success!':
                processed_chunks.append(chunk)

    # 保存缓存 Save cache
    cache['session_id'] = session_id
    cache['processed_chunks'] = processed_chunks
    cache['student_profile'] = student_profile
    save_cache(cache)

    # 交互式会话 Interactive session
    while True:  # 持续对话 Continuous loop for interaction
        question = generate_question(session_id)
        print(f"Question: {question}")
        student_answer = input("Your answer: ")
        feedback = evaluate_answer(question, student_answer, session_id)
        print(f"Feedback: {feedback}")
        # 根据反馈更新学生档案 Update student profile based on feedback if needed
        progress_key = f"question_{len(student_profile['progress']) + 1}"
        student_profile['progress'][progress_key] = {
            "question": question,
            "answer": student_answer,
            "feedback": feedback
        }
        # 保存缓存 Save cache
        cache['student_profile'] = student_profile
        save_cache(cache)

        # 询问学生是否继续回答问题 Ask if the student wants another question or to end the session
        continue_session = input("要继续回答问题吗？(yes/no): ")
        if continue_session.lower() != 'yes':
            break