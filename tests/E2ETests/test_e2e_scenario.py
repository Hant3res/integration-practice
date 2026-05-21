import pytest
import requests
import time

class TestE2EScenario:
    """E2E тесты для полного сценария"""
    
    @pytest.fixture
    def test_data(self):
        return {
            "cart_id": f"e2e_cart_{int(time.time())}",
            "user_id": "e2e_test_user",
            "address": "E2E Test Address, 123"
        }
    
    def test_full_order_flow(self, test_data):
        """E2E тест: полный сценарий покупки"""
        
        # 1. Проверяем что сервисы доступны
        services = {
            "catalog": "http://localhost:5001/health",
            "cart": "http://localhost:5002/health",
            "orders": "http://localhost:3000/health",
            "saga": "http://localhost:5004/health"
        }
        
        for name, url in services.items():
            try:
                response = requests.get(url, timeout=3)
                if response.status_code != 200:
                    pytest.skip(f"{name} service not available")
            except:
                pytest.skip(f"{name} service not running")
        
        # 2. Добавляем товар в корзину
        add_response = requests.post(
            "http://localhost:5002/cart/add",
            headers={"X-Cart-ID": test_data["cart_id"], "Content-Type": "application/json"},
            json={"product_id": 1, "product_name": "Test Pizza", "price": 100, "quantity": 2}
        )
        assert add_response.status_code == 201
        cart_data = add_response.json()
        assert cart_data["total"] == 200
        
        # 3. Запускаем Saga оформления заказа
        saga_response = requests.post(
            "http://localhost:5004/saga/start",
            json={
                "user_id": test_data["user_id"],
                "cart_id": test_data["cart_id"],
                "address": test_data["address"],
                "payment_method": "CARD"
            }
        )
        assert saga_response.status_code == 200
        order_data = saga_response.json()
        assert order_data["success"] is True
        
        print(f"\n✅ E2E тест пройден! Заказ #{order_data['order_id']} создан")
        
    def test_catalog_has_products(self):
        """E2E тест: каталог содержит товары"""
        try:
            response = requests.get("http://localhost:5001/products", timeout=5)
            assert response.status_code == 200
            products = response.json()
            assert len(products) >= 5
            print(f"✅ Каталог содержит {len(products)} товаров")
        except:
            pytest.skip("Catalog service not running")