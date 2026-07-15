"""Módulo de métricas e status em tempo real do NEXUS AI.

Expõe dados do sistema (CPU, RAM, disco, latência de rede) via endpoints REST
para serem consumidos pelo frontend HUD.
"""
import time
import platform

from fastapi import APIRouter, Depends
from app.core.security import get_current_user
from app.db import models
from app.core.llm import is_available
from app.config import APP_VERSION, DEMO_MODE

router = APIRouter(prefix="/api/metrics", tags=["metrics"])


def _get_system_metrics() -> dict:
    """Coleta métricas reais do sistema (se psutil disponível) ou gera valores realistas."""
    try:
        import psutil
        cpu = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        net = psutil.net_io_counters()
        boot = psutil.boot_time()
        uptime_sec = int(time.time() - boot)
        uptime_h = uptime_sec // 3600
        uptime_m = (uptime_sec % 3600) // 60
        return {
            "cpu_percent": round(cpu, 1),
            "memory_percent": round(mem.percent, 1),
            "memory_used_gb": round(mem.used / 1e9, 2),
            "memory_total_gb": round(mem.total / 1e9, 2),
            "disk_percent": round(disk.percent, 1),
            "disk_used_gb": round(disk.used / 1e9, 1),
            "disk_total_gb": round(disk.total / 1e9, 1),
            "net_sent_mb": round(net.bytes_sent / 1e6, 1),
            "net_recv_mb": round(net.bytes_recv / 1e6, 1),
            "uptime": f"{uptime_h}h {uptime_m}m",
            "platform": platform.system(),
            "real": True,
        }
    except ImportError:
        import random
        return {
            "cpu_percent": round(15 + random.random() * 25, 1),
            "memory_percent": round(38 + random.random() * 18, 1),
            "memory_used_gb": round(5.2 + random.random() * 3, 2),
            "memory_total_gb": 16.0,
            "disk_percent": round(42 + random.random() * 8, 1),
            "disk_used_gb": round(168 + random.random() * 10, 1),
            "disk_total_gb": 512.0,
            "net_sent_mb": round(100 + random.random() * 200, 1),
            "net_recv_mb": round(300 + random.random() * 500, 1),
            "uptime": "—",
            "platform": platform.system(),
            "real": False,
        }


@router.get("/system")
def system_metrics(user: models.User = Depends(get_current_user)):
    """Métricas do sistema em tempo real."""
    metrics = _get_system_metrics()
    metrics.update({
        "llm_available": is_available(),
        "demo_mode": DEMO_MODE,
        "nexus_version": APP_VERSION,
        "timestamp": int(time.time()),
    })
    return metrics


@router.get("/ping")
def ping():
    """Latência do servidor — responde instantaneamente para medir RTT no frontend."""
    return {"ts": time.time(), "status": "ok"}
