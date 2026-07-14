---
name: nexus-android
description: App Android nativo do NEXUS — telas, wake word, controle do celular e build via CI
triggers:
  - "app do nexus"
  - "android do nexus"
  - "como controlar o celular"
version: 1.1.0
tags: [nexus, android, kotlin, compose]
---

# App Android (NEXUS AI)

Kotlin + Jetpack Compose. APK gerado pelo **GitHub Actions** (CI) a cada mudança em
`main` e publicado como Release (`nexus-ai-<n>`). Link estável:
`.../releases/latest/download/app-debug.apk`.

## Telas (Compose)
Chat, Histórico, Lembretes, Dispositivos, Controle, Auto-melhoria, Ajustes (menu em `AppScaffold`).

## Fase 1 — Armazenamento seguro
`TokenStore.kt` usa **EncryptedSharedPreferences** (Android Keystore, AES-256-GCM).
Nada em texto puro. Ver [[Segurança]].

## Fase 2 — Wake word "Nexus"
`NexusVoiceService.kt` (ForegroundService): escuta "nexus", fala "Pronto", captura o
comando e responde por TTS. Comandos locais priorizam `NexusController`.
`BootReceiver.kt` reativa o serviço após reinício/atualização se o toggle estiver ligado.

## Fase 3 — Controle do celular
- `NexusAccessibilityService.kt`: ler tela, tocar em texto, rolar.
- `NexusNotificationListener.kt`: ler notificações.
- `NexusController.kt`: abrir apps e comandos locais.
- Manifest com permissões `QUERY_ALL_PACKAGES`, `REQUEST_IGNORE_BATTERY_OPTIMIZATIONS`,
  `allowBackup="false"` e XML de config do Accessibility.

## Permissões
Concedidas **manualmente** pelo dono nas configurações do Android (acessibilidade,
notificações, bateria). O app não sai do aparelho além do próprio backend.

Veja também: [[Segurança]], [[Arquitetura]], [[Backend FastAPI]].
