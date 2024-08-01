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

def interact_with_ai(content):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "你是一位中学的英语老师，你要根据提供的中考真题来教学生"},
            {"role": "user", "content": f"这是中考真题\n{content}\n\n请再出10道英语题目，要有不同形式的，是中考形式的，请学习我给你中考真题里的风格，谢谢！10道题目"}
        ],
        max_tokens=150,
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
    return '\n'.join(combined_content)

if __name__ == '__main__':
    directory = 'data'  # Directory containing the .docx files
    combined_content = process_all_docx_files(directory)
    questions = interact_with_ai(combined_content)
    print("Generated Questions:")
    print(questions)