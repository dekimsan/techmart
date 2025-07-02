# tests/test_api.py
import pytest
from fastapi.testclient import TestClient
from main import app
import os
import json

# Используем TestClient для отправки запросов к API
client = TestClient(app)

# --- Вспомогательные функции для тестов ---
@pytest.fixture(scope="module", autouse=True)
def setup_and_teardown():
    # Перед тестами создаем пустые файлы, чтобы не влиять на реальные данные
    with open("database/users.json", "w") as f:
        json.dump([], f)
    with open("database/products.json", "w") as f:
        json.dump([], f)
    
    yield # Здесь выполняются тесты
    
    # После тестов очищаем файлы
    os.remove("database/users.json")
    os.remove("database/products.json")


def register_user(username, password, role):
    endpoint_map = {
        "admin": "/api/admin-reg",
        "worker": "/api/worker-reg",
        "customer": "/api/customer-reg",
    }
    response = client.post(endpoint_map[role], json={"username": username, "password": password, "role": role})
    assert response.status_code == 201
    return response.json()

def get_token(username, password):
    response = client.post("/api/token", data={"username": username, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


# --- Тесты ---
def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the Technique Store API!"}

def test_user_registration():
    # Регистрируем админа, работника и покупателя
    admin = register_user("testadmin", "adminpass", "admin")
    assert admin["username"] == "testadmin"
    assert admin["id"].startswith("a")

    worker = register_user("testworker", "workerpass", "worker")
    assert worker["username"] == "testworker"
    assert worker["id"].startswith("w")
    
    customer = register_user("testcustomer", "customerpass", "customer")
    assert customer["username"] == "testcustomer"
    assert customer["id"].startswith("c")

def test_login_and_token():
    register_user("loginuser", "loginpass", "customer")
    token = get_token("loginuser", "loginpass")
    assert isinstance(token, str)

def test_product_management_as_worker():
    # Регистрируем работника и получаем токен
    register_user("prodworker", "prodpass", "worker")
    token = get_token("prodworker", "prodpass")
    headers = {"Authorization": f"Bearer {token}"}

    # Создаем товар
    product_data = {"name": "Laptop", "description": "A cool laptop", "price": 1200.50, "quantity": 10}
    response = client.post("/api/products/", headers=headers, json=product_data)
    assert response.status_code == 201
    product = response.json()
    assert product["name"] == "Laptop"
    assert product["id"].startswith("p")
    product_id = product["id"]

    # Проверяем, что товар появился в общем списке
    response = client.get("/api/products/", headers=headers)
    assert response.status_code == 200
    assert any(p["id"] == product_id for p in response.json())

    # Удаляем товар
    response = client.delete(f"/api/products/{product_id}", headers=headers)
    assert response.status_code == 204

def test_access_control_users_list():
    # Создаем пользователей
    register_user("admin2", "pass", "admin")
    register_user("worker2", "pass", "worker")
    register_user("customer2", "pass", "customer")
    
    # Получаем их токены
    admin_token = get_token("admin2", "pass")
    worker_token = get_token("worker2", "pass")
    customer_token = get_token("customer2", "pass")
    
    # 1. Админ должен видеть всех
    response = client.get("/api/user/", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    users = response.json()
    assert len(users) >= 3 # >= потому что предыдущие тесты тоже создавали юзеров

    # 2. Работник видит работников и покупателей
    response = client.get("/api/user/", headers={"Authorization": f"Bearer {worker_token}"})
    assert response.status_code == 200
    roles = {user['role'] for user in response.json()}
    assert "admin" not in roles
    assert "worker" in roles
    assert "customer" in roles

    # 3. Покупатель не должен видеть список
    response = client.get("/api/user/", headers={"Authorization": f"Bearer {customer_token}"})
    assert response.status_code == 403

def test_customer_purchase_flow():
    # Создаем работника и покупателя
    register_user("seller1", "pass", "worker")
    register_user("buyer1", "pass", "customer")
    worker_token = get_token("seller1", "pass")
    customer_token = get_token("buyer1", "pass")
    
    # Работник добавляет товар
    product_data = {"name": "Mouse", "description": "Gaming mouse", "price": 50.0, "quantity": 5}
    response = client.post("/api/products/", headers={"Authorization": f"Bearer {worker_token}"}, json=product_data)
    product_id = response.json()["id"]

    # Покупатель покупает 2 шт.
    purchase_data = {"quantity": 2}
    response = client.post(f"/api/products/{product_id}/purchase", headers={"Authorization": f"Bearer {customer_token}"}, json=purchase_data)
    assert response.status_code == 200
    assert response.json()["quantity"] == 3 # 5 - 2 = 3

    # Попытка купить больше, чем есть в наличии
    purchase_data_fail = {"quantity": 4}
    response = client.post(f"/api/products/{product_id}/purchase", headers={"Authorization": f"Bearer {customer_token}"}, json=purchase_data_fail)
    assert response.status_code == 400
    assert "Not enough items in stock" in response.json()["detail"]