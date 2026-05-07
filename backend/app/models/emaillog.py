from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime,Boolean,ForeignKey
from sqlalchemy.orm import relationship
from app.config.database import Base

class EmailLog(Base):
    __tablename__ = 'email_logs'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    subject = Column(String)
    event_type = Column(String)  # order_created, order_cancelled
    status = Column(String)      # sent, failed
    message_id = Column(String, nullable=True)
    sent_at = Column(DateTime, default=datetime.utcnow)
    opened = Column(Boolean, default=False)
    clicked = Column(Boolean, default=False)
    user = relationship("User", back_populates="email_logs")