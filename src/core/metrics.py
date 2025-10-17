from prometheus_client import Counter

health_hits_total = Counter("health_hits_total", "Total number of /health requests")
