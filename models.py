from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship

db = SQLAlchemy()

class User(db.Model):
    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    name = Column(String(120), nullable=False)
    age = Column(Integer, nullable=True)
    favorite_subject = Column(String(120), nullable=True)
    learning_goals = Column(Text, nullable=True)
    hobbies = Column(Text, nullable=True)
    preferred_learning_style = Column(Text, nullable=True)
    challenges = Column(Text, nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Conversation(db.Model):
    __bind_key__ = 'conversations'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    messages = Column(Text, nullable=False)

    user = relationship('User', backref='conversations')