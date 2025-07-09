# routers/users.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from models.models import UserPublic, UserInDB, UserSearch
from database.db import get_all_users_db, save_all_users_db, find_user_by_id
from security.security import get_admin_user, get_worker_user, get_current_active_user

router = APIRouter(prefix="/api", tags=["Users"])

@router.get("/user/", response_model=List[UserPublic])
async def read_users(current_user: UserInDB = Depends(get_current_active_user)):
    """
    Получение списка пользователей в зависимости от роли:
    - Админ: видит всех.
    - Работник: видит работников и покупателей.
    - Покупатель: доступ запрещен.
    """
    users = get_all_users_db()
    
    if current_user.role == "admin":
        return [UserPublic.model_validate(user.model_dump()) for user in users]
    
    if current_user.role == "worker":
        filtered_users = [user for user in users if user.role in ["worker", "customer"]]
        return [UserPublic.model_validate(u.model_dump()) for u in filtered_users]

        
    # Покупателям доступ запрещен
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

@router.get("/user/{user_id}", response_model=UserPublic)
async def read_user(user_id: str, current_user: UserInDB = Depends(get_current_active_user)):
    """
    Получение информации о конкретном пользователе.
    Доступ регулируется ролями.
    """
    user = find_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Админ видит всех
    if current_user.role == "admin":
        return UserPublic.model_validate(user.model_dump())
    
    # Работник видит работников и покупателей
    if current_user.role == "worker" and user.role in ["worker", "customer"]:
         return UserPublic.model_validate(user.model_dump())
         
    # Если не админ и не работник с нужными правами
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")


@router.delete("/delete-user/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: str, current_user: UserInDB = Depends(get_current_active_user)):
    """
    Удаление пользователя.
    - Админ: может удалить любого.
    - Работник: может удалить только покупателя.
    """
    users = get_all_users_db()
    user_to_delete = find_user_by_id(user_id)

    if not user_to_delete:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # Запрещаем удалять самого себя
    if user_to_delete.id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot delete yourself")

    can_delete = False
    if current_user.role == "admin":
        can_delete = True
    elif current_user.role == "worker" and user_to_delete.role == "customer":
        can_delete = True
    
    if not can_delete:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions to delete this user")
        
    users_after_deletion = [user for user in users if user.id != user_id]
    save_all_users_db(users_after_deletion)
    return

# routers/users.py (или где находится ваш эндпоинт)

@router.post("/user/search", response_model=List[UserPublic])
async def search_users(
    search_criteria: UserSearch,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Поиск пользователей по критериям (id, username, role, универсальный поиск).
    Права доступа применяются в зависимости от роли текущего пользователя.
    """
    if current_user.role == "customer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Customers cannot search for users."
        )

    all_users = get_all_users_db()
    if current_user.role == "admin":
        allowed_users = all_users
    else:
        allowed_users = [
            user for user in all_users if user.role in ["worker", "customer"]
        ]

    search_results = allowed_users
    if search_criteria.search:
        search_term = search_criteria.search.lower()
        search_results = [
            user for user in search_results 
            if search_term in user.username.lower() or search_term in user.id.lower() or search_term in user.role.lower()
        ]

    if search_criteria.id:
        search_results = [
            user for user in search_results if search_criteria.id == user.id
        ]

    if search_criteria.username:
        search_term = search_criteria.username.lower()
        search_results = [
            user for user in search_results if search_term in user.username.lower()
        ]
        
    if search_criteria.role:
        search_results = [
            user for user in search_results if search_criteria.role == user.role
        ]

    return [UserPublic.model_validate(user.model_dump()) for user in search_results]


