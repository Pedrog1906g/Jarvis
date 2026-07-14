package com.nexusai.app.data.remote

import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import com.nexusai.app.util.NexusConfig

object RetrofitClient {
    var baseUrl: String = NexusConfig.API_BASE_URL // URL pública do backend (Render)
    var api: NexusApi = build()

    private fun build(): NexusApi = Retrofit.Builder()
        .baseUrl(baseUrl)
        .addConverterFactory(GsonConverterFactory.create())
        .build()
        .create(NexusApi::class.java)

    fun rebuild(base: String) {
        baseUrl = base.trimEnd('/')
        api = build()
    }
}
