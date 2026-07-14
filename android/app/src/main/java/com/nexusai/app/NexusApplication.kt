package com.nexusai.app

import android.app.Application
import com.nexusai.app.data.remote.RetrofitClient
import com.nexusai.app.data.repository.NexusRepository
import com.nexusai.app.data.store.TokenStore

class NexusApplication : Application() {

    lateinit var tokenStore: TokenStore
        private set

    val repository by lazy { NexusRepository(tokenStore) }

    override fun onCreate() {
        super.onCreate()
        tokenStore = TokenStore(this)
        RetrofitClient.rebuild(tokenStore.getServerUrl())
    }
}
