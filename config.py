class Config:
    SECRET_KEY = 'your_secret_key'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///students.db'
    SQLALCHEMY_BINDS = {
        'conversations': 'sqlite:///conversations.db'
    }
    SESSION_TYPE = 'filesystem'