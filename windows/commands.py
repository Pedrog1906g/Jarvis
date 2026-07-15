"""Comandos locais do JARVIS no Windows (sem dependências pesadas na importação)."""

import os
import re
import shutil
import subprocess
import webbrowser

# Mapa simples nome -> comando/URL. Expanda à vontade.
KNOWN_APPS = {
    "chrome": "chrome",
    "google chrome": "chrome",
    "edge": "msedge",
    "firefox": "firefox",
    "notepad": "notepad",
    "bloco de notas": "notepad",
    "calculadora": "calc",
    "calculator": "calc",
    "explorador": "explorer",
    "explorer": "explorer",
    "cmd": "cmd",
    "prompt": "cmd",
    "spotify": "spotify",
    "youtube": "https://youtube.com",
    "música": "spotify",
    "musica": "spotify",
    "arquivos": "explorer",
}


def classify_command(text: str) -> str:
    """Retorna a intenção: open_app | organize | stats | volume | reminder | chat."""
    t = (text or "").lower().strip()
    if re.search(r"\b(abrir|abre|abra|execute|rodar|iniciar|inicie)\b", t):
        return "open_app"
    if "organiz" in t or "arrumar os arquivos" in t or "arrumar arquivos" in t:
        return "organize"
    if "desempenho" in t or "performance" in t or "cpu" in t or "memória" in t or "memoria" in t:
        return "stats"
    if "volume" in t:
        return "volume"
    if "lembrete" in t or "lembretes" in t:
        return "reminder"
    return "chat"


def open_program(name: str) -> str:
    t = (name or "").lower().strip()
    t = re.sub(r"^(abrir|abre|abra|execute|rodar|iniciar|inicie|o|a|os|as|me|um|uma|app|programa)\s+", "", t).strip()
    target = KNOWN_APPS.get(t)
    try:
        if target and target.startswith("http"):
            webbrowser.open(target)
            return f"Abrindo {t} no navegador."
        if target:
            subprocess.Popen(target, shell=True)
            return f"Abrindo {t}."
        subprocess.Popen(t, shell=True)
        return f"Executando {t}."
    except Exception as e:
        return f"Não consegui abrir {name}: {e}"


def organize_folder(path: str = None) -> str:
    path = path or os.path.expanduser("~/Downloads")
    if not os.path.isdir(path):
        return "Pasta não encontrada."
    groups = {
        "Imagens": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"],
        "Documentos": [".pdf", ".doc", ".docx", ".txt", ".xls", ".xlsx", ".ppt", ".pptx"],
        "Vídeos": [".mp4", ".mkv", ".avi", ".mov", ".webm"],
        "Músicas": [".mp3", ".wav", ".ogg", ".flac"],
        "Compactados": [".zip", ".rar", ".7z", ".tar", ".gz"],
        "Instaladores": [".exe", ".msi"],
    }
    moved = 0
    for f in os.listdir(path):
        fp = os.path.join(path, f)
        if not os.path.isfile(fp):
            continue
        ext = os.path.splitext(f)[1].lower()
        dest = None
        for grp, exts in groups.items():
            if ext in exts:
                dest = os.path.join(path, grp)
                break
        if not dest:
            dest = os.path.join(path, "Outros")
        os.makedirs(dest, exist_ok=True)
        try:
            shutil.move(fp, os.path.join(dest, f))
            moved += 1
        except Exception:
            pass
    return f"Organizei {moved} arquivo(s) em {path}."


def system_stats() -> str:
    try:
        import psutil
        cpu = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        return (f"CPU: {cpu:.0f}% | RAM: {mem.percent:.0f}% "
                f"({mem.used // (1024 ** 3)}/{mem.total // (1024 ** 3)} GB) | "
                f"Disco: {disk.percent:.0f}%")
    except Exception as e:
        return f"Não consegui ler o desempenho: {e}"


def set_volume(percent: int) -> str:
    """Define o volume mestre (0-100). Só funciona no Windows (pycaw)."""
    percent = max(0, min(100, int(percent)))
    try:
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        from comtypes import CLSCTX_ALL
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = interface.QueryInterface(IAudioEndpointVolume)
        volume.SetMasterVolumeLevelScalar(percent / 100.0, None)
        return f"Volume em {percent}%."
    except Exception as e:
        return f"Não consegui ajustar o volume: {e}"


def change_volume(delta: int) -> str:
    """Aumenta/diminui o volume mestre em 'delta' pontos percentuais."""
    try:
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        from comtypes import CLSCTX_ALL
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = interface.QueryInterface(IAudioEndpointVolume)
        cur = int(round(volume.GetMasterVolumeLevelScalar() * 100))
        return set_volume(cur + delta)
    except Exception as e:
        return f"Não consegui ajustar o volume: {e}"
