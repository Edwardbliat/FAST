from typing import List, Optional
from pydantic import BaseModel



#Задачи
class NoteBase(BaseModel):
    title: str
    description: str | None = None
    text_field_1: str | None = None
    text_field_2: str | None = None
    text_field_3: str | None = None
    text_field_4: str | None = None
    text_field_5: str | None = None
    due_date: str 
     
class NoteID(NoteBase):
    id: int

class Note(NoteBase):
    id: int
    owner_id: int
    
    class Config:
        from_attributes = True


class NoteDel(NoteBase):
    id: int

    
#Пользователь       
class UserBase(BaseModel):
    login_name: str
    
    
class UserEmailCreate(UserBase):
    email: str


class UserCreate(UserBase):
    password: str

        
#Вход
class UserEnter(BaseModel):
    login_name: str
    password: str

class UserLogin(UserEnter):
    login_name: str

class UserID(UserEnter):
    user_id: int
    

class UserResponse(BaseModel):
    user_id: int
    


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    login_name: str | None = None


class User(BaseModel):
    login_name: str
    email: str | None = None

    
class UserInDB(User):
    hashed_password: str

class UserPassword(User):
    password: str
    
    
class LoginForm(BaseModel):
    username: str
    password: str


    
#####################           тест модели


class UserTg(BaseModel):
    tg_id: int
    name_tg: str
    user_name: str