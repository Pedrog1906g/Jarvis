package com.nexusai.app.util

/**
 * Configuração central de rede do app NEXUS.
 *
 * API_BASE_URL aponta para o backend JARVIS (Render).
 * O usuário pode trocar a URL em "Ajustes" ou na tela de login para usar
 * um servidor local (ex.: http://192.168.0.15:5000 na mesma rede Wi-Fi).
 */
object NexusConfig {
    const val API_BASE_URL = "https://nexus-api-2o1y.onrender.com"
}
