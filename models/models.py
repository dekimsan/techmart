# models/models.py
from pydantic import BaseModel, Field
from typing import List, Optional, Literal

# Определяем возможные роли пользователей
Role = Literal["admin", "worker", "customer"]

# --- Модели товаров ---
class ProductBase(BaseModel):
    name: str
    description: str
    price: float
    quantity: int = Field(..., ge=0) # Количество не может быть отрицательным

class ProductCreate(ProductBase):
    pass

class Product(ProductBase):
    id: str

# Модель для покупки товара
class ProductPurchase(BaseModel):
    quantity: int = Field(1, gt=0) # Покупатель должен указать количество больше 0

# --- Модели пользователей ---
class UserBase(BaseModel):
    username: str
    role: Role

class UserCreate(UserBase):
    password: str

class UserInDB(UserBase):
    id: str
    hashed_password: str

# Модель для отображения информации о пользователе без хеша пароля
class UserPublic(UserBase):
    id: str

# --- Модели для аутентификации ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None