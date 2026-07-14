"""Descoberta na LAN via mDNS (Zeroconf).

Permite que o app Android encontre o backend automaticamente na mesma Wi-Fi,
sem precisar digitar o IP da máquina. É best-effort: se o `zeroconf` não
estiver instalado ou a rede bloquear mDNS, o app ainda pode conectar via IP manual.
"""
import logging
import socket
import threading

from app.config import PORT

logger = logging.getLogger("nexus.discovery")

_registrar = None
_SERVICE_TYPE = "_nexus._tcp.local."


def _local_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # não envia tráfego de fato; só usa a tabela de roteamento p/ achar o IP de saída
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()


def _advertise() -> None:
    global _registrar
    try:
        from zeroconf import Zeroconf, ServiceInfo
    except Exception as e:  # zeroconf opcional
        logger.warning("mDNS desativado (instale 'zeroconf' p/ auto-descoberta): %s", e)
        return
    try:
        ip = _local_ip()
        info = ServiceInfo(
            _SERVICE_TYPE,
            f"NEXUS AI.{_SERVICE_TYPE}",
            addresses=[socket.inet_aton(ip)],
            port=PORT,
            properties={"path": "/", "app": "nexus-ai"},
            server="nexus.local.",
        )
        zc = Zeroconf()
        zc.register_service(info)
        _registrar = (zc, info)
        logger.info("mDNS: serviço %s anunciado em %s:%s", _SERVICE_TYPE, ip, PORT)
    except Exception as e:
        logger.warning("Falha ao anunciar mDNS: %s", e)


def start_discovery() -> None:
    """Inicia o anúncio mDNS em thread separada (não bloqueia a subida do servidor)."""
    t = threading.Thread(target=_advertise, daemon=True)
    t.start()
