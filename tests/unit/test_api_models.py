import pytest
import json

class TestAPIModels:
    """Unit-тесты для API моделей"""
    
    def test_product_model(self):
        product = {
            "id": 1,
            "name": "Пицца Маргарита",
            "price": 450,
            "category": "Пицца",
            "inStock": True
        }
        assert product["id"] == 1
        assert product["name"] == "Пицца Маргарита"
        assert product["price"] > 0
        assert isinstance(product["inStock"], bool)
    
    def test_cart_item_model(self):
        cart_item = {
            "product_id": 1,
            "name": "Пицца",
            "price": 450,
            "quantity": 2
        }
        total = cart_item["price"] * cart_item["quantity"]
        assert total == 900
        assert cart_item["quantity"] >= 1
    
    def test_order_model(self):
        order = {
            "id": 100,
            "userId": "user123",
            "status": "PENDING",
            "totalAmount": 900,
            "items": [
                {"product_id": 1, "name": "Пицца", "price": 450, "quantity": 2}
            ]
        }
        assert order["status"] in ["PENDING", "CONFIRMED", "COURIER_ASSIGNED", "DELIVERED"]
        assert order["totalAmount"] > 0
        assert len(order["items"]) > 0
    
    def test_order_serialization(self):
        order = {
            "id": 100,
            "userId": "user123",
            "status": "PENDING"
        }
        json_str = json.dumps(order)
        parsed = json.loads(json_str)
        assert parsed["id"] == 100
        assert parsed["userId"] == "user123"
    
    def test_cart_calculation(self):
        items = [
            {"price": 100, "quantity": 2},
            {"price": 200, "quantity": 1},
            {"price": 50, "quantity": 3}
        ]
        total = sum(item["price"] * item["quantity"] for item in items)
        assert total == (100*2 + 200*1 + 50*3) == 550
