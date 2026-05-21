import structlog
import logging
import sys
from datetime import datetime
from pathlib import Path

# Создаём папку для логов
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# Настройка стандартного логгера
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_dir / "app.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)

# Настройка структурированного логирования (JSON формат)
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

def log_success(order_id: int, user_id: str, total: float):
    """Логирование успешной операции"""
    logger.info(
        "order_success",
        order_id=order_id,
        user_id=user_id,
        total_amount=total,
        status="COMPLETED"
    )

def log_error(order_id: int, error_type: str, error_message: str):
    """Логирование ошибки"""
    logger.error(
        "order_failed",
        order_id=order_id,
        error_type=error_type,
        error_message=error_message,
        status="FAILED"
    )

def log_payment_attempt(order_id: int, attempt: int, success: bool):
    """Логирование попытки оплаты (Retry)"""
    logger.info(
        "payment_attempt",
        order_id=order_id,
        attempt=attempt,
        success=success
    )

def log_circuit_breaker_state(state: str, service: str):
    """Логирование состояния Circuit Breaker"""
    logger.warning(
        "circuit_breaker_state",
        service=service,
        state=state
    )