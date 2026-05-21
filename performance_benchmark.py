import time
import requests
import statistics
from typing import Dict, List

class PerformanceBenchmark:
    """Класс для замера производительности (аналог BenchmarkDotNet)"""
    
    def __init__(self):
        self.results: Dict[str, Dict] = {}
    
    def measure(self, name: str, func, iterations: int = 5) -> float:
        """Замер времени выполнения функции"""
        times = []
        
        for i in range(iterations):
            start = time.perf_counter()
            func()
            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)
            print(f"  {name} - iteration {i+1}: {elapsed:.2f}ms")
        
        avg = statistics.mean(times)
        min_time = min(times)
        max_time = max(times)
        stddev = statistics.stdev(times) if len(times) > 1 else 0
        
        self.results[name] = {
            "avg_ms": avg,
            "min_ms": min_time,
            "max_ms": max_time,
            "stddev_ms": stddev,
            "iterations": iterations
        }
        
        return avg
    
    def api_call(self, url: str, method: str = "GET", data: dict = None):
        """Выполнение API запроса"""
        if method == "GET":
            return requests.get(url, timeout=10)
        elif method == "POST":
            return requests.post(url, json=data, timeout=10)
    
    def benchmark_catalog(self, base_url: str = "http://localhost:5001"):
        """Бенчмарк каталога (сравнение с кэшем и без)"""
        print("\n" + "="*50)
        print("BENCHMARK: Catalog Service")
        print("="*50)
        
        # Очищаем кэш
        try:
            requests.post(f"{base_url}/products/clear-cache")
        except:
            pass
        
        # Первый запрос (без кэша)
        print("\n1. First request (NO CACHE):")
        def first_request():
            self.api_call(f"{base_url}/products")
        
        first_avg = self.measure("catalog_no_cache", first_request, iterations=3)
        
        # Второй запрос (с кэшем)
        print("\n2. Second request (WITH CACHE):")
        def cached_request():
            self.api_call(f"{base_url}/products")
        
        cached_avg = self.measure("catalog_with_cache", cached_request, iterations=3)
        
        improvement = (first_avg - cached_avg) / first_avg * 100 if first_avg > 0 else 0
        print(f"\n[IMPROVEMENT] {improvement:.1f}% faster")
        print(f"   Before: {first_avg:.2f}ms -> After: {cached_avg:.2f}ms")
        
        return {"before": first_avg, "after": cached_avg, "improvement": improvement}
    
    def benchmark_order_flow(self, cart_id: str, base_cart: str = "http://localhost:5002", 
                            base_saga: str = "http://localhost:5004"):
        """Бенчмарк полного процесса заказа"""
        print("\n" + "="*50)
        print("BENCHMARK: Full Order Flow")
        print("="*50)
        
        print("\n1. Add to cart:")
        def add_to_cart():
            try:
                requests.post(
                    f"{base_cart}/cart/add",
                    headers={"X-Cart-ID": cart_id, "Content-Type": "application/json"},
                    json={"product_id": 1, "product_name": "Pizza", "price": 450, "quantity": 2},
                    timeout=10
                )
            except:
                pass
        
        add_avg = self.measure("add_to_cart", add_to_cart, iterations=3)
        
        print("\n2. Create order via Saga:")
        def create_order():
            try:
                requests.post(
                    f"{base_saga}/saga/start",
                    json={
                        "user_id": "benchmark_user",
                        "cart_id": cart_id,
                        "address": "Benchmark St",
                        "payment_method": "CARD"
                    },
                    timeout=10
                )
            except:
                pass
        
        order_avg = self.measure("saga_create_order", create_order, iterations=3)
        
        return {"add_to_cart_ms": add_avg, "saga_order_ms": order_avg}
    
    def print_report(self):
        """Вывод отчёта о производительности"""
        print("\n" + "="*50)
        print("PERFORMANCE REPORT")
        print("="*50)
        
        for name, data in self.results.items():
            print(f"\n{name}:")
            print(f"  Average: {data['avg_ms']:.2f}ms")
            print(f"  Min: {data['min_ms']:.2f}ms")
            print(f"  Max: {data['max_ms']:.2f}ms")
            if data['stddev_ms'] > 0:
                print(f"  StdDev: {data['stddev_ms']:.2f}ms")
    
    def export_to_markdown(self, filename: str = "PERFORMANCE_REPORT.md"):
        """Экспорт отчёта в Markdown"""
        with open(filename, "w", encoding="utf-8") as f:
            f.write("# Performance Benchmark Report\n\n")
            f.write("## Benchmark Results\n\n")
            f.write("| Operation | Avg (ms) | Min (ms) | Max (ms) |\n")
            f.write("|-----------|----------|----------|----------|\n")
            
            for name, data in self.results.items():
                f.write(f"| {name} | {data['avg_ms']:.2f} | {data['min_ms']:.2f} | {data['max_ms']:.2f} |\n")
            
            if 'catalog_no_cache' in self.results and 'catalog_with_cache' in self.results:
                before = self.results['catalog_no_cache']['avg_ms']
                after = self.results['catalog_with_cache']['avg_ms']
                if before > 0:
                    improvement = (before - after) / before * 100
                    f.write(f"\n## Performance Improvement\n\n")
                    f.write(f"- **Before caching:** {before:.2f}ms\n")
                    f.write(f"- **After caching:** {after:.2f}ms\n")
                    f.write(f"- **Speedup:** {improvement:.1f}%\n")
        
        print(f"\n[EXPORT] Report saved to {filename}")

def main():
    benchmark = PerformanceBenchmark()
    
    try:
        benchmark.benchmark_catalog()
    except Exception as e:
        print(f"[ERROR] Catalog benchmark failed: {e}")
    
    cart_id = f"bench_{int(time.time())}"
    try:
        benchmark.benchmark_order_flow(cart_id)
    except Exception as e:
        print(f"[ERROR] Order flow benchmark failed: {e}")
    
    benchmark.print_report()
    benchmark.export_to_markdown()

if __name__ == "__main__":
    main()