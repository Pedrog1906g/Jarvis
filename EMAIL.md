# E-mail no JARVIS (NEXUS AI)

O JARVIS envia e-mails de verdade usando SMTP. Funciona em qualquer lugar
(web, EXE no PC, APK no celular) — basta dizer ou escrever um comando como:

> "envie um email para fulano@gmail.com assunto Olá dizendo Tudo bem por aí?"

Você também pode usar o botão/endpoint direto. Para isso, o JARVIS precisa
saber os dados do seu e-mail (servidor SMTP + conta + senha).

## Opção 1 — Painel do Render (mais durável, recomendada)

1. Acesse https://dashboard.render.com e abra o serviço `nexus-api`.
2. Vá em **Environment** e preencha:
   - `EMAIL_SMTP_HOST` → ex.: `smtp.gmail.com`
   - `EMAIL_SMTP_PORT` → `587` (ou `465` se usar SSL)
   - `EMAIL_ADDRESS` → seu e-mail (ex.: `voce@gmail.com`)
   - `EMAIL_PASSWORD` → **senha de aplicativo** (não a senha normal — veja abaixo)
   - `EMAIL_SMTP_SSL` → `false` (porta 587) ou `true` (porta 465)
   - `EMAIL_FROM_NAME` → `NEXUS AI` (ou como quer que apareça)
3. Salve e espere o Render reimplantar (deploy). Pronto — já funciona.

> **Gmail:** não use a senha comum. Crie uma **Senha de aplicativo**:
> Conta Google → Segurança → Verificação em duas etapas → **Senhas de app**.
> Gere uma senha de 16 caracteres e cole em `EMAIL_PASSWORD`.

## Opção 2 — Ligar na hora (sem abrir o Render)

Chame o endpoint `POST /api/email/set_config` (somente o dono), autenticado:

```bash
curl -X POST https://nexus-api-2o1y.onrender.com/api/email/set_config \
  -H "Authorization: Bearer SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"smtp_host":"smtp.gmail.com","smtp_port":587,"address":"voce@gmail.com","password":"SENHA_DE_APP","use_ssl":false,"from_name":"NEXUS AI"}'
```

Ou peça ao JARVIS no chat: *"configurar email"* (em breve por comando de voz).

## Testar

- `GET /api/email/config` → mostra o status (sem expor a senha).
- `POST /api/email/test` → envia um e-mail de teste para o seu próprio endereço.

## Observações

- Sem configuração, o JARVIS apenas avisa que o e-mail não está configurado
  (não quebra o resto do sistema).
- A senha é guardada criptografada no banco do servidor.
- O Telegram foi removido do projeto (não faz mais parte do JARVIS).
