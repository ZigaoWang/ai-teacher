import openai
import os
import json
from dotenv import load_dotenv
from docx import Document
from time import sleep

# Load environment variables from .env file
load_dotenv()

# Initialize the OpenAI client
client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Cache file path
CACHE_FILE = 'cache.json'

def read_docx(file_path):
    doc = Document(file_path)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return '\n'.join(full_text)

def send_chunk_to_ai(content, session_id, retries=3):
    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "你是一位中学的英语老师，你要根据提供的中考真题来教学生。你要当以为很好的中学老师，很耐心，很专业，也很关心学生。你要帮助学生学习英语，跟他对话，让他爱上学习，并且觉得学习有趣，觉得你作为老师很有趣。"},
                    {"role": "user",
                     "content": f"这是中考真题的一部分:\n{content}\n\n请确认你已经接收到这部分内容并回复'Input Success!'。只需要回复'Input Success'，不要回复别的。"}
                ],
                max_tokens=50,
                temperature=0.7,
                timeout=60,  # Increase timeout to 60 seconds
            )
            return response.choices[0].message.content.strip()
        except openai.error.Timeout as e:
            print(f"Timeout error on attempt {attempt + 1}: {e}")
            if attempt < retries - 1:
                sleep(2 ** attempt)  # Exponential backoff
            else:
                raise

def generate_question(session_id, retries=3):
    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "你是一位中学的英语老师，你要根据提供的中考真题来教学生"},
                    {"role": "user",
                     "content": "请根据这些内容生成一道中考形式的英语题目，要有不同形式的，请学习中考真题里的风格，谢谢！只要一道就行了，一道，那这道题目来来考考你的学生。要当老师！"}
                ],
                max_tokens=5000,
                temperature=0.7,
                timeout=60,  # Increase timeout to 60 seconds
            )
            return response.choices[0].message.content.strip()
        except openai.error.Timeout as e:
            print(f"Timeout error on attempt {attempt + 1}: {e}")
            if attempt < retries - 1:
                sleep(2 ** attempt)  # Exponential backoff
            else:
                raise

def evaluate_answer(question, answer, session_id, retries=3):
    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "你是一位中学的英语老师，你要根据提供的中考真题来教学生。你要当以为很好的中学老师，很耐心，很专业，也很关心学生。你要帮助学生学习英语，跟他对话，让他爱上学习，并且觉得学习有趣，觉得你作为老师很有趣。"},
                    {"role": "user",
                     "content": f"题目：{question}\n学生的答案：{answer}\n请给出评分和反馈。要记住，你是一位中学老师哦！"}
                ],
                max_tokens=500,
                temperature=0.7,
                timeout=60,  # Increase timeout to 60 seconds
            )
            return response.choices[0].message.content.strip()
        except openai.error.Timeout as e:
            print(f"Timeout error on attempt {attempt + 1}: {e}")
            if attempt < retries - 1:
                sleep(2 ** attempt)  # Exponential backoff
            else:
                raise

def process_all_docx_files(directory):
    combined_content = []
    for filename in os.listdir(directory):
        if filename.endswith('.docx'):
            file_path = os.path.join(directory, filename)
            print(f"Processing file: {file_path}")
            content = read_docx(file_path)
            combined_content.append(content)
    return combined_content

def chunk_text(text, chunk_size=1500):
    words = text.split()
    for i in range(0, len(words), chunk_size):
        yield ' '.join(words[i:i + chunk_size])

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_cache(cache):
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f)

def initialize_student_profile(student_name):
    # Initialize student profile
    profile = {
        "name": student_name,
        "preferences": {},
        "progress": {}
    }
    return profile

def update_student_profile(profile, key, value):
    # Update student profile
    profile[key] = value
    return profile

if __name__ == '__main__':
    directory = 'data'  # Directory containing the .docx files
    student_name = input("请输入学生的名字: ")

    # Load cache
    cache = load_cache()
    session_id = cache.get('session_id', None)
    processed_chunks = cache.get('processed_chunks', [])
    student_profile = cache.get('student_profile', initialize_student_profile(student_name))

    combined_content_list = process_all_docx_files(directory)
    combined_content = '\n'.join(combined_content_list)

    # Send chunks to AI and confirm receipt
    for chunk in chunk_text(combined_content):
        if chunk not in processed_chunks:
            confirmation = send_chunk_to_ai(chunk, session_id)
            print(f"AI Response: {confirmation}")
            if confirmation == 'Input Success!':
                processed_chunks.append(chunk)

    # Save cache
    cache['session_id'] = session_id
    cache['processed_chunks'] = processed_chunks
    cache['student_profile'] = student_profile
    save_cache(cache)

    # Interactive session
    while True:  # Continuous loop for interaction
        question = generate_question(session_id)
        print(f"Question: {question}")
        student_answer = input("Your answer: ")
        feedback = evaluate_answer(question, student_answer, session_id)
        print(f"Feedback: {feedback}")
        # Update student profile based on feedback if needed
        student_profile = update_student_profile(student_profile, f"question_{len(student_profile['progress']) + 1}", {
            "question": question,
            "answer": student_answer,
            "feedback": feedback
        })
        # Save cache
        cache['student_profile'] = student_profile
        save_cache(cache)

        # Ask if the student wants another question or to end the session
        continue_session = input("Do you want another question? (yes/no): ")
        if continue_session.lower() != 'yes':
            break