import pytest
from playwright.sync_api import sync_playwright
import requests
import time

class TestE2E:
    """E2E тесты через Playwright"""
    
    @pytest.fixture(scope="class")
    def browser(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)  # headless=True для CI
            yield browser
            browser.close()
    
    def test_full_order_flow(self, browser):
        """E2E тест: полный сценарий покупки через UI"""
        page = browser.new_page()
        
        # 1. Открываем фронтенд
        page.goto("file:///C:/Users/hante/Desktop/3%20etap/frontend/index.html")
        
        # 2. Ждём загрузки каталога
        page.wait_for_selector(".product-card", timeout=10000)
        
        # 3. Кликаем на первый товар (добавление в корзину)
        page.click(".product-card:first-child")
        
        # 4. Проверяем, что корзина обновилась
        page.wait_for_function(
            'document.getElementById("cartCount").innerText !== "0"',
            timeout=5000
        )
        cart_count = page.inner_text("#cartCount")
        assert int(cart_count) > 0, "Cart should not be empty"
        
        # 5. Нажимаем "Оформить заказ"
        page.click("#checkoutBtn")
        
        # 6. Ждём модальное окно и заполняем форму
        page.wait_for_selector("#checkoutModal", timeout=5000)
        page.fill("#address", "E2E Test Address")
        
        # 7. Подтверждаем заказ
        page.click("#confirmOrderBtn")
        
        # 8. Ждём успешного уведомления
        page.wait_for_selector(".toast-notification .alert", timeout=10000)
        toast_text = page.inner_text(".toast-notification .alert")
        assert "заказ" in toast_text.lower() or "order" in toast_text.lower()
        
        print(f"✅ E2E тест пройден: {toast_text}")
        page.close()
    
    def test_add_to_cart_updates_total(self, browser):
        """E2E тест: добавление товара обновляет сумму в корзине"""
        page = browser.new_page()
        page.goto("file:///C:/Users/hante/Desktop/3%20etap/frontend/index.html")
        page.wait_for_selector(".product-card", timeout=10000)
        
        # Получаем цену первого товара
        first_product = page.locator(".product-card:first-child")
        price_text = first_product.locator(".text-muted").inner_text()
        import re
        price = int(re.search(r"\d+", price_text).group())
        
        # Добавляем товар 3 раза
        for i in range(3):
            first_product.click()
            time.sleep(0.5)
        
        # Проверяем итоговую сумму
        total = int(page.inner_text("#cartTotal"))
        assert total == price * 3, f"Expected {price*3}, got {total}"
        
        page.close()