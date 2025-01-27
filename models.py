from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, BigInteger, DateTime, Text
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime



class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    login_name = Column(String, nullable=True)
    email = Column(String, index=True, nullable=True)
    password = Column(String, nullable=True)
    tg_id = Column(BigInteger, nullable=True)
    name_tg = Column(String, nullable=True)
    user_name = Column(String, nullable=True)
    is_online = Column(Boolean, default=False)
    last_password_update = Column(DateTime, default=datetime.utcnow)
    
    notes = relationship("Note", back_populates="owner")
    tg_account = relationship('TGUser', back_populates='user_tg')


class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True)
    title = Column(String, index=True)
    description = Column(String, index=True)
    text_field_1 = Column(String, index=True, nullable=True)
    text_field_2 = Column(String, index=True, nullable=True)
    text_field_3 = Column(String, index=True, nullable=True)
    text_field_4 = Column(String, index=True, nullable=True)
    text_field_5 = Column(String, index=True, nullable=True)
    due_date = Column(String, nullable=False)  # Дата, когда нужно выполнить задачу
    
    
    created_at = Column(DateTime, default=datetime.utcnow)  # Время создания задачи
    owner_id = Column(Integer, ForeignKey("users.id"))
    
    owner = relationship("User", back_populates="notes")




 
class TGUser(Base):
    __tablename__ = 'tgusers'
    
    id = Column(Integer, primary_key=True)
    tg_id = Column(BigInteger, nullable=False)
    name_tg = Column(String(20), nullable=True)
    tg_owner = Column(Integer, ForeignKey('users.id'))
    
    user_tg = relationship('User', back_populates='tg_account')    
    
    

    