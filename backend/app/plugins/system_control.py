"""Plugin de controle de sistema (stub).
No app nativo, estes comandos são executados no dispositivo (abrir app, volume, câmera...).
O backend apenas classifica a intenção e confirma ações perigosas.
"""


def handle(command: str):
    cmd = command.lower()
    intent = "unknown"
    dangerous = False
    if any(k in cmd for k in ["abrir", "open", "launch"]):
        intent = "open_app"
    elif any(k in cmd for k in ["ligar", "desligar", "on", "off"]):
        intent = "power"
    elif "volume" in cmd:
        intent = "volume"
    elif any(k in cmd for k in ["câmera", "camera", "foto", "foto"]):
        intent = "camera"
    elif any(k in cmd for k in ["apagar", "delete", "remover tudo"]):
        intent = "destructive"
        dangerous = True

    confirm = dangerous  # a IA nunca executa ações perigosas sem confirmação
    return {
        "intent": intent,
        "dangerous": dangerous,
        "requires_confirmation": confirm,
        "message": "Ação perigosa requer confirmação do usuário." if dangerous else None,
    }
