"""JARVIS para Windows — bandeja + chat por voz com o backend NEXUS.

Execute:
    pip install -r requirements.txt
    python nexus_app.py
Gere o .exe:
    pyinstaller --noconsole --onefile nexus_app.py

O app fica na bandeja, liga sozinho no modo "Jarvis" (wake word) ao abrir e
responde por voz (TTS masculino SAPI + STT). Também executa comandos locais:
abrir programas, organizar arquivos, mostrar desempenho e controlar o volume.
"""

import os
import re
import json
import logging
import threading
import queue

import tkinter as tk
from tkinter import scrolledtext

import requests
import websocket  # pacote websocket-client

from commands import (classify_command, open_program, organize_folder,
                      system_stats, set_volume, change_volume, play_music,
                      take_screenshot, get_weather, web_search, lock_screen, get_clipboard)
from voice import WindowsVoice

APP_NAME = "JARVIS"
VERSION = "1.0.0"
CONFIG_PATH = os.path.join(os.path.expanduser("~"), "jarvis_windows_config.json")
DEFAULT_SERVER = "https://nexus-api-2o1y.onrender.com"
LOG_PATH = os.path.join(os.path.expanduser("~"), "jarvis_windows.log")

logging.basicConfig(filename=LOG_PATH, level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("jarvis")


# ----------------------------- Configuração -----------------------------
def load_config():
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"server": DEFAULT_SERVER, "username": "owner", "passphrase": "nexus"}


def save_config(cfg):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
    except Exception:
        pass


# ----------------------------- Backend -----------------------------
class Backend:
    def __init__(self):
        self.server = DEFAULT_SERVER
        self.token = None
        self.ws = None
        self.on_text = None
        self.on_done = None
        self.on_status = None

    def login(self, server, username, passphrase):
        self.server = server.rstrip("/")
        try:
            r = requests.post(self.server + "/api/auth/login",
                              json={"username": username, "passphrase": passphrase},
                              timeout=20)
            if r.status_code == 200:
                self.token = r.json().get("access_token")
                log.info("login OK")
                return True
            log.warning("login falhou: %s", r.status_code)
            return False
        except Exception as e:
            log.warning("login erro: %s", e)
            return False

    def connect_ws(self):
        if not self.token:
            return False
        url = self.server.replace("http://", "ws://").replace("https://", "wss://")
        url += "/api/ws/chat?token=" + self.token
        try:
            self.ws = websocket.WebSocketApp(
                url, on_open=self._on_open, on_message=self._on_message,
                on_error=self._on_error, on_close=self._on_close)
            threading.Thread(target=self.ws.run_forever, daemon=True).start()
            log.info("ws conectando %s", url[:60])
            return True
        except Exception as e:
            log.warning("ws erro: %s", e)
            return False

    def _on_open(self, ws):
        if self.on_status:
            self.on_status(True)

    def _on_message(self, ws, raw):
        try:
            m = json.loads(raw)
        except Exception:
            return
        if m.get("type") == "delta" and self.on_text:
            self.on_text(m.get("content", ""))
        elif m.get("type") == "done" and self.on_done:
            self.on_done()

    def _on_error(self, ws, e):
        log.warning("ws on_error: %s", e)
        if self.on_status:
            self.on_status(False)

    def _on_close(self, ws, *a):
        if self.on_status:
            self.on_status(False)

    def send(self, text, conv_id=None):
        if not self.ws:
            return False
        try:
            self.ws.send(json.dumps({
                "type": "message", "content": text, "conversation_id": conv_id}))
            return True
        except Exception as e:
            log.warning("ws send erro: %s", e)
            return False


# ----------------------------- App (GUI + bandeja) -----------------------------
class App:
    def __init__(self):
        self.cfg = load_config()
        self.voice = WindowsVoice()
        self.backend = Backend()
        self.conv_id = None
        self._bot_open = False
        self._bot_buf = ""
        self._continuous = False
        self._listening = False
        self._main_thread = threading.main_thread()
        self._tts_queue = queue.Queue()
        self._build_ui()
        self.backend.on_text = self._bot_chunk
        self.backend.on_done = self._bot_finish
        self.backend.on_status = self._set_status
        log.info("voz selecionada: %s", self.voice.voice_name())
        self._auto_connect()

    # ----- UI -----
    def _build_ui(self):
        self.root = tk.Tk()
        self.root.title(APP_NAME + " — NEXUS AI")
        self.root.geometry("540x760")
        self.root.configure(bg="#02040a")
        self.root.protocol("WM_DELETE_WINDOW", lambda: self.root.withdraw())

        # ---- Fundo HUD (grade + cantos) ----
        self._bg = tk.Canvas(self.root, bg="#02040a", highlightthickness=0)
        self._bg.place(x=0, y=0, relwidth=1, relheight=1)
        self.root.bind("<Configure>", lambda e: self._draw_bg())

        # ---- Cabeçalho ----
        hdr = tk.Frame(self.root, bg="#02040a")
        hdr.pack(fill=tk.X, padx=12, pady=(12, 0))
        self._build_reactor(hdr)
        title_f = tk.Frame(hdr, bg="#02040a")
        title_f.pack(side=tk.LEFT, padx=(16, 0))
        tk.Label(title_f, text="J A R V I S", bg="#02040a", fg="#5fe0ff",
                 font=("Segoe UI", 24, "bold")).pack(anchor="w")
        tk.Label(title_f, text="NEXUS AI  •  ASSISTENTE PESSOAL", bg="#02040a",
                 fg="#7c4dff", font=("Segoe UI", 9, "bold")).pack(anchor="w")

        # ---- Chat ----
        self.chat = scrolledtext.ScrolledText(
            self.root, wrap=tk.WORD, state=tk.DISABLED,
            bg="#03060d", fg="#dff3ff", font=("Segoe UI", 11),
            insertbackground="#5fe0ff", relief="flat", borderwidth=0)
        self.chat.pack(fill=tk.BOTH, expand=True, padx=14, pady=12)
        self.chat.tag_config("user", foreground="#19f0ff")
        self.chat.tag_config("jarvis", foreground="#7c4dff")

        # ---- Entrada ----
        self.input = tk.Entry(self.root, bg="#0a0f1a", fg="#dff3ff",
                              font=("Segoe UI", 12), insertbackground="#5fe0ff",
                              relief="flat")
        self.input.pack(fill=tk.X, padx=14, pady=(0, 8))
        self.input.bind("<Return>", lambda e: self._send())

        # ---- Barra de botões ----
        bar = tk.Frame(self.root, bg="#02040a")
        bar.pack(fill=tk.X, padx=14, pady=(0, 6))
        tk.Button(bar, text="Enviar", command=self._send, width=9,
                  bg="#0a2a33", fg="#5fe0ff", relief="flat",
                  activebackground="#103a47",
                  font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)
        tk.Button(bar, text="🎙 Falar", command=self._push_to_talk, width=10,
                  bg="#0a2a33", fg="#5fe0ff", relief="flat",
                  activebackground="#103a47",
                  font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT, padx=4)
        tk.Button(bar, text="🎙 Jarvis", command=self.toggle_continuous, width=11,
                  bg="#1a1030", fg="#b388ff", relief="flat",
                  activebackground="#241646",
                  font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT, padx=4)
        tk.Button(bar, text="⚙ Config", command=self._open_settings, width=10,
                  bg="#0a2a33", fg="#5fe0ff", relief="flat",
                  activebackground="#103a47",
                  font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT, padx=4)

        self.status = tk.Label(self.root, text="Iniciando...", bg="#02040a",
                               fg="#5fe0ff", font=("Segoe UI", 9), anchor="w")
        self.status.pack(fill=tk.X, padx=14, pady=(0, 8))

        self._draw_bg()
        self._pump_tts()  # inicia a fila de fala na thread principal

    def _draw_bg(self):
        try:
            c = self._bg
            c.delete("all")
            w = c.winfo_width() or 540
            h = c.winfo_height() or 760
            for x in range(0, w, 40):
                c.create_line(x, 0, x, h, fill="#06161d", width=1)
            for y in range(0, h, 40):
                c.create_line(0, y, w, y, fill="#06161d", width=1)
            L, m, col = 26, 12, "#00e5ff"
            for (cx, cy, dx, dy) in [(m, m, 1, 1), (w - m, m, -1, 1),
                                     (m, h - m, 1, -1), (w - m, h - m, -1, -1)]:
                c.create_line(cx, cy, cx + L * dx, cy, fill=col, width=2)
                c.create_line(cx, cy, cx, cy + L * dy, fill=col, width=2)
        except Exception:
            pass

    def _build_reactor(self, parent):
        try:
            import math
            SIZE = 150
            c = tk.Canvas(parent, width=SIZE, height=SIZE, bg="#02040a", highlightthickness=0)
            c.pack(side=tk.LEFT)
            self._reactor = c
            self._reactor_angle = 0

            def draw():
                try:
                    c.delete("all")
                    cx = cy = SIZE / 2
                    r = SIZE / 2 - 6
                    listening = getattr(self, "_listening", False)
                    cyan = "#00e5ff"
                    violet = "#7c4dff"
                    a = self._reactor_angle
                    # anéis base
                    c.create_oval(cx - r, cy - r, cx + r, cy + r, outline="#0a4a5a", width=2)
                    c.create_oval(cx - r * 0.78, cy - r * 0.78, cx + r * 0.78, cy + r * 0.78,
                                 outline="#0a6c8c", width=1)
                    # marcações (ticks) 60
                    for i in range(60):
                        ang = math.radians(i * 6)
                        major = i % 5 == 0
                        r1 = r
                        r2 = r - (10 if major else 5)
                        c.create_line(cx + r1 * math.cos(ang), cy + r1 * math.sin(ang),
                                      cx + r2 * math.cos(ang), cy + r2 * math.sin(ang),
                                      fill=cyan if major else "#1b6d7a",
                                      width=2 if major else 1)
                    # varredura de radar (fatias)
                    c.create_arc(cx - r, cy - r, cx + r, cy + r, start=a, extent=70,
                                outline=cyan, width=2, style="arc")
                    c.create_arc(cx - r * 0.78, cy - r * 0.78, cx + r * 0.78, cy + r * 0.78,
                                start=-a * 1.3, extent=50, outline=violet, width=1, style="arc")
                    # íris central + núcleo brilhante
                    c.create_oval(cx - 22, cy - 22, cx + 22, cy + 22, outline=cyan, width=1)
                    c.create_oval(cx - 13, cy - 13, cx + 13, cy + 13, outline=violet, width=1)
                    core = violet if listening else cyan
                    for rr, wdt in [(8, 3), (5, 5), (2, 8)]:
                        c.create_oval(cx - rr, cy - rr, cx + rr, cy + rr,
                                      outline=core, width=wdt)
                    c.create_oval(cx - 3, cy - 3, cx + 3, cy + 3, fill=core, outline="")
                    # linha de varredura
                    ang = math.radians(a)
                    c.create_line(cx, cy, cx + r * math.cos(ang), cy + r * math.sin(ang),
                                  fill=cyan, width=1)
                    self._reactor_angle = (a + 6) % 360
                except Exception:
                    return
                self.root.after(60, draw)
            self.root.after(60, draw)
        except Exception:
            pass


    def _set_status(self, ok):
        try:
            self.root.title(APP_NAME + (" — online" if ok else " — offline"))
            self._set_statusbar("Conectado" if ok else "Sem conexão")
        except Exception:
            pass

    def _set_statusbar(self, text):
        try:
            self.status.configure(text=text)
        except Exception:
            pass

    def _user(self, text):
        self.chat.configure(state=tk.NORMAL)
        self.chat.insert(tk.END, "Você: " + text + "\n", "user")
        self.chat.configure(state=tk.DISABLED)
        self.chat.see(tk.END)

    def _bot_chunk(self, text):
        self.chat.configure(state=tk.NORMAL)
        if not self._bot_open:
            self.chat.insert(tk.END, "JARVIS: ", "jarvis")
            self._bot_open = True
            self._bot_buf = ""
        self.chat.insert(tk.END, text)
        self._bot_buf += text
        self.chat.configure(state=tk.DISABLED)
        self.chat.see(tk.END)

    def _append_bot_chunk(self, text):
        # referência usada pelo modo contínuo "Jarvis"
        self._bot_chunk(text)

    # ----- Fala (TTS) na thread principal -----
    # O pyttsx3 (SAPI do Windows) travA se for chamado de uma thread que não é a
    # principal. Por isso enfileiramos o texto e a thread principal consome/roteia.
    def _speak(self, text: str):
        if not text:
            return
        self._tts_queue.put(text)

    def _pump_tts(self):
        try:
            while not self._tts_queue.empty():
                text = self._tts_queue.get_nowait()
                if text:
                    self.voice.speak(text)
        except Exception:
            pass
        try:
            self.root.after(150, self._pump_tts)
        except Exception:
            pass

    def _bot_finish(self):
        self.chat.configure(state=tk.NORMAL)
        self.chat.insert(tk.END, "\n")
        self.chat.configure(state=tk.DISABLED)
        self._bot_open = False
        self._speak(self._bot_buf)

    # ----- Ações -----
    def _send(self):
        text = self.input.get().strip()
        if not text:
            return
        self.input.delete(0, tk.END)
        self._user(text)

        intent = classify_command(text)
        if intent == "open_app":
            m = re.search(r"(abrir|abre|abra|execute|rodar|iniciar|inicie)\s+(.+)", text, re.I)
            name = m.group(2) if m else text
            result = open_program(name)
        elif intent == "organize":
            result = organize_folder(None)
        elif intent == "stats":
            result = system_stats()
        elif intent == "volume":
            result = self._handle_volume(text)
        elif intent == "music":
            result = play_music(text)
        elif intent == "screenshot":
            result = take_screenshot()
        elif intent == "weather":
            # Extrai nome da cidade se mencionado
            m = re.search(r"(?:em|para|de|do|da)\s+([A-Za-z\u00C0-\u024F\s]+)", text, re.I)
            city = m.group(1).strip() if m else None
            result = get_weather(city)
        elif intent == "search":
            query = re.sub(r"\b(pesquisar|pesquise|buscar|busque|googlar|google|pesquisa|sobre|por)\b", "", text, flags=re.I).strip()
            result = web_search(query or text)
        elif intent == "lock":
            result = lock_screen()
        elif intent == "clipboard":
            result = get_clipboard()
        else:
            result = None

        if result is not None:
            self._bot_chunk(result)
            self._bot_finish()
            return

        if not self.backend.token:
            self._bot_chunk("Faça login nas configurações primeiro.")
            self._bot_finish()
            return
        self.backend.send(text, self.conv_id)

    def _push_to_talk(self):
        self._set_statusbar("Ouvindo... (fale agora)")
        self._listening = True
        try:
            text = self.voice.listen_once()
        finally:
            self._listening = False
        if text:
            self.input.delete(0, tk.END)
            self.input.insert(0, text)
            self._send()
        else:
            self._set_statusbar("Não entendi. Tente de novo.")

    # ----- Wake word "Jarvis" contínuo -----
    def toggle_continuous(self):
        if self._continuous:
            self.voice.stop_continuous()
            self._continuous = False
            self._listening = False
            self._append_bot_chunk("Modo contínuo 'Jarvis' desligado.")
            self._bot_finish()
            self._set_statusbar("Microfone parado")
            return
        ok = self.voice.start_continuous(self._on_phrase)
        self._continuous = ok
        if ok:
            self._listening = True
            self._append_bot_chunk("Modo 'Jarvis' ligado. Diga 'Jarvis' e seu comando a qualquer momento.")
            self._bot_finish()
            self._set_statusbar("🎙 Ouvindo 'Jarvis'...")
            log.info("wake word ligado")
        else:
            self._listening = False
            self._append_bot_chunk("Não consegui iniciar o reconhecimento contínuo (verifique o microfone).")
            self._bot_finish()
            self._set_statusbar("Erro no microfone")

    def _auto_wake(self):
        if not self._continuous:
            self.toggle_continuous()

    def _on_phrase(self, text):
        t = (text or "").lower()
        log.info("frase reconhecida: %s", text)
        self._set_statusbar("🎙 Ouvi: " + (text or "")[:60])
        if "jarvis" in t or "nexus" in t:
            cmd = re.sub(r"\b(jarvis|nexus)\b", "", t, flags=re.I).strip()
            if cmd:
                self.root.after(0, self._send_phrase, cmd)
            else:
                self.root.after(0, self._ack)

    def _send_phrase(self, cmd):
        self.input.delete(0, tk.END)
        self.input.insert(0, cmd)
        self._send()

    def _ack(self):
        self._append_bot_chunk("Às ordens. Diga seu comando.")
        self._bot_finish()

    def _handle_volume(self, text):
        m = re.search(r"(\d+)\s*%", text)
        if m:
            return set_volume(int(m.group(1)))
        if "aument" in text or "sobe" in text or "suba" in text or "maior" in text:
            return change_volume(15)
        if "diminu" in text or "baix" in text or "menor" in text:
            return change_volume(-15)
        return set_volume(50)

    def _auto_connect(self):
        if self.backend.login(self.cfg.get("server", DEFAULT_SERVER),
                              self.cfg.get("username", "owner"),
                              self.cfg.get("passphrase", "nexus")):
            self.backend.connect_ws()
            self._set_status(True)
            self._bot_chunk("JARVIS online. Diga 'Jarvis' para falar comigo, ou escreva abaixo.")
            self._bot_finish()
            self.root.after(1500, self.check_for_update)
        else:
            self._set_status(False)
            self._bot_chunk("Sem conexão. Abra ⚙ Config e ajuste servidor/login.")
            self._bot_finish()

    def _open_settings(self):
        win = tk.Toplevel(self.root)
        win.title("Configurações do JARVIS")
        win.geometry("380x220")
        win.configure(bg="#02040a")

        tk.Label(win, text="Servidor", bg="#02040a", fg="#5fe0ff").pack(anchor="w", padx=10, pady=(8, 0))
        srv = tk.Entry(win)
        srv.insert(0, self.cfg.get("server", DEFAULT_SERVER))
        srv.pack(fill=tk.X, padx=10)

        tk.Label(win, text="Usuário", bg="#02040a", fg="#5fe0ff").pack(anchor="w", padx=10, pady=(6, 0))
        usr = tk.Entry(win)
        usr.insert(0, self.cfg.get("username", "owner"))
        usr.pack(fill=tk.X, padx=10)

        tk.Label(win, text="Frase de acesso", bg="#02040a", fg="#5fe0ff").pack(anchor="w", padx=10, pady=(6, 0))
        pwd = tk.Entry(win, show="*")
        pwd.insert(0, self.cfg.get("passphrase", "nexus"))
        pwd.pack(fill=tk.X, padx=10)

        def save():
            self.cfg = {
                "server": srv.get().strip() or DEFAULT_SERVER,
                "username": usr.get().strip() or "owner",
                "passphrase": pwd.get(),
            }
            save_config(self.cfg)
            self.backend.token = None
            self._auto_connect()
            win.destroy()

        tk.Button(win, text="Salvar e conectar", command=save).pack(pady=10)

    # ----- Bandeja -----
    def _make_icon(self):
        from PIL import Image, ImageDraw
        img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.ellipse((6, 6, 58, 58), fill=(0, 229, 255, 255))
        d.ellipse((24, 24, 40, 40), fill=(2, 16, 24, 255))
        return img

    def _start_tray(self):
        try:
            import pystray
            icon = pystray.Icon("jarvis", self._make_icon(), "JARVIS")

            def show(ic, item):
                self.root.after(0, self.root.deiconify)

            def talk(ic, item):
                threading.Thread(target=self._push_to_talk, daemon=True).start()

            def wake(ic, item):
                self.root.after(0, self.toggle_continuous)

            def quit_(ic, item):
                try:
                    self.voice.stop_continuous()
                except Exception:
                    pass
                ic.stop()
                self.root.after(0, self.root.destroy)

            icon.menu = pystray.Menu(
                pystray.MenuItem("Mostrar", show),
                pystray.MenuItem("🎙 Falar", talk),
                pystray.MenuItem("🎙 Jarvis (ligar/desligar)", wake),
                pystray.MenuItem("Sair", quit_),
            )
            threading.Thread(target=icon.run, daemon=True).start()
        except Exception as e:
            log.warning("tray erro: %s", e)

    def check_for_update(self):
        # AUTOATUALIZAÇÃO (notificação): verifica o lançamento mais novo no GitHub.
        try:
            import urllib.request, json
            url = "https://api.github.com/repos/Pedrog1906g/Jarvis/releases/latest"
            req = urllib.request.Request(url, headers={"User-Agent": "NEXUS-JARVIS"})
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.loads(r.read().decode())
            tag = data.get("tag_name", "")
            link = ""
            for a in data.get("assets", []):
                if a.get("name") == "JARVIS.exe":
                    link = a.get("browser_download_url", "")
            m = re.search(r"(\d+)", tag)
            latest = int(m.group(1)) if m else 0
            seen = self.cfg.get("last_update_seen", 0)
            if latest and latest != seen:
                self.cfg["last_update_seen"] = latest
                save_config(self.cfg)
                msg = "Nova versão disponível (%s)." % tag
                if link:
                    msg += " Baixe em: " + link
                self._append_bot_chunk(msg)
                self._bot_finish()
        except Exception:
            pass

    def run(self):
        self._start_tray()
        # liga o modo 'Jarvis' sozinho após a janela abrir (sem precisar clicar)
        self.root.after(1500, self._auto_wake)
        self.root.mainloop()


if __name__ == "__main__":
    App().run()
