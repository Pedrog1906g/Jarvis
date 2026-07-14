# Política de Segurança

## Reportando uma vulnerabilidade
Se você encontrar um problema de segurança, **não abra uma issue pública**.
Envie um e-mail para o mantenedor ou use a aba **Security → Report a vulnerability** do repositório.
Tentaremos responder em até 72h.

## Boas práticas deste projeto
- **Nunca commite segredos.** O arquivo `.env`, chaves da Groq/Spotify e bancos `*.db` estão no
  `.gitignore`. Use sempre `.env.example` como template.
- **Credencial padrão de dono:** o `OWNER_PASSPHRASE` vem como `nexus` apenas para testes locais.
  Em qualquer exposição real, altere `OWNER_PASSPHRASE` e `JWT_SECRET` no `.env`.
- **Rede:** o app Android conecta via HTTP/WS em ambiente de testes/dev. Para produção, use HTTPS
  e um domínio com TLS.
- **Tokens:** o app guarda o JWT em `SharedPreferences` (não criptografado por padrão nesta fase de
  testes). Em produção, migre para `EncryptedSharedPreferences`.
