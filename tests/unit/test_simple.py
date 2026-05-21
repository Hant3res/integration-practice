import pytest

class TestSimple:
    """Простые unit-тесты для проверки работы pytest"""
    
    def test_addition(self):
        assert 1 + 1 == 2
    
    def test_string_concatenation(self):
        assert "hello" + " world" == "hello world"
    
    def test_list_append(self):
        items = []
        items.append(1)
        assert len(items) == 1
        assert items[0] == 1
    
    def test_dictionary(self):
        data = {"name": "test", "value": 100}
        assert data["name"] == "test"
        assert data.get("value") == 100
    
    def test_true_condition(self):
        assert True is True
    
    def test_false_condition(self):
        assert False is not True
    
    @pytest.mark.parametrize("a,b,expected", [
        (1, 2, 3),
        (5, 5, 10),
        (0, 0, 0),
        (-1, 1, 0),
    ])
    def test_parameterized_addition(self, a, b, expected):
        assert a + b == expected
