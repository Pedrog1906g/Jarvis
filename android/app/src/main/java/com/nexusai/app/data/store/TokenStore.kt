package com.nexusai.app.data.store

import android.content.Context
import android.content.SharedPreferences

class TokenStore(context: Context) {
    private val prefs = context.getSharedPreferences("nexus_secure", Context.MODE_PRIVATE)
    private val settings = context.getSharedPreferences("nexus_settings", Context.MODE_PRIVATE)

    fun saveToken(token: String) = prefs.edit().putString("token", token).apply()
    fun getToken(): String? = prefs.getString("token", null)
    fun clear() = prefs.edit().clear().apply()

    fun getServerUrl(): String =
        settings.getString("server_url", "http://10.0.2.2:8000") ?: "http://10.0.2.2:8000"

    fun setServerUrl(url: String) = settings.edit().putString("server_url", url).apply()
}
