# Performance Benchmark Report

## Benchmark Results

| Operation | Avg (ms) | Min (ms) | Max (ms) |
|-----------|----------|----------|----------|
| catalog_no_cache | 2225.03 | 2072.93 | 2494.58 |
| catalog_with_cache | 2095.78 | 2079.61 | 2117.55 |
| add_to_cart | 4098.27 | 4095.43 | 4099.88 |
| saga_create_order | 4098.83 | 4079.21 | 4132.35 |

## Performance Improvement

- **Before caching:** 2225.03ms
- **After caching:** 2095.78ms
- **Speedup:** 5.8%
