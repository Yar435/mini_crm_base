"""Prometheus-метрики приложения analytics."""

from prometheus_client import Histogram

process_graph_build_seconds = Histogram(
    "analytics_process_graph_build_seconds",
    "Wall time spent building process graph (cache miss)",
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0),
)
