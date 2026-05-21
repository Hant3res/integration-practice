import time
import functools
import threading
from enum import Enum
from typing import Callable, Any
from logging_config import logger, log_payment_attempt, log_circuit_breaker_state

class CircuitState(Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"

class CircuitBreaker:
    """Circuit Breaker паттерн (аналог Polly)"""
    
    def __init__(self, failure_threshold: int = 3, timeout_seconds: int = 30):
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.failure_count = 0
        self.state = CircuitState.CLOSED
        self.last_failure_time = None
        self._lock = threading.Lock()
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Вызов функции с защитой Circuit Breaker"""
        with self._lock:
            if self.state == CircuitState.OPEN:
                if time.time() - self.last_failure_time > self.timeout_seconds:
                    self.state = CircuitState.HALF_OPEN
                    log_circuit_breaker_state("HALF_OPEN", "payment_service")
                else:
                    raise Exception(f"Circuit breaker OPEN. Service unavailable for {self.timeout_seconds}s")
        
        try:
            result = func(*args, **kwargs)
            
            with self._lock:
                if self.state == CircuitState.HALF_OPEN:
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
                    log_circuit_breaker_state("CLOSED", "payment_service")
            
            return result
            
        except Exception as e:
            with self._lock:
                self.failure_count += 1
                self.last_failure_time = time.time()
                
                if self.failure_count >= self.failure_threshold:
                    self.state = CircuitState.OPEN
                    log_circuit_breaker_state("OPEN", "payment_service")
            
            raise e

def retry(max_attempts: int = 3, delay_seconds: float = 1.0, backoff_factor: float = 2.0):
    """
    Декоратор для Retry (аналог Polly WaitAndRetry)
    
    Пример:
        @retry(max_attempts=3, delay_seconds=1, backoff_factor=2)
        def call_payment_api():
            ...
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay_seconds
            
            for attempt in range(1, max_attempts + 1):
                try:
                    result = func(*args, **kwargs)
                    # Логируем успешную попытку
                    log_payment_attempt(kwargs.get('order_id', 0), attempt, True)
                    return result
                    
                except Exception as e:
                    last_exception = e
                    log_payment_attempt(kwargs.get('order_id', 0), attempt, False)
                    
                    if attempt < max_attempts:
                        time.sleep(current_delay)
                        current_delay *= backoff_factor  # exponential backoff
                    else:
                        raise last_exception
            
            raise last_exception
        return wrapper
    return decorator

# Пример использования Retry + Circuit Breaker вместе
class ResilientPaymentService:
    """Платежный сервис с Retry и Circuit Breaker"""
    
    def __init__(self):
        self.circuit_breaker = CircuitBreaker(failure_threshold=3, timeout_seconds=30)
        self.failure_simulator = False  # Для тестирования
    
    @retry(max_attempts=3, delay_seconds=1, backoff_factor=2)
    def process_payment(self, order_id: int, amount: float, method: str = "CARD"):
        """
        Обработка оплаты с Retry
        """
        # Симуляция ошибки для тестирования
        if self.failure_simulator:
            raise Exception(f"Payment service unavailable")
        
        # Имитация вызова внешнего API
        import random
        if random.random() < 0.1:  # 10% ошибка
            raise Exception(f"Payment gateway error for order {order_id}")
        
        return {"status": "success", "transaction_id": f"TXN_{order_id}", "amount": amount}
    
    def process_payment_safe(self, order_id: int, amount: float, method: str = "CARD"):
        """
        Безопасная обработка оплаты (Retry + Circuit Breaker)
        """
        return self.circuit_breaker.call(
            self.process_payment,
            order_id=order_id,
            amount=amount,
            method=method
        )