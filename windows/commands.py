"""Comandos locais do JARVIS no Windows (sem dependências pesadas na importação)."""

import os
import re
import shutil
import subprocess
import webbrowser
import urllib.parse

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
    if re.search(r"\b(tocar|toque|ouvir|play|m[úu]sica|som)\b", t) or \
       "spotify" in t or "youtube" in t or "deezer" in t:
        return "music"
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


# ----------------------------- YouTube (melhor vídeo) -----------------------------

_STOP = set("a o e de da do das dos em no na nos nas um uma umas para com que seu sua seus su as os ao aos pela pelas pelo".split())


def _norm(s: str):
    return re.findall(r"[a-z0-9]+", (s or "").lower())


def _score(qtok, ttok) -> float:
    if not ttok:
        return 0.0
    ts = set(t for t in ttok if t not in _STOP)
    qs = set(t for t in qtok if t not in _STOP)
    if not qs:
        return 0.0
    inter = qs & ts
    j = len(inter) / len(qs | ts)
    return j * 100 + len(inter) * 5


def _yt_pairs(query: str):
    """Retorna lista de (videoId, titulo) extraídos do YouTube."""
    import requests
    try:
        html = requests.get(
            "https://www.youtube.com/results",
            params={"search_query": query},
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
            timeout=12,
        ).text
    except Exception:
        return []
    found = re.findall(
        r'"videoId":"([A-Za-z0-9_-]{11})".*?"title":\{"runs":\[\{"text":"(.*?)"\}\]',
        html, re.DOTALL)
    return found


def best_youtube_video(query: str):
    """Escolhe o vídeo que melhor combina com o pedido (não só o 1º)."""
    pairs = _yt_pairs(query)
    if not pairs:
        return None
    qtok = _norm(query)
    best, best_sc = None, -1.0
    for vid, raw in pairs:
        title = raw.replace("\\u0026", "&").replace('\\"', '"')
        sc = _score(qtok, _norm(title))
        low = title.lower()
        if "official" in low or "original" in low:
            sc += 12
        if "audio" in low or "álbum" in low or "album" in low:
            sc += 6
        if "live" in low or "ao vivo" in low:
            sc -= 6
        if any(k in low for k in ["lyrics", "letra", "karaoke", "instrumental",
                                  "remix", "cover", "tutorial", "reaction"]):
            sc -= 10
        if qtok and all(w in low for w in qtok if w not in _STOP):
            sc += 12
        if sc > best_sc:
            best_sc, best = sc, vid
    return best


# ----------------------------- Spotify (tocar de verdade) -----------------------------

def _spotify_track_id(query: str):
    """Tenta achar o ID da música no Spotify (precisa de app/website com o URI)."""
    import requests
    try:
        html = requests.get(
            "https://open.spotify.com/search/" + urllib.parse.quote(query),
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
            timeout=12,
        ).text
    except Exception:
        return None
    m = re.search(r'spotify:track:([A-Za-z0-9]+)', html)
    if m:
        return m.group(1)
    m = re.search(r'"uri":"spotify:track:([A-Za-z0-9]+)"', html)
    return m.group(1) if m else None


# ----------------------------- Play music -----------------------------

def play_music(query: str) -> str:
    """Toca música de verdade:
    - Spotify: abre a música no app (spotify:track:ID) ou a busca no app.
    - YouTube: escolhe o vídeo que melhor combina e já abre tocando.
    """
    q = (query or "").strip()
    use_spotify = "spotify" in q.lower()
    try:
        if use_spotify:
            term = q.lower().replace("spotify", "").strip()
            search = term if term else "lofi hip hop"
            tid = None
            label = search
            try:
                from spotify_auth import search_track
                res = search_track(search)
                if res:
                    tid, name, artists = res
                    label = (artists + " — " + name).strip(" —") or search
            except Exception:
                tid = None
            if tid:
                webbrowser.open("spotify:track:" + tid)
                return f"Tocando {label} no Spotify."
            # fallback: abre a busca DENTRO do app Spotify (não a tela do navegador)
            enc = urllib.parse.quote(search)
            if not webbrowser.open("spotify:search:" + enc):
                webbrowser.open("https://open.spotify.com/search/" + enc)
            return f"Abrindo {search} no Spotify."

        search = q if q else "lofi hip hop"
        vid = best_youtube_video(search)
        if vid:
            webbrowser.open(f"https://www.youtube.com/watch?v={vid}&autoplay=1")
            return f"Tocando {search} no YouTube."
        webbrowser.open("https://www.youtube.com/results?search_query=" +
                        urllib.parse.quote(search))
        return f"Abrindo música no YouTube: {search}."
    except Exception as e:
        return f"Não consegui abrir o player de música: {e}"
