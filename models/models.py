from pydantic import BaseModel, Field
from typing import Optional, Literal

# Определяем возможные роли пользователей
Role = Literal["admin", "worker", "customer"]

# --- МОДЕЛИ ТОВАРОВ ---
class ProductBase(BaseModel):
    name: str
    description: str
    price: float
    category: str
    quantity: int = Field(..., ge=0)

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

class UserBase(BaseModel):
    username: str
    role: Role

class UserCreate(BaseModel):
    username: str
    password: str

class UserInDB(UserBase):
    id: str
    hashed_password: str

class UserPublic(UserBase):
    id: str

# --- МОДЕЛИ КАТЕГОРИЙ ---
class CategoryBase(BaseModel):
    name: str

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

# --- Модели поиска ---

class ProductSearch(BaseModel):
    search: Optional[str] = None
    id: Optional[str] = None
    name: Optional[str] = None
    category: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None

class UserSearch(BaseModel):
    search: Optional[str] = None
    id: Optional[str] = None
    username: Optional[str] = None
    role: Optional[Role] = None
