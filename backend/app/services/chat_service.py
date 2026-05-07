from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from app.models.chat import ChatSession, ChatMessage

class ChatService:
    def __init__(self, db: Session):
        self.db = db

    def get_or_create_session(
        self,
        user_id: int,
        session_id: Optional[int] = None,
        session_name: Optional[str] = None,
    ) -> ChatSession:
        if session_id is not None:
            existing = (
                self.db.query(ChatSession)
                .filter(ChatSession.id == session_id, ChatSession.user_id == user_id)
                .first()
            )
            if existing:
                return existing

        if not session_name:
            session_name = f"Chat Session {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"

        return self.create_chat_session(user_id=user_id, session_name=session_name)

    def create_chat_session(self, user_id: int, session_name: str) -> ChatSession:
        chat_session = ChatSession(user_id=user_id, session_name=session_name)
        self.db.add(chat_session)
        self.db.commit()
        self.db.refresh(chat_session)
        return chat_session

    def add_message(self, session_id: int, role: str, message: str) -> ChatMessage:
        chat_message = ChatMessage(session_id=session_id, role=role, message=message)
        self.db.add(chat_message)
        self.db.commit()
        self.db.refresh(chat_message)
        return chat_message

    def get_recent_messages(self, session_id: int, limit: int = 10) -> list[ChatMessage]:
        return self.db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(ChatMessage.timestamp.desc()).limit(limit).all()
       
