from flask import Flask, jsonify, request
from flask_cors import CORS
import logging
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from saga.order_saga import OrderSaga

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Инициализация Saga оркестратора
saga_orchestrator = OrderSaga()

@app.route('/saga/start', methods=['POST'])
def start_saga():
    """
    Запуск сквозного сценария оформления заказа
    7.1 - end-to-end сценарий из BPMN
    """
    data = request.json
    user_id = data.get('user_id')
    cart_id = data.get('cart_id')
    address = data.get('address')
    payment_method = data.get('payment_method', 'CARD')
    
    if not all([user_id, cart_id, address]):
        return jsonify({"error": "Missing required fields: user_id, cart_id, address"}), 400
    
    logger.info(f"Starting end-to-end order process for user {user_id}")
    result, status_code = saga_orchestrator.start_order_saga(
        user_id=user_id,
        cart_id=cart_id,
        address=address,
        payment_method=payment_method
    )
    
    return jsonify(result), status_code

@app.route('/saga/status/<int:order_id>', methods=['GET'])
def get_saga_status(order_id):
    """Получить статус Saga процесса"""
    result, status_code = saga_orchestrator.get_saga_status(order_id)
    return jsonify(result), status_code

@app.route('/saga/active', methods=['GET'])
def get_active_sagas():
    """Получить все активные Saga процессы"""
    sagas = []
    for order_id, saga in saga_orchestrator.active_sagas.items():
        sagas.append({
            "order_id": order_id,
            "status": saga.status.value,
            "payment_status": saga.payment_status.value,
            "total_amount": saga.total_amount
        })
    return jsonify(sagas)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "module": "saga-orchestrator"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5004, debug=True)