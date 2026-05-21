import logging
import requests
import time
import sys
import os
from datetime import datetime
from typing import Dict, List

# Добавляем путь для импорта модулей
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from saga.models import OrderSagaData, OrderItem, OrderStatus, PaymentStatus

# Импортируем модули логирования и resilience
try:
    from logging_config import logger, log_success, log_error
    from resilience import ResilientPaymentService
except ImportError:
    # Fallback, если файлы ещё не созданы
    import logging
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO)
    
    def log_success(order_id, user_id, total):
        logger.info(f"SUCCESS: order {order_id}, user {user_id}, total {total}")
    
    def log_error(order_id, error_type, error_message):
        logger.error(f"ERROR: order {order_id}, {error_type} - {error_message}")
    
    class ResilientPaymentService:
        def __init__(self):
            self.failure_simulator = False
        def process_payment_safe(self, order_id, amount, method="CARD"):
            if self.failure_simulator:
                raise Exception("Payment failed")
            return {"status": "success", "transaction_id": f"TXN_{order_id}"}


class OrderSaga:
    """
    Saga оркестратор для процесса заказа
    Реализует паттерн Saga с компенсациями
    """
    
    def __init__(self):
        self.active_sagas: Dict[int, OrderSagaData] = {}
        # URL сервисов (модули)
        self.catalog_url = "http://localhost:5001"
        self.cart_url = "http://localhost:5002"
        self.orders_url = "http://localhost:3000"
    
    def start_order_saga(self, user_id: str, cart_id: str, address: str, payment_method: str = "CARD"):
        """
        Начало Saga процесса заказа
        7.1 - сквозной сценарий из BPMN
        """
        logger.info(f"=== START SAGA: user={user_id}, cart={cart_id} ===")
        
        # Шаг 1: Получаем корзину
        saga_data = self._get_cart_data(cart_id)
        if not saga_data:
            return {"error": "Cart not found"}, 404
        
        saga_data.user_id = user_id
        saga_data.address = address
        saga_data.payment_method = payment_method
        saga_data.status = OrderStatus.NEW
        
        self.active_sagas[saga_data.order_id] = saga_data
        logger.info(f"Saga started for order #{saga_data.order_id}")
        
        # Выполняем шаги Saga
        try:
            # 7.2 - Проверка остатков
            self._check_stock(saga_data)
            
            # 7.3 - Обработка оплаты (с Retry + Circuit Breaker)
            self._process_payment(saga_data)
            
            # Создание заказа
            self._create_order(saga_data)
            
            # Назначение курьера
            self._assign_courier(saga_data)
            
            # Логируем успех
            log_success(saga_data.order_id, saga_data.user_id, saga_data.total_amount)
            
            logger.info(f"=== SAGA COMPLETED for order #{saga_data.order_id} ===")
            return {
                "success": True,
                "order_id": saga_data.order_id,
                "status": saga_data.status.value,
                "total_amount": saga_data.total_amount
            }, 200
            
        except Exception as e:
            logger.error(f"SAGA FAILED: {e}")
            log_error(saga_data.order_id, "SAGA_ERROR", str(e))
            # Компенсация
            self._compensate(saga_data)
            return {
                "success": False,
                "error": str(e),
                "order_id": saga_data.order_id,
                "status": saga_data.status.value
            }, 500
    
    def _get_cart_data(self, cart_id: str) -> OrderSagaData:
        """Получение данных корзины из модуля Б"""
        try:
            headers = {"X-Cart-ID": cart_id}
            response = requests.get(f"{self.cart_url}/cart", headers=headers, timeout=10)
            response.raise_for_status()
            cart = response.json()
            
            items = [
                OrderItem(
                    product_id=item["product_id"],
                    product_name=item["name"],
                    price=item["price"],
                    quantity=item["quantity"]
                )
                for item in cart.get("items", [])
            ]
            
            return OrderSagaData(
                order_id=int(time.time()) % 10000,
                user_id="",
                items=items,
                address="",
                payment_method="",
                total_amount=cart.get("total", 0),
                status=OrderStatus.NEW,
                payment_status=PaymentStatus.PENDING,
                created_at=datetime.now().isoformat(),
                compensation_done=False
            )
        except Exception as e:
            logger.error(f"Failed to get cart: {e}")
            raise Exception(f"Cart not found: {e}")
    
    def _check_stock(self, saga: OrderSagaData):
        """7.2 - Проверка остатков товаров"""
        logger.info(f"Checking stock for order #{saga.order_id}")
        
        for item in saga.items:
            try:
                response = requests.get(f"{self.catalog_url}/products/{item.product_id}", timeout=5)
                response.raise_for_status()
                product = response.json()
                
                if not product.get("inStock", False):
                    raise Exception(f"Product {item.product_name} is out of stock")
                
                logger.info(f"Stock OK: {item.product_name} x{item.quantity}")
            except Exception as e:
                raise Exception(f"Stock check failed for {item.product_name}: {e}")
        
        saga.status = OrderStatus.STOCK_RESERVED
        logger.info(f"Stock check passed for order #{saga.order_id}")
    
    def _process_payment(self, saga: OrderSagaData):
        """
        9.3 - Обработка оплаты с Retry + Circuit Breaker
        """
        logger.info(f"Processing payment for order #{saga.order_id}, amount: {saga.total_amount}")
        
        payment_service = ResilientPaymentService()
        
        # Для демонстрации ошибки (раскомментируйте для теста)
        # payment_service.failure_simulator = True
        
        try:
            result = payment_service.process_payment_safe(
                order_id=saga.order_id,
                amount=saga.total_amount,
                method=saga.payment_method
            )
            
            saga.payment_status = PaymentStatus.SUCCESS
            saga.status = OrderStatus.PAYMENT_CONFIRMED
            logger.info(f"Payment SUCCESS for order #{saga.order_id}, tx: {result.get('transaction_id')}")
            
        except Exception as e:
            saga.payment_status = PaymentStatus.FAILED
            saga.status = OrderStatus.CANCELLED
            log_error(saga.order_id, "PAYMENT_ERROR", str(e))
            raise Exception(f"Payment failed after retries: {e}")
    
    def _create_order(self, saga: OrderSagaData):
        """Создание заказа в модуле В"""
        logger.info(f"Creating order #{saga.order_id}")
        
        order_items = [
            {
                "product_id": item.product_id,
                "name": item.product_name,
                "price": item.price,
                "quantity": item.quantity
            }
            for item in saga.items
        ]
        
        order_data = {
            "userId": saga.user_id,
            "items": order_items,
            "address": saga.address,
            "paymentMethod": saga.payment_method
        }
        
        try:
            response = requests.post(f"{self.orders_url}/orders/create", json=order_data, timeout=10)
            response.raise_for_status()
            order = response.json()
            saga.order_id = order.get("id", saga.order_id)
            saga.status = OrderStatus.ORDER_CREATED
            logger.info(f"Order #{saga.order_id} created successfully")
        except Exception as e:
            raise Exception(f"Order creation failed: {e}")
    
    def _assign_courier(self, saga: OrderSagaData):
        """Назначение курьера"""
        logger.info(f"Assigning courier for order #{saga.order_id}")
        saga.status = OrderStatus.COURIER_ASSIGNED
        logger.info(f"Courier assigned for order #{saga.order_id}")
    
    def _compensate(self, saga: OrderSagaData):
        """Компенсация: отмена заказа и возврат средств"""
        logger.warning(f"=== COMPENSATION START for order #{saga.order_id} ===")
        
        # 1. Если заказ был создан, отменяем его
        if saga.status in [OrderStatus.ORDER_CREATED, OrderStatus.COURIER_ASSIGNED]:
            try:
                requests.post(f"{self.orders_url}/orders/{saga.order_id}/cancel", timeout=5)
                logger.info(f"Order #{saga.order_id} cancelled")
            except Exception as e:
                logger.error(f"Order cancellation failed: {e}")
        
        # 2. Если оплата прошла, возвращаем средства
        if saga.payment_status == PaymentStatus.SUCCESS:
            logger.info(f"Refunding payment for order #{saga.order_id}")
            saga.payment_status = PaymentStatus.REFUNDED
        
        # 3. Возвращаем товары на склад
        logger.info(f"Stock released for order #{saga.order_id}")
        
        saga.status = OrderStatus.COMPENSATION_DONE
        saga.compensation_done = True
        log_error(saga.order_id, "COMPENSATION", "Saga compensated after failure")
        logger.warning(f"=== COMPENSATION DONE for order #{saga.order_id} ===")
    
    def get_saga_status(self, order_id: int):
        """Получить статус Saga"""
        saga = self.active_sagas.get(order_id)
        if not saga:
            return {"error": "Saga not found"}, 404
        
        return {
            "order_id": saga.order_id,
            "status": saga.status.value,
            "payment_status": saga.payment_status.value,
            "total_amount": saga.total_amount,
            "compensation_done": saga.compensation_done,
            "created_at": saga.created_at
        }, 200