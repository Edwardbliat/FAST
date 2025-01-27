from fastapi import FastAPI, Depends, HTTPException, File, UploadFile, status, BackgroundTasks
from sqlalchemy.orm import Session
import crud, models, schemas
from database import SessionLocal, engine
import os
import shutil
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import datetime, timedelta, timezone
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta, timezone
from fastapi.security import OAuth2PasswordBearer
from typing import Optional
from jose import JWTError


SECRET_KEY = "979683579c45c4ca9b3a9657e98ad3bb5673df79385311a578ca82b71cd611e6"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


models.Base.metadata.create_all(bind=engine)
app = FastAPI()

UPLOAD_DIR = "uploaded_files"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



####Hash content
# ----- Хелпер-функции -----
def get_password_hash(password: str) -> str:
    """Хэшируем пароль."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверяем совпадение пароля с хэшем."""
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Создаём JWT-токен для аутентификации."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_user(db, login_name: str):
    """Находим пользователя в базе данных по `login_name`."""
    return db.query(models.User).filter(models.User.login_name == login_name).first()

def authenticate_user(db, login_name: str, password: str):
    """Аутентифицируем пользователя, сверяя пароль и хэш."""
    user = get_user(db, login_name)
    if not user or not verify_password(password, user.password):
        return None
    return user



# ----- Эндпоинты приложения -----

@app.post("/register/", response_model=schemas.User)
def register_user(user: schemas.UserPassword, db: Session = Depends(get_db)):
    """Регистрация нового пользователя."""
    # Проверяем, существует ли пользователь с таким `login_name`
    db_user = get_user(db, user.login_name)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Login name already registered",
        )

    # Создаем пользователя и сохраняем в базу данных
    hashed_password = get_password_hash(user.password)
    db_user = models.User(login_name=user.login_name, email=user.email, password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


@app.post("/token", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    print(f"Полученные данные: username={form_data.username}, password={form_data.password}")
    
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect login name or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.login_name}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me", response_model=int)  # Указываем, что возвращаем только int
def read_users_me(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Получение id текущего пользователя."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        login_name: str = payload.get("sub")
        if login_name is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = get_user(db, login_name=login_name)
    if user is None:
        raise credentials_exception

    # Возвращаем только id пользователя
    return user.id

####################################################

@app.post('/add_usertg/', response_model=schemas.UserTg)
def add_new_tg_user(user: schemas.UserTg, db: Session = Depends(get_db)):
    user_tg_db = crud.check_usertg(db, user_tg=user.tg_id)
    if user_tg_db:
        raise HTTPException(status_code=404, detail='Такой пользователь уже существует')
    add_user_tg_db = crud.reg_usertg(db, user=user)
    return add_user_tg_db


####################################################
@app.post("/registration_username", response_model=schemas.UserBase)
def add_new_username(user: schemas.UserBase, db: Session = Depends(get_db)):
    db_user = crud.check_username(db, name=user.name)
    if db_user:
        raise HTTPException(status_code=400, detail='Такой пользователь уже существует')
    return crud.add_new_username(db=db, user=user)


#Создание задачи
@app.post('/create_note/{owner_id}', response_model=schemas.NoteID)
def add_new_note_endpoint(note: schemas.NoteBase, owner_id: int, db: Session = Depends(get_db)):
    add_note = crud.add_new_note(db=db, note=note, owner_id=owner_id)
    if not add_note:
        raise HTTPException(status_code=400, detail='Такой задачи не существует. Проверьте свои данные')
    # Возвращаем ID новой задачи, используя объект NoteID
    db_note = crud.get_note_id(db=db, title=note.title)
    return db_note



#Регистрация пользователя
@app.post('/reg_newuser/', response_model=schemas.UserCreate)
def reg_newuser(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.check_created_user(db=db, login_name=user.login_name)
    if db_user:
        raise HTTPException(status_code=400, detail='Такой пользователь уже существует')
    return crud.reg_user(db=db, user=user)


#Вход пользователя
@app.post('/enter_user/', response_model=schemas.UserResponse)
def enter_user(user: schemas.UserEnter, db: Session = Depends(get_db)):
    db_user = crud.db_enter_user(db=db, user=user)
    if not db_user:
        raise HTTPException(status_code=400, detail='Такого пользователя не существует. Проверьте свои данные')
    return crud.db_get_id_by_login(db=db, login_name=user.login_name)


#Пользователь получает список своих задач
@app.get("/tasks/{user_id}")
def get_tasks(user_id, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return db_user.notes


#Удаление задачи
@app.delete('/task_delete/{note_id}')
def note_delete(note_id: int, db: Session = Depends(get_db)):
    db_note = crud.get_note_for_del(db=db, note=note_id)
    db.delete(db_note)
    db.commit()
    db.refresh
    return {'message': f'Задача {note_id} успешно удалена'}


#Получаем задачу пользователя по выбранной дате
@app.get('/tasks/{user_id}/{note_date}')
def get_user_notes_cal(user_id: int, note_date: str , db: Session = Depends(get_db)):
    return crud.get_notes_cal(db=db, user_id=user_id, note_date=note_date)


#Получаем выбранную дату для редактирования
@app.get('/task_edit/{owner_id}/{note_id}')
def get_note_for_edit(owner_id: str, note_id: str, db: Session = Depends(get_db)):
    return crud.get_notes_for_edit(db=db, owner_id=owner_id, note_id=note_id)


#Редактируем конкретную задачу через редактор
@app.post('/task_edit/{note_id}', response_model = schemas.NoteBase)
def edit_note(note_id: str, note_data: schemas.NoteBase , db:Session = Depends(get_db)):
    return crud.edit_note_add_db(db=db, note_id=note_id, note_data=note_data)


#Загрузка файла
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Получение и сохранение файла"""
    # Сохраняем файл в директории
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())

    return {"message": "Файл успешно загружен", "filename": file.filename}

@app.delete("/delete/{filename}")
async def delete_file(filename: str):
    """Удаление файла из директории"""
    file_path = os.path.join(UPLOAD_DIR, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        return {"message": f"Файл '{filename}' успешно удален."}
    else:
        raise HTTPException(status_code=404, detail="Файл не найден.")
    
    
@app.post("/upload/{username}/{task_id}")
async def upload_file(username: str, task_id: str, file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, username, task_id, file.filename)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)  # Создает директорию для пользователя и задачи
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())
    return {"filename": file.filename}

@app.get("/files/{username}/{task_id}")
async def get_files(username: str, task_id: str):
    task_dir = os.path.join(UPLOAD_DIR, username, task_id)
    if os.path.exists(task_dir):
        files = os.listdir(task_dir)
        return {"files": files}
    return {"files": []}

@app.delete("/files/{username}/{task_id}/{filename}")
async def delete_file(username: str, task_id: str, filename: str):
    file_path = os.path.join(UPLOAD_DIR, username, task_id, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        return {"message": "File deleted successfully"}
    return {"error": "File not found"}


@app.delete("/task/{username}/{task_id}")
async def delete_task(username: str, task_id: str, db: Session = Depends(get_db)):
    """
    Удалить задачу и папку с файлами, связанной с задачей.
    """
    task_dir = os.path.join(UPLOAD_DIR, username, task_id)
    
    # Предположим, здесь вы удаляете задачу из базы данных (замените на логику своей БД)
    task = db.query(models.Note).filter(models.Note.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена.")

    db.delete(task)  # Удалить задачу из базы данных
    db.commit()

    # Удаление папки с файлами, связанной с задачей, если она существует
    if os.path.exists(task_dir):
        shutil.rmtree(task_dir)
        return {"message": f"Задача '{task_id}' и соответствующая папка были успешно удалены."}
    
    return {"message": f"Задача '{task_id}' была удалена, но папка не найдена."}