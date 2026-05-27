# 🍕 Food Delivery System — Интеграционная практика

## Описание проекта

Система доставки еды, реализованная в рамках курса "Интеграционная практика".  
Проект демонстрирует микросервисную архитектуру с Saga оркестрацией, кэшированием и CI/CD.

## Архитектура

| Сервис | Порт | Назначение |
|--------|------|------------|
| Catalog Service | 5001 | Управление каталогом товаров |
| Cart Service | 5002 | Управление корзиной |
| Orders Service | 3000 | Управление заказами |
| Saga Orchestrator | 5004 | Оркестрация процесса заказа |
| Frontend | статический | Пользовательский интерфейс |
| PostgreSQL/MSSQL | 5432/1433 | База данных |
| Redis | 6379 | Кэш |

## Требования

- Python 3.11+
- Docker Desktop
- Redis (или Docker)
- PostgreSQL / SQL Server (или Docker)

## Быстрый старт

### 1. Клонирование репозитория
```bash
git clone https://github.com/Hant3res/integration-practice.git
cd integration-practice