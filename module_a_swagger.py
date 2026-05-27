from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Тестовые данные
products = [
    {"id": 1, "name": "Пицца Маргарита", "price": 450, "category": "Пицца", "inStock": True},
    {"id": 2, "name": "Пицца Пепперони", "price": 520, "category": "Пицца", "inStock": True},
    {"id": 3, "name": "Суши Филадельфия", "price": 650, "category": "Суши", "inStock": True},
    {"id": 4, "name": "Бургер Гурман", "price": 380, "category": "Бургеры", "inStock": False},
    {"id": 5, "name": "Карбонара", "price": 420, "category": "Паста", "inStock": True},
]

# ========== API ЭНДПОИНТЫ ==========

@app.route('/products', methods=['GET'])
def get_products():
    """Получить все товары"""
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

# ========== SWAGGER UI ==========

@app.route('/swagger')
def swagger_ui():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Swagger UI - Catalog API</title>
        <link rel="stylesheet" type="text/css" href="https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/5.10.5/swagger-ui.min.css">
        <style>
            body { margin: 0; padding: 0; }
        </style>
    </head>
    <body>
        <div id="swagger-ui"></div>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/5.10.5/swagger-ui-bundle.min.js"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/5.10.5/swagger-ui-standalone-preset.min.js"></script>
        <script>
            window.onload = function() {
                SwaggerUIBundle({
                    url: "/openapi.json",
                    dom_id: "#swagger-ui",
                    presets: [
                        SwaggerUIBundle.presets.apis,
                        SwaggerUIStandalonePreset
                    ],
                    layout: "BaseLayout",
                    deepLinking: true
                });
            }
        </script>
    </body>
    </html>
    '''

@app.route('/openapi.json')
def openapi_json():
    """OpenAPI 3.0 спецификация для Swagger"""
    return {
        "openapi": "3.0.0",
        "info": {
            "title": "Food Delivery - Catalog API",
            "description": "API для управления каталогом товаров",
            "version": "1.0.0",
            "contact": {
                "name": "Integration Practice",
                "url": "https://github.com/Hant3res/integration-practice"
            }
        },
        "servers": [
            {
                "url": "http://localhost:5001",
                "description": "Local development server"
            }
        ],
        "paths": {
            "/products": {
                "get": {
                    "summary": "Получить список всех товаров",
                    "description": "Возвращает массив всех товаров из каталога",
                    "parameters": [
                        {
                            "name": "category",
                            "in": "query",
                            "description": "Фильтр по категории",
                            "required": False,
                            "schema": {
                                "type": "string",
                                "example": "Пицца"
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Успешный ответ",
                            "content": {
                                "application/json": {
                                    "example": [
                                        {"id": 1, "name": "Пицца Маргарита", "price": 450, "category": "Пицца", "inStock": True}
                                    ]
                                }
                            }
                        }
                    }
                }
            },
            "/products/{product_id}": {
                "get": {
                    "summary": "Получить товар по ID",
                    "parameters": [
                        {
                            "name": "product_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "integer"},
                            "description": "ID товара"
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Товар найден",
                            "content": {
                                "application/json": {
                                    "example": {"id": 1, "name": "Пицца Маргарита", "price": 450, "category": "Пицца", "inStock": True}
                                }
                            }
                        },
                        "404": {
                            "description": "Товар не найден",
                            "content": {
                                "application/json": {
                                    "example": {"error": "Product not found"}
                                }
                            }
                        }
                    }
                }
            },
            "/health": {
                "get": {
                    "summary": "Проверка статуса сервиса",
                    "responses": {
                        "200": {
                            "description": "Сервис работает",
                            "content": {
                                "application/json": {
                                    "example": {"status": "ok", "module": "catalog"}
                                }
                            }
                        }
                    }
                }
            }
        },
        "tags": [
            {"name": "Products", "description": "Операции с товарами"},
            {"name": "Health", "description": "Проверка работоспособности"}
        ]
    }

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)