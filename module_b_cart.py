from flask import Flask, jsonify, request
from flask_cors import CORS
import uuid

app = Flask(__name__)
app.secret_key = 'secret-key-for-demo'
CORS(app)

carts = {}

@app.route('/cart', methods=['GET'])
def get_cart():
    cart_id = request.headers.get('X-Cart-ID')
    if not cart_id or cart_id not in carts:
        return jsonify({"items": [], "total": 0})
    return jsonify(carts[cart_id])

@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    cart_id = request.headers.get('X-Cart-ID')
    if not cart_id:
        cart_id = str(uuid.uuid4())
    
    data = request.json
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)
    product_name = data.get('product_name')
    price = data.get('price')
    
    if cart_id not in carts:
        carts[cart_id] = {"items": [], "total": 0}
    
    cart = carts[cart_id]
    existing = next((i for i in cart['items'] if i['product_id'] == product_id), None)
    
    if existing:
        existing['quantity'] += quantity
    else:
        cart['items'].append({
            "product_id": product_id,
            "name": product_name,
            "price": price,
            "quantity": quantity
        })
    
    cart['total'] = sum(i['price'] * i['quantity'] for i in cart['items'])
    
    return jsonify({
        "cart_id": cart_id,
        "items": cart['items'],
        "total": cart['total']
    }), 201

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "module": "cart"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)