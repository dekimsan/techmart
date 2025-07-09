from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Form 
from models.models import ProductUpdate, Product, ProductCreate, ProductPurchase, UserInDB, Category, CategoryCreate, QuantityUpdate
from database.db import get_all_products_db, save_all_products_db, generate_new_id, get_all_categories_db, save_all_categories_db
from security.security import get_worker_user, get_current_active_user

router = APIRouter(prefix="/api", tags=["Products"])

# --- эндпоинты для категорий ---
@router.post("/products/category/", response_model=Category, status_code=status.HTTP_201_CREATED)
async def create_category(
    category_data: CategoryCreate, 
    current_user: UserInDB = Depends(get_worker_user)
):
    """Создание новой категории товаров (только для админов и работников)."""
    categories = get_all_categories_db()
    
    if any(cat.name.lower() == category_data.name.lower() for cat in categories):
        raise HTTPException(status_code=400, detail="Category with this name already exists")
    
    new_category = Category(name=category_data.name)
    
    categories.append(new_category)
    save_all_categories_db(categories)
    return new_category

@router.get("/products/category/", response_model=List[Category])
async def get_all_categories(
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Получение списка всех созданных категорий."""
    return get_all_categories_db()

@router.get("/products/category/{category_name}", response_model=List[Product])
async def get_products_by_category(
    category_name: str, 
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Получение списка товаров по названию категории."""
    products = get_all_products_db()
    
    filtered_products = [
        p for p in products if p.category.lower() == category_name.lower()
    ]
    
    return filtered_products

# --- Эндпоинты для Товаров ---

@router.get("/products/", response_model=List[Product])
async def get_all_products(current_user: UserInDB = Depends(get_current_active_user)):
    """Все пользователи могут просматривать список товаров."""
    return get_all_products_db()

@router.get("/products/{product_id}", response_model=Product)
async def get_product_by_id(product_id: str, current_user: UserInDB = Depends(get_current_active_user)):
    """Получение одного товара по его ID."""
    products = get_all_products_db()
    product = next((p for p in products if p.id == product_id), None)
    
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product

@router.post("/products/", response_model=Product, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_data: ProductCreate, 
    current_user: UserInDB = Depends(get_worker_user)
):
    """Добавление нового товара."""
    categories = get_all_categories_db()
    if not any(cat.name.lower() == product_data.category.lower() for cat in categories):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category '{product_data.category}' does not exist."
        )

    products = get_all_products_db()
    new_product = Product(
        id=generate_new_id("p", [p.model_dump() for p in products]),
        **product_data.model_dump()
    )
    products.append(new_product)
    save_all_products_db(products)
    return new_product

@router.put("/products/{product_id}/update-quantity", response_model=Product)
async def update_product_quantity(
    product_id: str, 
    quantity_update: QuantityUpdate, 
    current_user: UserInDB = Depends(get_worker_user)
):
    """Изменение количества товара."""
    products = get_all_products_db()
    product_to_update = next((p for p in products if p.id == product_id), None)
    if not product_to_update:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    new_quantity = product_to_update.quantity + quantity_update.change
    if new_quantity < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Product quantity cannot be negative."
        )
    
    product_to_update.quantity = new_quantity
    save_all_products_db(products)
    return product_to_update

@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(product_id: str, current_user: UserInDB = Depends(get_worker_user)):
    """Удаление товара."""
    products = get_all_products_db()
    product_to_delete = next((p for p in products if p.id == product_id), None)
    
    if not product_to_delete:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        
    products.remove(product_to_delete)
    save_all_products_db(products)
    return

@router.post("/products/{product_id}/purchase", response_model=Product)
async def purchase_product(
    product_id: str,
    purchase: ProductPurchase,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Покупка (бронирование) товара покупателем."""
    if current_user.role != "customer":
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only customers can purchase products")

    products = get_all_products_db()
    product_to_purchase = next((p for p in products if p.id == product_id), None)

    if not product_to_purchase:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    if product_to_purchase.quantity < purchase.quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Not enough items in stock. Available: {product_to_purchase.quantity}."
        )
    
    product_to_purchase.quantity -= purchase.quantity
    save_all_products_db(products)
    
    return product_to_purchase

# --- Эндпоинты для РЕДАКТИРОВАНИЯ ---

@router.patch("/products/{product_id}", response_model=Product)
async def edit_product(
    product_id: str,
    product_update: ProductUpdate,
    current_user: UserInDB = Depends(get_worker_user)
):
    """Основной эндпоинт редактирования данных товара (JSON)."""
    products = get_all_products_db()
    product_to_edit = next((p for p in products if p.id == product_id), None)

    if not product_to_edit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    update_data = product_update.model_dump(exclude_none=True)

    # Проверку категории проводим только если она есть в данных для обновления
    if "category" in update_data:
        categories = get_all_categories_db()
        if not any(cat.name.lower() == update_data["category"].lower() for cat in categories):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category '{update_data['category']}' does not exist."
            )
            
    # Проверку количества проводим только если оно есть в данных для обновления
    if "quantity" in update_data and update_data["quantity"] < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product quantity cannot be negative."
        )

    for key, value in update_data.items():
        setattr(product_to_edit, key, value)

    save_all_products_db(products)
    return product_to_edit

def get_product_update_from_form(
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    price: Optional[float] = Form(None),
    category: Optional[str] = Form(None),
    quantity: Optional[int] = Form(None)
) -> ProductUpdate:
    """Собирает данные из формы в модель ProductUpdate, отбрасывая пустые значения."""
    # Используем model_dump с exclude_none=True, чтобы передать в основной эндпоинт
    # только те поля, которые были реально переданы в форме.
    return ProductUpdate(
        name=name,
        description=description,
        price=price,
        category=category,
        quantity=quantity
    )

@router.patch("/products/{product_id}/form", response_model=Product)
async def edit_product_form(
    product_id: str,
    product_update: ProductUpdate = Depends(get_product_update_from_form),
    current_user: UserInDB = Depends(get_worker_user)
):
    """Альтернативное редактирование данных товара через form-data."""
    # Теперь этот эндпоинт просто вызывает основной, передавая ему подготовленные данные
    return await edit_product(
        product_id=product_id,
        product_update=product_update,
        current_user=current_user
    )
