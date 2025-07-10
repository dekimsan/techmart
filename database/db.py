import json
from typing import List, Dict, Any, Optional
from models.models import UserInDB, Product, Category

# Пути к файлам данных
USERS_DB_PATH = "database/users.json"
PRODUCTS_DB_PATH = "database/products.json"
CATEGORIES_DB_PATH = "database/categories.json" 

# --- Функции для работы с JSON ---
def read_data(path: str) -> List[Dict[str, Any]]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def write_data(path: str, data: List[Dict[str, Any]]):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

# --- Генерация ID ---
def generate_new_id(prefix: str, items: List[Dict[str, Any]]) -> str:
    """Генерирует новый ID с инкрементом."""
    if not items:
        return f"{prefix}1"
    
    max_id = 0
    for item in items:
        if item['id'].startswith(prefix):
            try:
                # Извлекаем числовую часть ID
                num_part = int(item['id'][len(prefix):])
                if num_part > max_id:
                    max_id = num_part
            except (ValueError, IndexError):
                continue
                
    return f"{prefix}{max_id + 1}"

# --- Функции для пользователей ---
def get_all_users_db() -> List[UserInDB]:
    users_data = read_data(USERS_DB_PATH)
    return [UserInDB(**user) for user in users_data]

def save_all_users_db(users: List[UserInDB]):
    write_data(USERS_DB_PATH, [user.model_dump() for user in users])

def find_user_by_username(username: str) -> Optional[UserInDB]:
    users = get_all_users_db()
    for user in users:
        if user.username == username:
            return user
    return None

def find_user_by_id(user_id: str) -> Optional[UserInDB]:
    users = get_all_users_db()
    for user in users:
        if user.id == user_id:
            return user
    return None

# --- Функции для товаров ---
def get_all_products_db() -> List[Product]:
    products_data = read_data(PRODUCTS_DB_PATH)
    return [Product(**product) for product in products_data]

def save_all_products_db(products: List[Product]):
    write_data(PRODUCTS_DB_PATH, [p.model_dump() for p in products])

def get_all_categories_db() -> List[Category]:
    categories_data = read_data(CATEGORIES_DB_PATH)
    return [Category(**cat) for cat in categories_data]

def save_all_categories_db(categories: List[Category]):
    write_data(CATEGORIES_DB_PATH, [cat.model_dump() for cat in categories])