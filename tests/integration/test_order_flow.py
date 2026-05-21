import pytest
import requests
import time

class TestOrderFlow:
    """Интеграционные тесты для сквозного процесса заказа"""
    
    BASE_URL_CATALOG = "http://localhost:5001"
    BASE_URL_CART = "http://localhost:5002"
    BASE_URL_ORDERS = "http://localhost:3000"
    BASE_URL_SAGA = "http://localhost:5004"
    
    @pytest.fixture
    def cart_id(self):
        return f"test_cart_{int(time.time())}"
    
    def test_add_to_cart_then_checkout_creates_order(self, cart_id):
        """Интеграционный тест: добавление в корзину → оформление → создание заказа"""
        
        # 1. Добавляем товар в корзину
        add_response = requests.post(
            f"{self.BASE_URL_CART}/cart/add",
            headers={"X-Cart-ID": cart_id, "Content-Type": "application/json"},
            json={"product_id": 1, "product_name": "Test Pizza", "price": 100, "quantity": 2}
        )
        assert add_response.status_code == 201
        cart_data = add_response.json()
        assert cart_data["total"] == 200
        
        # 2. Запускаем Saga оформления заказа
        saga_response = requests.post(
            f"{self.BASE_URL_SAGA}/saga/start",
            json={
                "user_id": "test_user",
                "cart_id": cart_id,
                "address": "Test Address",
                "payment_method": "CARD"
            }
        )
        assert saga_response.status_code == 200
        order_data = saga_response.json()
        assert order_data["success"] is True
        assert order_data["total_amount"] == 200
        
        # 3. Проверяем, что заказ создался в модуле В
        time.sleep(2)  # Ждём асинхронного создания
        orders_response = requests.get(f"{self.BASE_URL_ORDERS}/orders")
        assert orders_response.status_code == 200
        orders = orders_response.json()
        
        # Находим наш заказ
        found = any(o.get("totalAmount") == 200 for o in orders)
        assert found, "Order not found in orders list"
    
    def test_catalog_returns_products(self):
        """Тест: каталог возвращает список товаров"""
        response = requests.get(f"{self.BASE_URL_CATALOG}/products")
        assert response.status_code == 200
        products = response.json()
        assert len(products) > 0
        assert "name" in products[0]
        assert "price" in products[0]
    
    def test_get_cart_returns_empty(self, cart_id):
        """Тест: новая корзина должна быть пустой"""
        response = requests.get(
            f"{self.BASE_URL_CART}/cart",
            headers={"X-Cart-ID": cart_id}
        )
        assert response.status_code == 200
        cart_data = response.json()
        assert cart_data["items"] == []
        assert cart_data["total"] == 0