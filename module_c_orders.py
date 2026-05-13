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

@app.route('/orders/create', methods=['POST'])
def create_order():
    global order_id_counter
    data = request.json
    
    if not data.get('userId') or not data.get('items') or not data.get('address'):
        return jsonify({"error": "Missing required fields"}), 400
    
    new_order = {
        "id": order_id_counter,
        "userId": data['userId'],
        "items": data['items'],
        "address": data['address'],
        "paymentMethod": data.get('paymentMethod', 'CASH'),
        "status": "PENDING",
        "totalAmount": sum(i['price'] * i['quantity'] for i in data['items']),
        "createdAt": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        "courierId": None,
        "eta": None
    }
    order_id_counter += 1
    orders.append(new_order)
    
    # Симуляция поиска курьера (фоном)
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

@app.route('/orders/<int:order_id>/status', methods=['GET'])
def get_status(order_id):
    order = next((o for o in orders if o['id'] == order_id), None)
    if not order:
        return jsonify({"error": "Order not found"}), 404
    return jsonify({
        "orderId": order['id'],
        "status": order['status'],
        "courierId": order['courierId'],
        "eta": order['eta']
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)
EOF