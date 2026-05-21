from flask import Flask, jsonify, request
from flask_cors import CORS
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import requests
import urllib.parse

app = Flask(__name__)
CORS(app)

# Подключение к MSSQL
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_USER = os.environ.get('DB_USER', 'sa')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'YourStrong!Passw0rd')
DB_NAME = os.environ.get('DB_NAME', 'DeliveryDB')

params = urllib.parse.quote_plus(
    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
    f"SERVER={DB_HOST};"
    f"DATABASE={DB_NAME};"
    f"UID={DB_USER};"
    f"PWD={DB_PASSWORD}"
)
DATABASE_URL = f"mssql+pyodbc:///?odbc_connect={params}"

engine = create_engine(DATABASE_URL)
Base = declarative_base()
Session = sessionmaker(bind=engine)
session = Session()

class Product(Base):
    __tablename__ = 'Products'
    Id = Column(Integer, primary_key=True)
    Name = Column(String(200), nullable=False)
    Price = Column(Float, nullable=False)
    Category = Column(String(100))
    InStock = Column(Boolean, default=True)

Base.metadata.create_all(engine)

ORDER_SERVICE_URL = os.environ.get('ORDER_SERVICE_URL', 'http://localhost:3000')

def send_webhook(product_data):
    try:
        response = requests.post(
            f"{ORDER_SERVICE_URL}/webhooks/product-created",
            json=product_data,
            timeout=5
        )
        print(f'Webhook sent: {response.status_code}')
    except Exception as e:
        print(f'Webhook failed: {e}')

@app.route('/products', methods=['GET'])
def get_products():
    products = session.query(Product).all()
    return jsonify([{
        'id': p.Id,
        'name': p.Name,
        'price': p.Price,
        'category': p.Category,
        'inStock': p.InStock
    } for p in products])

@app.route('/products', methods=['POST'])
def create_product():
    data = request.json
    new_product = Product(
        Name=data['name'],
        Price=data['price'],
        Category=data.get('category', ''),
        InStock=data.get('inStock', True)
    )
    session.add(new_product)
    session.commit()
    product_data = {
        'id': new_product.Id,
        'name': new_product.Name,
        'price': new_product.Price,
        'category': new_product.Category
    }
    send_webhook(product_data)
    return jsonify({'id': new_product.Id, 'message': 'Product created'}), 201

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'module': 'catalog'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
