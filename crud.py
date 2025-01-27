from sqlalchemy.orm import Session
import models, schemas
from sqlalchemy import select, update
from fastapi import HTTPException
from fastapi import Depends, HTTPException, status
from typing import Optional






#Регистрация пользователя
def reg_user(db: Session, user: schemas.UserCreate):
    db_user = models.User(login_name=user.login_name, password=user.password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def reg_usertg(db: Session, user: schemas.UserTg):
    add_user_db = models.User(tg_id=user.tg_id, name_tg=user.name_tg, user_name=user.user_name)
    db.add(add_user_db)
    db.commit()
    db.refresh(add_user_db)
    return add_user_db

def check_usertg(db: Session, user_tg: int):
    return db.query(models.User).filter(models.User.tg_id == user_tg).first()

#Проверка на существование пользователя
def check_created_user(db: Session, login_name: str):
    return db.query(models.User).filter(models.User.login_name == login_name ).first()


#Добавление задачи в БД
def add_new_note(db: Session, note: schemas.NoteBase, owner_id: int):
    db_note = models.Note(**note.dict(), owner_id=owner_id)
    db.add(db_note)
    db.commit()
    db.refresh(db_note)  # Получаем данные обновленного объекта, включая ID
    return db_note


def get_note_id(db: Session, title: str):
    db_note_title = db.query(models.Note).filter(models.Note.title == title).first()
    if not db_note_title:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    # Возвращаем объект NoteID с ID задачи и другой необходимой информацией
    return schemas.NoteID(
        id=db_note_title.id,
        title=db_note_title.title,
        description=db_note_title.description,
        text_field_1=db_note_title.text_field_1,
        text_field_2=db_note_title.text_field_2,
        text_field_3=db_note_title.text_field_3,
        text_field_4=db_note_title.text_field_4,
        text_field_5=db_note_title.text_field_5,
        due_date=db_note_title.due_date
    )


#Для входа в свой аккаунт
def db_enter_user(db: Session, user: schemas.UserEnter):
    return db.query(models.User).filter(models.User.login_name == user.login_name,
                                        models.User.password == user.password).first()
    
   
#Достаем ID пользователя
def db_get_id_by_login(db: Session, login_name: str):
    db_user = db.query(models.User).filter(models.User.login_name == login_name).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return schemas.UserResponse(user_id=db_user.id)


#Удаляем определенную задачу у пользователя
def get_note_for_del(db: Session, note: schemas.NoteDel):
    db_note = db.query(models.Note).filter(models.Note.id == note).first()
    if not db_note:
        raise HTTPException(status_code=404, detail='Такой задачи не существует')
    return db_note


#Достаем задачи пользователя из календаря
def get_notes_cal(db: Session, user_id: int, note_date: str):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    tasks = db.query(models.Note).filter(
        models.Note.owner_id == user_id,
        models.Note.due_date == note_date
    ).all()

    if not tasks:
        raise HTTPException(status_code=404)
    
    return tasks


#Функция получения задачи для редактирования
def get_notes_for_edit(db: Session, owner_id: str, note_id: str):
    owner = db.query(models.User).filter(models.User.id == owner_id).first()
    if not owner:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    note = db.query(models.Note).filter(models.Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    return note



#Функция редактирования задачи
def edit_note_add_db(db: Session, note_id: str, note_data: schemas.NoteBase):
    note = db.query(models.Note).filter(models.Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    note.title = note_data.title
    note.description = note_data.description
    note.text_field_1 = note_data.text_field_1
    note.text_field_2 = note_data.text_field_2
    note.text_field_3 = note_data.text_field_3
    note.text_field_4 = note_data.text_field_4
    note.text_field_5 = note_data.text_field_5
    note.due_date = note_data.due_date
    db.commit()
    return note


