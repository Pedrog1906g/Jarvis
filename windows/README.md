# JARVIS para Windows

App de mesa (desktop) do JARVIS: fica na **bandeja**, roda em **segundo plano**,
conversa por **voz** (TTS masculino SAPI + STT) e manda os comandos ao mesmo
backend do celular e do PC web. Também executa comandos locais no Windows.

## Funcionalidades (v1)
- 🔆 Ícone na bandeja (pystray) + janela de chat.
- 🎙️ Conversa por voz: fale clicando em **🎙 Falar** (push-to-talk).
- 💬 Chat em tempo real com o backend via WebSocket (`/api/ws/chat`).
- 🖥️ Comandos locais: **abrir programas**, **organizar arquivos** (Downloads),
  **mostrar desempenho** (CPU/RAM/disco).
- 🔐 Login igual ao app (usuário `owner`, acesso `nexus`).
- ▶️ Inicia com o Windows (veja "Iniciar com o Windows" abaixo).

## Como rodar (modo desenvolvimento)
```powershell
cd windows
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python nexus_app.py
```
> Precisa de microfone e de permissão de microfone. O STT usa o Google Web
> Speech (precisa de internet); o TTS é offline (SAPI do Windows).

## Gerar o .exe
```powershell
pip install pyinstaller
pyinstaller --noconsole --onefile nexus_app.py
```
O executável fica em `dist/nexus_app.exe`.

## Iniciar com o Windows
1. Copie `dist/nexus_app.exe` para uma pasta fixa (ex.: `C:\JARVIS\`).
2. Crie um atalho dele em:
   `shell:startup` (tecle Win+R, cole e Enter).
Pronto — ele sobe sozinho ao ligar o PC, na bandeja.

## Comandos de voz/exemplo
- "Jarvis, abra o Chrome"
- "Jarvis, organize meus arquivos"
- "Jarvis, qual o desempenho?"
- "Jarvis, me explique o que é uma rede neural"

## Próximos passos (extensões)
- Wake word "Jarvis" contínuo (escuta sempre ligada).
- Controle de volume/periféricos (pycaw + pywin32).
- Automações agendadas e sincronização com o Supabase (cross-device).
