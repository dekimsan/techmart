from pydantic import BaseModel, Field
from typing import List, Optional, Literal

# Определяем возможные роли пользователей
Role = Literal["admin", "worker", "customer"]

# --- БАЗОВЫЕ МОДЕЛИ ---
# Эти модели должны быть определены первыми, так как другие от них наследуются

class ProductBase(BaseModel):
    name: str
    description: str
    price: float
    category: str
    quantity: int = Field(..., ge=0)

class UserBase(BaseModel):
    username: str
    role: Role

class CategoryBase(BaseModel):
    name: str

# --- МОДЕЛИ ТОВАРОВ ---
# Эти модели зависят от ProductBase

class ProductCreate(ProductBase):
    pass

class Product(ProductBase):
    id: str

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    category: Optional[str] = None
    quantity: Optional[int] = None

class QuantityUpdate(BaseModel):
    change: int

class ProductPurchase(BaseModel):
    quantity: int = Field(1, gt=0)

# --- МОДЕЛИ ПОЛЬЗОВАТЕЛЕЙ ---
# Эти модели зависят от UserBase

class UserCreate(UserBase):
    password: str

class UserInDB(UserBase):
    id: str
    hashed_password: str

class UserPublic(UserBase):
    id: str

# --- МОДЕЛИ КАТЕГОРИЙ ---
# Эти модели зависят от CategoryBase

class CategoryCreate(CategoryBase):
    pass

class Category(CategoryBase):
    pass

# --- МОДЕЛИ ДЛЯ АУТЕНТИФИКАЦИИ ---

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
