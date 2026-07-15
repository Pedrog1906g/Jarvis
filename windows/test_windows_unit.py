"""Testes unitários do app Windows (lógica pura, sem Windows/GUI necessário)."""
from commands import classify_command


def test_classify_open():
    assert classify_command("abra o chrome") == "open_app"
    assert classify_command("abrir calculadora") == "open_app"
    assert classify_command("execute o notepad") == "open_app"


def test_classify_organize():
    assert classify_command("organize a pasta downloads") == "organize"
    assert classify_command("organizar meus arquivos") == "organize"


def test_classify_stats():
    assert classify_command("qual o desempenho") == "stats"
    assert classify_command("cpu") == "stats"
    assert classify_command("memória") == "stats"


def test_classify_volume_and_reminder():
    assert classify_command("aumente o volume") == "volume"
    assert classify_command("crie um lembrete") == "reminder"


def test_classify_chat_default():
    assert classify_command("qual seu nome?") == "chat"
    assert classify_command("me explique o que é IA") == "chat"
