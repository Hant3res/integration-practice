import pytest

class TestOrderCalculations:
    """Unit-тесты для расчётов заказа"""
    
    def test_cart_total_calculation(self):
        items = [
            {"price": 100, "quantity": 2},
            {"price": 200, "quantity": 1},
            {"price": 50, "quantity": 3}
        ]
        total = sum(item["price"] * item["quantity"] for item in items)
        assert total == 550
    
    def test_order_status_valid(self):
        valid_statuses = ["PENDING", "CONFIRMED", "COURIER_ASSIGNED", "DELIVERED", "CANCELLED"]
        assert "PENDING" in valid_statuses
        assert "DELIVERED" in valid_statuses
        assert len(valid_statuses) == 5
    
    def test_price_validation(self):
        def validate_price(price):
            return price > 0 and isinstance(price, (int, float))
        
        assert validate_price(450) is True
        assert validate_price(-10) is False
        assert validate_price(0) is False
    
    @pytest.mark.parametrize("quantity,expected", [
        (1, True),
        (0, False),
        (-1, False),
        (100, True)
    ])
    def test_quantity_validation(self, quantity, expected):
        def is_valid_quantity(q):
            return q > 0
        assert is_valid_quantity(quantity) == expected