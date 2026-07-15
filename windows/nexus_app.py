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

import tkinter as tk
from tkinter import scrolledtext

import requests
import websocket  # pacote websocket-client

from commands import (classify_command, open_program, organize_folder,
                      system_stats, set_volume, change_volume, play_music)
from voice import WindowsVoice

APP_NAME = "JARVIS"
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
        self.root.geometry("480x680")
        self.root.configure(bg="#02040a")
        self.root.protocol("WM_DELETE_WINDOW", lambda: self.root.withdraw())

        hdr = tk.Frame(self.root, bg="#02040a")
        hdr.pack(fill=tk.X, padx=8, pady=(8, 0))
        self._build_reactor(hdr)
        tk.Label(hdr, text="⚡ JARVIS  •  NEXUS AI",
                 bg="#02040a", fg="#5fe0ff",
                 font=("Segoe UI", 14, "bold")).pack(side=tk.LEFT)

        self.chat = scrolledtext.ScrolledText(
            self.root, wrap=tk.WORD, state=tk.DISABLED,
            bg="#03060d", fg="#dff3ff", font=("Segoe UI", 11),
            insertbackground="#5fe0ff")
        self.chat.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        self.chat.tag_config("user", foreground="#19f0ff")
        self.chat.tag_config("jarvis", foreground="#7c4dff")

        self.input = tk.Entry(self.root, bg="#0a0f1a", fg="#dff3ff",
                              font=("Segoe UI", 12), insertbackground="#5fe0ff")
        self.input.pack(fill=tk.X, padx=8, pady=(0, 4))
        self.input.bind("<Return>", lambda e: self._send())

        bar = tk.Frame(self.root, bg="#02040a")
        bar.pack(fill=tk.X, padx=8, pady=(0, 4))
        tk.Button(bar, text="Enviar", command=self._send).pack(side=tk.LEFT)
        tk.Button(bar, text="🎙 Falar", command=self._push_to_talk).pack(side=tk.LEFT, padx=4)
        tk.Button(bar, text="🎙 Jarvis", command=self.toggle_continuous).pack(side=tk.LEFT, padx=4)
        tk.Button(bar, text="⚙ Config", command=self._open_settings).pack(side=tk.LEFT, padx=4)

        self.status = tk.Label(self.root, text="Iniciando...", bg="#02040a",
                               fg="#5fe0ff", font=("Segoe UI", 9), anchor="w")
        self.status.pack(fill=tk.X, padx=8, pady=(0, 6))
        self._start_pulse()

    def _build_reactor(self, parent):
        try:
            import math
            c = tk.Canvas(parent, width=72, height=72, bg="#02040a", highlightthickness=0)
            c.pack(side=tk.LEFT, padx=(0, 12))
            self._reactor = c
            self._reactor_angle = 0

            def draw():
                try:
                    c.delete("all")
                    cx, cy, r = 36, 36, 32
                    c.create_oval(cx - r, cy - r, cx + r, cy + r, outline="#0a4a5a", width=2)
                    c.create_oval(cx - 23, cy - 23, cx + 23, cy + 23, outline="#0a6c8c", width=1)
                    a = self._reactor_angle
                    # varredura (radar)
                    c.create_arc(cx - r, cy - r, cx + r, cy + r, start=a, extent=70,
                                outline="#00e5ff", width=2, style="arc")
                    c.create_arc(cx - 23, cy - 23, cx + 23, cy + 23, start=-a * 1.3, extent=50,
                                outline="#7c4dff", width=1, style="arc")
                    # íris central
                    c.create_oval(cx - 12, cy - 12, cx + 12, cy + 12, outline="#19f0ff", width=1)
                    c.create_oval(cx - 4, cy - 4, cx + 4, cy + 4, fill="#19f0ff", outline="")
                    # linha de varredura
                    ang = math.radians(a)
                    c.create_line(cx, cy, cx + r * math.cos(ang), cy + r * math.sin(ang),
                                  fill="#00e5ff", width=1)
                    self._reactor_angle = (a + 6) % 360
                except Exception:
                    return
                self.root.after(60, draw)
            self.root.after(60, draw)
        except Exception:
            pass

    def _start_pulse(self):
        try:
            state = {"on": False}

            def tick():
                try:
                    state["on"] = not state["on"]
                    self.status.configure(fg="#5fe0ff" if state["on"] else "#1b9fd6")
                except Exception:
                    return
                self.root.after(900, tick)
            self.root.after(900, tick)
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
        text = self.voice.listen_once()
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
            self._append_bot_chunk("Modo contínuo 'Jarvis' desligado.")
            self._bot_finish()
            self._set_statusbar("Microfone parado")
            return
        ok = self.voice.start_continuous(self._on_phrase)
        self._continuous = ok
        if ok:
            self._append_bot_chunk("Modo 'Jarvis' ligado. Diga 'Jarvis' e seu comando a qualquer momento.")
            self._bot_finish()
            self._set_statusbar("🎙 Ouvindo 'Jarvis'...")
            log.info("wake word ligado")
        else:
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

    def run(self):
        self._start_tray()
        # liga o modo 'Jarvis' sozinho após a janela abrir (sem precisar clicar)
        self.root.after(1500, self._auto_wake)
        self.root.mainloop()


if __name__ == "__main__":
    App().run()
