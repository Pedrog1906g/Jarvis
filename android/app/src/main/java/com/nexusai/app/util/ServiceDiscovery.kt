package com.nexusai.app.util

import android.content.Context
import android.net.nsd.NsdManager
import android.net.nsd.NsdServiceInfo
import java.util.concurrent.ConcurrentHashMap

/**
 * Descoberta do backend NEXUS na LAN via NSD/mDNS (serviço `_nexus._tcp`).
 * Permite que o app conecte automaticamente sem digitar o IP da máquina.
 */
object ServiceDiscovery {

    private const val SERVICE_TYPE = "_nexus._tcp."

    fun discover(context: Context, onResult: (List<String>) -> Unit) {
        val nsd = context.getSystemService(Context.NSD_SERVICE) as? NsdManager ?: return
        val found = ConcurrentHashMap<String, String>()

        val resolveListener = object : NsdManager.ResolveListener {
            override fun onResolveFailed(service: NsdServiceInfo?, error: Int) {}
            override fun onServiceResolved(service: NsdServiceInfo?) {
                service ?: return
                val host = service.host?.hostAddress ?: return
                val url = "http://$host:${service.port}"
                found[host] = url
                onResult(found.values.toList())
            }
        }

        val discoveryListener = object : NsdManager.DiscoveryListener {
            override fun onDiscoveryStarted(regType: String?) {}
            override fun onDiscoveryStopped(regType: String?) {}
            override fun onServiceFound(service: NsdServiceInfo?) {
                service ?: return
                if (service.serviceType.contains("nexus", ignoreCase = true)) {
                    try { nsd.resolveService(service, resolveListener) } catch (_: Exception) {}
                }
            }
            override fun onServiceLost(service: NsdServiceInfo?) {}
            override fun onStartDiscoveryFailed(type: String?, error: Int) {
                try { nsd.stopServiceDiscovery(this) } catch (_: Exception) {}
            }
            override fun onStopDiscoveryFailed(type: String?, error: Int) {
                try { nsd.stopServiceDiscovery(this) } catch (_: Exception) {}
            }
        }

        try {
            nsd.discoverServices(SERVICE_TYPE, NsdManager.PROTOCOL_DNS_SD, discoveryListener)
        } catch (_: Exception) {
            onResult(emptyList())
        }
    }
}
