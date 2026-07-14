package com.nexusai.app.data.store

import android.content.Context
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey

class TokenStore(context: Context) {

    private val masterKey = MasterKey.Builder(context)
        .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
        .build()

    private val secure = EncryptedSharedPreferences.create(
        context,
        "nexus_secure",
        masterKey,
        EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
        EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
    )

    private val settings = context.getSharedPreferences("nexus_settings", Context.MODE_PRIVATE)

    fun saveToken(token: String) = secure.edit().putString("token", token).apply()
    fun getToken(): String? = secure.getString("token", null)
    fun clear() = secure.edit().clear().apply()

    fun getServerUrl(): String =
        settings.getString("server_url", "http://10.0.2.2:8000") ?: "http://10.0.2.2:8000"

    fun setServerUrl(url: String) = settings.edit().putString("server_url", url).apply()
}
