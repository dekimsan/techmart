from datetime import timedelta
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm

from models.models import UserCreate, UserPublic, Token, Role
from database.db import get_all_users_db, save_all_users_db, find_user_by_username, generate_new_id, UserInDB
from security.security import get_password_hash, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, verify_password

router = APIRouter(prefix="/api", tags=["Authentication"])

def register_user(user_data: UserCreate, role: Role, id_prefix: str):
    """Общая функция для регистрации пользователя."""
    if find_user_by_username(user_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this username already exists"
        )
    
    users = get_all_users_db()
    
    new_user = UserInDB(
        id=generate_new_id(id_prefix, [u.model_dump() for u in users]),
        username=user_data.username,
        hashed_password=get_password_hash(user_data.password),
        role=role
    )
    
    users.append(new_user)
    save_all_users_db(users)
    return UserPublic(id=new_user.id, username=new_user.username, role=new_user.role)

@router.post("/admin-reg", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
async def register_admin_user(user: UserCreate):
    return register_user(user, "admin", "a")

@router.post("/worker-reg", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
async def register_worker_user(user: UserCreate):
    return register_user(user, "worker", "w")

@router.post("/customer-reg", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
async def register_customer_user(user: UserCreate):
    return register_user(user, "customer", "c")

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = find_user_by_username(form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}