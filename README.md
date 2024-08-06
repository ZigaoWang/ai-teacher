# AI Teacher

AI Teacher is an interactive web application designed to help middle school students learn English. The application uses OpenAI's GPT-4o-mini model to generate engaging and educational conversations, simulating a patient and professional English teacher.

## Table of Contents

- [Project Description](#project-description)
- [Features](#features)
- [Setup Instructions](#setup-instructions)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

## Project Description

AI Teacher aims to make learning English enjoyable and effective for middle school students by providing interactive conversations with an AI teacher. The AI teacher can generate exam-style questions, provide explanations, and engage in educational dialogues.

## Features

- User registration and login
- Personalized onboarding to tailor the learning experience
- Interactive chat interface for text-based conversations
- Speech mode for voice interactions
- Text-to-speech (tts-1) and speech-to-text (whisper-1) functionalities
- Session management to keep track of conversations

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- Virtual environment tool (e.g., `venv` or `virtualenv`)
- SQLite (default database)

### Installation

1. **Clone the repository:**

   ```sh
   git clone https://github.com/yourusername/AI-Teacher.git
   cd AI-Teacher
   ```

2. **Create and activate a virtual environment:**

   ```sh
   python -m venv .venv
   source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
   ```

3. **Install the required dependencies:**

   ```sh
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**

   Create a `.env` file in the root directory and add the following:

   ```env
   FLASK_APP=app.py
   FLASK_ENV=development
   FLASK_DEBUG=1
   OPENAI_API_KEY=your_openai_api_key
   OPENAI_BASE_URL=https://api.openai.com/v1
   ```

5. **Initialize the database:**

   ```sh
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

6. **Run the application:**

   ```sh
   flask run
   ```

   The application will be available at `http://127.0.0.1:5000`.

## Usage

### User Registration and Login

1. **Register a new user:**
   - Navigate to the registration page (`/register`).
   - Fill in the required details and submit the form.

2. **Log in:**
   - Navigate to the login page (`/login`).
   - Enter your username and password to log in.

### Onboarding

- Complete the onboarding process to personalize your learning experience. Provide details such as age, favorite subject, learning goals, hobbies, preferred learning style, and challenges.

### Interactive Chat

- Use the chat interface to interact with the AI teacher. Ask questions, request explanations, and engage in educational dialogues.

### Speech Mode

- Switch to speech mode to interact with the AI teacher using voice commands. Press and hold the microphone button to speak, and release to send the audio.

## Contributing

Contributions are welcome! Please follow these steps to contribute:

1. Fork the repository.
2. Create a new branch (`git checkout -b your-feature-branch`).
3. Make your changes and commit them (`git commit -m 'Add some feature'`).
4. Push to the branch (`git push origin your-feature-branch`).
5. Open a pull request.

## License

This project is licensed under the GNU General Public License v3.0. See the [LICENSE](LICENSE) file for details.

## Contact

If you have any questions or suggestions, feel free to contact the project maintainer:

- Name: Zigao Wang
- Email: a@zigao.wang