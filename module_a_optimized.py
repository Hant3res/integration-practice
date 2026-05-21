from flask import Flask, jsonify, request
from flask_cors import CORS
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import urllib.parse
import time
from cache_service import cache

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

class Product(Base):
    __tablename__ = 'Products'
    Id = Column(Integer, primary_key=True)
    Name = Column(String(200), nullable=False)
    Price = Column(Float, nullable=False)
    Category = Column(String(100))
    InStock = Column(Boolean, default=True)

@app.route('/products', methods=['GET'])
def get_products():
    """С кэшированием (кеш на 5 минут)"""
    start_time = time.time()
    
    # Пытаемся получить из кэша
    cached = cache.get_json('catalog:products')
    
    if cached:
        elapsed = (time.time() - start_time) * 1000
        print(f"📊 Response time (CACHED): {elapsed:.2f}ms")
        return jsonify(cached)
    
    # Кэш промах — идём в БД
    session = Session()
    products = session.query(Product).all()
    session.close()
    
    result = [{
        'id': p.Id,
        'name': p.Name,
        'price': p.Price,
        'category': p.Category,
        'inStock': p.InStock
    } for p in products]
    
    # Сохраняем в кэш на 5 минут
    cache.set_json('catalog:products', result, ttl=300)
    
    elapsed = (time.time() - start_time) * 1000
    print(f"📊 Response time (DB): {elapsed:.2f}ms")
    
    return jsonify(result)

@app.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Получение одного товара с кэшированием"""
    start_time = time.time()
    
    cached = cache.get_json(f'catalog:product:{product_id}')
    if cached:
        elapsed = (time.time() - start_time) * 1000
        print(f"📊 Product {product_id} (CACHED): {elapsed:.2f}ms")
        return jsonify(cached)
    
    session = Session()
    product = session.query(Product).filter(Product.Id == product_id).first()
    session.close()
    
    if not product:
        return jsonify({"error": "Not found"}), 404
    
    result = {
        'id': product.Id,
        'name': product.Name,
        'price': product.Price,
        'category': product.Category,
        'inStock': product.InStock
    }
    
    cache.set_json(f'catalog:product:{product_id}', result, ttl=300)
    
    elapsed = (time.time() - start_time) * 1000
    print(f"📊 Product {product_id} (DB): {elapsed:.2f}ms")
    
    return jsonify(result)

@app.route('/products/clear-cache', methods=['POST'])
def clear_cache():
    """Очистка кэша каталога"""
    cache.clear("catalog:*")
    return jsonify({"message": "Cache cleared", "stats": cache.get_stats()})

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "module": "catalog-optimized"})

@app.route('/performance/stats', methods=['GET'])
def performance_stats():
    return jsonify(cache.get_stats())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)