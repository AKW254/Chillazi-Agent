from sqlalchemy import Column, Integer, String, DateTime,ForeignKey
from datetime import datetime
from app.config.database import Base

class ChatSession(Base):
    __tablename__ = 'chat_sessions'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    session_name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
class ChatMessage(Base):
    __tablename__ = 'chat_messages'

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey('chat_sessions.id'), nullable=False)
    role = Column(String, nullable=False)
    message = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)