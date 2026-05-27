from flask import Flask, jsonify, request
from flask_cors import CORS
import threading
import time

app = Flask(__name__)
CORS(app)

orders = []
order_id_counter = 100

@app.route('/orders', methods=['GET'])
def get_orders():
    user_id = request.args.get('userId')
    if user_id:
        user_orders = [o for o in orders if o['userId'] == user_id]
        return jsonify(user_orders)
    return jsonify(orders)

@app.route('/orders/<int:order_id>', methods=['GET'])
def get_order(order_id):
    """Получить заказ по ID (ДОБАВЛЕНО)"""
    order = next((o for o in orders if o['id'] == order_id), None)
    if order:
        return jsonify(order)
    return jsonify({"error": "Order not found"}), 404

@app.route('/orders/create', methods=['POST'])
def create_order():
    global order_id_counter
    data = request.json
    
    new_order = {
        "id": order_id_counter,
        "userId": data.get('userId'),
        "items": data.get('items'),
        "address": data.get('address'),
        "paymentMethod": data.get('paymentMethod', 'CASH'),
        "status": "PENDING",
        "totalAmount": sum(i['price'] * i['quantity'] for i in data.get('items', [])),
        "createdAt": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        "courierId": None,
        "eta": None
    }
    order_id_counter += 1
    orders.append(new_order)
    
    # Симуляция назначения курьера
    def assign_courier(order_id):
        time.sleep(2)
        for o in orders:
            if o['id'] == order_id and o['status'] == 'PENDING':
                o['status'] = 'COURIER_ASSIGNED'
                o['courierId'] = 500
                o['eta'] = 25
                print(f"Courier assigned to order {order_id}")
    
    threading.Thread(target=assign_courier, args=(new_order['id'],)).start()
    
    return jsonify(new_order), 201

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "module": "orders"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)
