package com.nexusai.app.util

/**
 * Configuração central de rede do app NEXUS.
 *
 * API_BASE_URL é a URL pública do backend (Render). Para apontar para outro
 * ambiente, basta alterar esta constante e recompilar (ou mudar em "Ajustes"
 * / tela de Login dentro do app).
 */
object NexusConfig {
    const val API_BASE_URL = "https://nexus-api.onrender.com"
}
