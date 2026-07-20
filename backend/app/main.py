python
from fastapi import FastAPI
from pydantic import BaseModel
from transformers import pipeline
import pyttsx3

app = FastAPI()

# Configuração do sintetizador de voz
engine = pyttsx3.init()
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[0].id)  # Alterado para a primeira voz disponível, que geralmente é mais grave e masculina
engine.setProperty('rate', 150)  # Taxa de fala ajustada para um valor mais razoável

class Texto(BaseModel):
    texto: str

@app.post("/sintetizar")
def sintetizar_voz(texto: Texto):
    engine.say(texto.texto)
    engine.runAndWait()
    return {"mensagem": "Voz sintetizada com sucesso"}

@app.get("/teste")
def teste():
    return {"mensagem": "API funcionando corretamente"}