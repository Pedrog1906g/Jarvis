package com.nexusai.app.data.store

import android.content.Context
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKeys
import com.nexusai.app.util.NexusConfig

/**
 * Armazenamento SEGURO do NEXUS.
 *
 * Tudo que for sensível (token JWT, URL do servidor, preferências) é gravado com
 * [EncryptedSharedPreferences]: a chave-mestra fica guardada no Android Keystore
 * (hardware, quando o aparelho suporta) e os valores são cifrados com AES-256-GCM.
 * Nada é salvo em texto puro no dispositivo.
 */
class TokenStore(context: Context) {

    private val masterKeyAlias = MasterKeys.getOrCreate(MasterKeys.AES256_GCM_SPEC)

    private val securePrefs = EncryptedSharedPreferences.create(
        "nexus_secure",
        masterKeyAlias,
        context,
        EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
        EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
    )

    private val settingsPrefs = EncryptedSharedPreferences.create(
        "nexus_settings",
        masterKeyAlias,
        context,
        EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
        EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
    )

    fun saveToken(token: String) = securePrefs.edit().putString("token", token).apply()
    fun getToken(): String? = securePrefs.getString("token", null)

    /** Remove só o token (usado em "Sair"). Mantém a URL do servidor e ajustes. */
    fun clearToken() = securePrefs.edit().clear().apply()

    /** Apaga tudo (token + ajustes). */
    fun clear() {
        securePrefs.edit().clear().apply()
        settingsPrefs.edit().clear().apply()
    }

    fun getServerUrl(): String =
        settingsPrefs.getString("server_url", NexusConfig.API_BASE_URL) ?: NexusConfig.API_BASE_URL

    fun setServerUrl(url: String) = settingsPrefs.edit().putString("server_url", url).apply()

    fun isWakeWordEnabled(): Boolean = settingsPrefs.getBoolean("wake_word", true)
    fun setWakeWordEnabled(v: Boolean) = settingsPrefs.edit().putBoolean("wake_word", v).apply()
}
