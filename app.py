import openai
import os
from dotenv import load_dotenv
from docx import Document

# Load environment variables from .env file
load_dotenv()

# Initialize the OpenAI client
client = openai.OpenAI(
    api_key=os.getenv('OPENAI_API_KEY')
)


def read_docx(file_path):
    doc = Document(file_path)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return '\n'.join(full_text)


def send_chunk_to_ai(content):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "你是一位中学的英语老师，你要根据提供的中考真题来教学生"},
            {"role": "user",
             "content": f"这是中考真题的一部分:\n{content}\n\n请确认你已经接收到这部分内容并回复'Input Success!'。只需要回复'Input Success'，不要回复别的。"}
        ],
        max_tokens=50,
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()


def generate_questions():
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "你是一位中学的英语老师，你要根据提供的中考真题来教学生"},
            {"role": "user",
             "content": "你已经接收了所有的中考真题内容，请根据这些内容生成十道中考形式的英语题目，要有不同形式的，请学习中考真题里的风格，谢谢！只需要给我题目，不需要说别的。只要题目，谢谢！"}
        ],
        max_tokens=5000,
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()


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


if __name__ == '__main__':
    directory = 'data'  # Directory containing the .docx files
    combined_content_list = process_all_docx_files(directory)
    combined_content = '\n'.join(combined_content_list)

    # Send chunks to AI and confirm receipt
    for chunk in chunk_text(combined_content):
        confirmation = send_chunk_to_ai(chunk)
        print(f"AI Response: {confirmation}")

    # Generate questions after all chunks have been processed
    questions = generate_questions()
    print("Generated Questions:")
    print(questions)