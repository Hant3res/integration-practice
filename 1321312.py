from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

products = [
    {"id": 1, "name": "Пицца Маргарита", "price": 450, "category": "Пицца", "inStock": True},
    {"id": 2, "name": "Пицца Пепперони", "price": 520, "category": "Пицца", "inStock": True},
    {"id": 3, "name": "Суши Филадельфия", "price": 650, "category": "Суши", "inStock": True},
    {"id": 4, "name": "Бургер Гурман", "price": 380, "category": "Бургеры", "inStock": False},
    {"id": 5, "name": "Карбонара", "price": 420, "category": "Паста", "inStock": True},
]

@app.route('/products', methods=['GET'])
def get_products():
    """Получить список всех товаров"""
    category = request.args.get('category')
    if category:
        filtered = [p for p in products if p['category'].lower() == category.lower()]
        return jsonify(filtered)
    return jsonify(products)

@app.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Получить товар по ID"""
    product = next((p for p in products if p['id'] == product_id), None)
    if product:
        return jsonify(product)
    return jsonify({"error": "Product not found"}), 404

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "module": "catalog"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
