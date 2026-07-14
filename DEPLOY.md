# Deploy NEXUS AI — Render (Backend) + Firebase + APK Android

Este guia conecta o projeto em nuvem:

```
App Android ──HTTPS──▶ Backend FastAPI (Render) ──▶ Firebase (Auth + Firestore: usuários, histórico, memória, lembretes)
```

Tudo que o app precisa (URL, chaves) vem do Render via Environment Variables. **Nenhuma chave
do Firebase vai para dentro do APK.**

---

## 1) Backend no Render

1. Crie a conta em https://render.com e conecte este repositório GitHub (`Pedrog1906g/Jarvis`).
2. **New Web Service** → selecione o repo. O `render.yaml` já está no projeto e será lido
   automaticamente (modo Blueprint). Se preferir manual:
   - **Runtime:** Python 3.11
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Health Check Path:** `/api/system/health`
   - **Root Directory:** `backend`  ← importante, senão o módulo `app.main` não é encontrado
3. O Render gera a URL pública, ex.: `https://nexus-api.onrender.com`.
4. **Environment Variables** (painel do Render, em *Secret* quando indicado):
   - `GROQ_API_KEY` (Secret) — sua chave da Groq (https://console.groq.com/keys). Sem ela, roda em modo DEMO.
   - `JWT_SECRET` (Secret) — gere um segredo forte.
   - `OWNER_PASSPHRASE` — `nexus` (ou mude).
   - `DATABASE_URL` — `sqlite:///./nexus.db` funciona para teste. **O disco do Render é efêmero**
     (zera a cada deploy); para persistir, crie um **Postgres** no Render e cole a URL aqui, **ou**
     use o espelhamento Firestore (seção 2).
   - `AUTH_MODE` — `jwt` (padrão).
   - `FIREBASE_*` — preencher na seção 2.
5. Deploy automático a cada push na `main`. Acompanhe em **Logs**.

> O backend já escuta em `0.0.0.0` (não só localhost) e usa `$PORT` — exigência do Render. ✅

---

## 2) Firebase

1. Console Firebase (https://console.firebase.google.com) → **Add project** (ex.: `nexus-ai`).
2. **Build → Authentication → Sign-in method**: habilite **Email/Password** (e o que quiser).
3. **Build → Firestore Database**: crie um banco (modo produção ou teste).
4. **Project Settings → Service accounts → Generate new private key** → baixe o JSON.
5. No painel do **Render**, adicione as Environment Variables (Secret):
   - `FIREBASE_PROJECT_ID` = `project_id` do JSON
   - `FIREBASE_CLIENT_EMAIL` = `client_email` do JSON
   - `FIREBASE_PRIVATE_KEY` = `private_key` do JSON **inteiro**, incluindo os `\n` (cole como está)
   - `AUTH_MODE` = `jwt` (o app continua usando o login padrão; o Firebase é a "ponte" de dados)
6. O backend, ao subir, inicializa o Firebase Admin SDK e **espelha** (best-effort) no Firestore:
   - `users/{id}` — perfil
   - `conversations/{cid}/messages` — histórico da IA
   - `memory/{owner_id}` — memória de longo prazo
   - `users/{owner_id}/reminders` — lembretes

### Login via Firebase Auth (opcional, para o app)
O backend expõe `POST /api/auth/firebase` que recebe um **ID token** do Firebase Auth, valida e
emite o JWT do app (ponte Firebase → app). Para usá-lo no app Android, seria necessário integrar
o Firebase Auth SDK no app (google-services.json) e enviar o ID token para esse endpoint — etapa
futura. O caminho atual (owner/passphrase) continua funcionando.

---

## 3) App Android → Render

O APK já aponta por padrão para `https://nexus-api.onrender.com` (constante `API_BASE_URL` em
`android/app/.../util/NexusConfig.kt`). Para reconectar em outro ambiente, basta mudar essa
constante e recompilar — ou alterar a URL em **Ajustes / tela de Login** dentro do app.

1. Gere o APK via GitHub Actions (já configurado) ou Android Studio.
2. Instale no celular e abra.
3. Na tela de Login, o servidor já vem `https://nexus-api.onrender.com`. Toque **Testar** → deve
   mostrar `✅ Conectado`. Depois **Entrar** (`owner` / `nexus`).
4. Em rede local (sem nuvem), use **🔎 Buscar na rede** ou digite o IP da máquina.

---

## 4) Segurança

- ✅ **HTTPS**: o Render termina HTTPS na URL pública; o app usa `https://`.
- ✅ **CORS**: configurado (`*`) em `main.py`.
- ✅ **Auth por token**: JWT em todas as rotas protegidas (`get_current_user`).
- ✅ **Sem chaves no APK**: `FIREBASE_*` ficam só nas Environment Variables do Render.
- ✅ **Validação**: login valida a passphrase; o caminho Firebase valida o ID token.
- Recomendação: troque `OWNER_PASSPHRASE` e `JWT_SECRET` em produção; restrinja CORS ao seu
  domínico se quiser.

---

## 5) Verificação final

- [ ] APK conecta pela internet (URL do Render)
- [ ] Usuário consegue entrar (owner/nexus ou Firebase)
- [ ] Mensagens do chat aparecem e o histórico é salvo (SQLite/Firestore)
- [ ] Com Firebase ativo, os dados aparecem no Firestore (coleção `users`, `conversations`, `memory`)
- [ ] Backend continua de pé no Render (Health Check verde)

---

## 6) Troubleshooting

- **App não conecta**: confira a URL em *Ajustes*; use **Testar** na Login. No celular, a rede
  precisa alcançar o Render (internet normal).
- **Build do Render falha**: confirme **Root Directory = `backend`** e `startCommand` exato.
- **Firebase não inicializa**: verifique `FIREBASE_PROJECT_ID/CLIENT_EMAIL/PRIVATE_KEY`; o
  `PRIVATE_KEY` precisa manter os `\n`. Erros aparecem nos Logs do Render (modo graceful).
- **Dados somem após redeploy**: use Postgres ou Firestore para persistência (disco efêmero).
