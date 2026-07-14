package com.nexusai.app.data.remote

import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory

object RetrofitClient {
    var baseUrl: String = "http://10.0.2.2:8000" // emulador aponta para o localhost do PC
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
