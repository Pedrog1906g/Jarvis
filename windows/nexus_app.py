"""JARVIS para Windows — bandeja + chat por voz com o backend NEXUS.

Execute:
    pip install -r requirements.txt
    python nexus_app.py
Gere o .exe:
    pyinstaller --noconsole --onefile nexus_app.py

O app fica na bandeja, roda em segundo plano, conversa por voz (TTS masculino
SAPI + STT) e manda os comandos ao backend (mesmo do celular/PC web). Também
executa comandos locais: abrir programas, organizar arquivos e mostrar desempenho.
"""

import os
import re
import json
import threading

import tkinter as tk
from tkinter import scrolledtext

import requests
import websocket  # pacote websocket-client

from commands import classify_command, open_program, organize_folder, system_stats
from voice import WindowsVoice

APP_NAME = "JARVIS"
CONFIG_PATH = os.path.join(os.path.expanduser("~"), "jarvis_windows_config.json")
DEFAULT_SERVER = "https://nexus-api-2o1y.onrender.com"


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
                return True
            return False
        except Exception:
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
            return True
        except Exception:
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
        except Exception:
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
        self._build_ui()
        self.backend.on_text = self._bot_chunk
        self.backend.on_done = self._bot_finish
        self.backend.on_status = self._set_status
        self._auto_connect()

    # ----- UI -----
    def _build_ui(self):
        self.root = tk.Tk()
        self.root.title(APP_NAME + " — NEXUS AI")
        self.root.geometry("480x640")
        self.root.protocol("WM_DELETE_WINDOW", lambda: self.root.withdraw())

        self.chat = scrolledtext.ScrolledText(
            self.root, wrap=tk.WORD, state=tk.DISABLED,
            bg="#03060d", fg="#dff3ff", font=("Segoe UI", 11))
        self.chat.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        self.input = tk.Entry(self.root, bg="#0a0f1a", fg="#dff3ff",
                               font=("Segoe UI", 12))
        self.input.pack(fill=tk.X, padx=8, pady=(0, 4))
        self.input.bind("<Return>", lambda e: self._send())

        bar = tk.Frame(self.root)
        bar.pack(fill=tk.X, padx=8, pady=(0, 8))
        tk.Button(bar, text="Enviar", command=self._send).pack(side=tk.LEFT)
        tk.Button(bar, text="🎙 Falar", command=self._push_to_talk).pack(side=tk.LEFT, padx=4)
        tk.Button(bar, text="⚙ Config", command=self._open_settings).pack(side=tk.LEFT, padx=4)

    def _set_status(self, ok):
        try:
            self.root.title(APP_NAME + (" — online" if ok else " — offline"))
        except Exception:
            pass

    def _user(self, text):
        self.chat.configure(state=tk.NORMAL)
        self.chat.insert(tk.END, "Você: " + text + "\n")
        self.chat.configure(state=tk.DISABLED)
        self.chat.see(tk.END)

    def _bot_chunk(self, text):
        self.chat.configure(state=tk.NORMAL)
        if not self._bot_open:
            self.chat.insert(tk.END, "JARVIS: ")
            self._bot_open = True
            self._bot_buf = ""
        self.chat.insert(tk.END, text)
        self._bot_buf += text
        self.chat.configure(state=tk.DISABLED)
        self.chat.see(tk.END)

    def _bot_finish(self):
        self.chat.configure(state=tk.NORMAL)
        self.chat.insert(tk.END, "\n")
        self.chat.configure(state=tk.DISABLED)
        self._bot_open = False
        self.voice.speak(self._bot_buf)

    # ----- Ações -----
    def _send(self):
        text = self.input.get().strip()
        if not text:
            return
        self.input.delete(0, tk.END)
        self._user(text)

        intent = classify_command(text)
        if intent == "open_app":
            m = re.search(r"(abrir|abre|execute|rodar|iniciar)\s+(.+)", text, re.I)
            name = m.group(2) if m else text
            result = open_program(name)
        elif intent == "organize":
            result = organize_folder(None)
        elif intent == "stats":
            result = system_stats()
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
        text = self.voice.listen_once()
        if text:
            self.input.delete(0, tk.END)
            self.input.insert(0, text)
            self._send()

    def _auto_connect(self):
        if self.backend.login(self.cfg.get("server", DEFAULT_SERVER),
                              self.cfg.get("username", "owner"),
                              self.cfg.get("passphrase", "nexus")):
            self.backend.connect_ws()
            self._set_status(True)
            self._bot_chunk("JARVIS online. Escreva ou clique em 🎙 Falar.")
            self._bot_finish()
        else:
            self._set_status(False)
            self._bot_chunk("Sem conexão. Abra ⚙ Config e ajuste servidor/login.")
            self._bot_finish()

    def _open_settings(self):
        win = tk.Toplevel(self.root)
        win.title("Configurações do JARVIS")
        win.geometry("380x200")

        tk.Label(win, text="Servidor").pack(anchor="w", padx=10, pady=(8, 0))
        srv = tk.Entry(win)
        srv.insert(0, self.cfg.get("server", DEFAULT_SERVER))
        srv.pack(fill=tk.X, padx=10)

        tk.Label(win, text="Usuário").pack(anchor="w", padx=10, pady=(6, 0))
        usr = tk.Entry(win)
        usr.insert(0, self.cfg.get("username", "owner"))
        usr.pack(fill=tk.X, padx=10)

        tk.Label(win, text="Frase de acesso").pack(anchor="w", padx=10, pady=(6, 0))
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

            def quit_(ic, item):
                ic.stop()
                self.root.after(0, self.root.destroy)

            icon.menu = pystray.Menu(
                pystray.MenuItem("Mostrar", show),
                pystray.MenuItem("🎙 Falar", talk),
                pystray.MenuItem("Sair", quit_),
            )
            threading.Thread(target=icon.run, daemon=True).start()
        except Exception:
            pass

    def run(self):
        self._start_tray()
        self.root.mainloop()


if __name__ == "__main__":
    App().run()
