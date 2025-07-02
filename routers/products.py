# routers/products.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status

from models.models import Product, ProductCreate, ProductPurchase, UserInDB
from database.db import get_all_products_db, save_all_products_db, generate_new_id
from security.security import get_worker_user, get_current_active_user

router = APIRouter(prefix="/api/products", tags=["Products"])

@router.get("/", response_model=List[Product])
async def get_all_products(current_user: UserInDB = Depends(get_current_active_user)):
    """Все пользователи могут просматривать список товаров."""
    return get_all_products_db()

@router.post("/", response_model=Product, status_code=status.HTTP_201_CREATED)
async def create_product(product_data: ProductCreate, current_user: UserInDB = Depends(get_worker_user)):
    """Добавление нового товара (только для админов и работников)."""
    products = get_all_products_db()
    new_product = Product(
        id=generate_new_id("p", [p.model_dump() for p in products]),
        **product_data.model_dump()
    )
    products.append(new_product)
    save_all_products_db(products)
    return new_product

@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(product_id: str, current_user: UserInDB = Depends(get_worker_user)):
    """Удаление товара (только для админов и работников)."""
    products = get_all_products_db()
    product_to_delete = next((p for p in products if p.id == product_id), None)
    
    if not product_to_delete:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        
    products.remove(product_to_delete)
    save_all_products_db(products)
    return

@router.post("/{product_id}/purchase", response_model=Product)
async def purchase_product(
    product_id: str,
    purchase: ProductPurchase,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Покупка (бронирование) товара покупателем.
    Количество товара уменьшается.
    """
    if current_user.role != "customer":
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only customers can purchase products")

    products = get_all_products_db()
    product_to_purchase = next((p for p in products if p.id == product_id), None)

    if not product_to_purchase:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    if product_to_purchase.quantity < purchase.quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Not enough items in stock. Available: {product_to_purchase.quantity}. Please check other products."
        )
    
    product_to_purchase.quantity -= purchase.quantity
    save_all_products_db(products)
    
    return product_to_purchase