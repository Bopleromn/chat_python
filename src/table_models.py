from db import Base, engine
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship


class Users(Base):
    __tablename__ = 'users'

    id: int = Column(Integer, primary_key=True,
                     autoincrement=True, nullable=False)
    email: str = Column(String, unique=True, nullable=False)
    password: str = Column(String, nullable=False)
    name: str = Column(String, nullable=False)
    age: int = Column(Integer, nullable=False)
    photo: str = Column(String, nullable=False)
    last_seen: str = Column(String, nullable=False)


class VerificationCodes(Base):
    __tablename__ = 'verification_codes'

    id: int = Column(Integer, primary_key=True, unique=True)
    email: str = Column(String, unique=True, nullable=False)
    verification_code: int = Column(Integer, nullable=False)


class ChatMessages(Base):
    __tablename__ = 'chat_messages'

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    room_id: int = Column(Integer, nullable=False)
    user_id: int = Column(Integer, ForeignKey('users.id'), nullable=False)
    message: str = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)

    user = relationship('Users', backref='chat_messages')


class ChatRooms(Base):
    __tablename__ = 'chat_rooms'

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    room_id: int = Column(Integer, nullable=False)
    user_id: int = Column(Integer, ForeignKey('users.id'), nullable=False)
    last_message: str = Column(String, nullable=True)

    user = relationship('Users', backref='chat_rooms')


# line to create all tables, if they don't already exist
Base.metadata.create_all(bind=engine)
