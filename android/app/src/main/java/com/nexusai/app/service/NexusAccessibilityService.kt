package com.nexusai.app.service

import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.AccessibilityServiceInfo
import android.content.Intent
import android.view.accessibility.AccessibilityEvent
import android.view.accessibility.AccessibilityNodeInfo

/**
 * Serviço de Acessibilidade do NEXUS (Fase 3 — controle do celular).
 *
 * O usuário ativa manualmente em Configurações > Acessibilidade. Permite ler o
 * conteúdo da tela e tocar em elementos quando pedido por voz/comando. Nenhuma
 * informação de tela é enviada a lugar nenhum além do próprio backend (e só o
 * texto solicitado).
 */
class NexusAccessibilityService : AccessibilityService() {

    companion object {
        var instance: NexusAccessibilityService? = null
    }

    override fun onServiceConnected() {
        super.onServiceConnected()
        instance = this
        serviceInfo = AccessibilityServiceInfo().apply {
            eventTypes = AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED or
                AccessibilityEvent.TYPE_VIEW_CLICKED or
                AccessibilityEvent.TYPE_NOTIFICATION_STATE_CHANGED
            feedbackType = AccessibilityServiceInfo.FEEDBACK_GENERIC
            flags = AccessibilityServiceInfo.DEFAULT or
                AccessibilityServiceInfo.FLAG_REPORT_VIEW_IDS or
                AccessibilityServiceInfo.FLAG_RETRIEVE_INTERACTIVE_WINDOWS
            notificationTimeout = 100
        }
    }

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {}

    override fun onInterrupt() {}

    override fun onUnbind(intent: Intent?): Boolean {
        instance = null
        return super.onUnbind(intent)
    }

    /** Lê todo o texto visível na janela atual. */
    fun readScreen(): String {
        val root = rootInActiveWindow ?: return ""
        val sb = StringBuilder()
        collectText(root, sb, 0)
        return sb.toString().trim()
    }

    private fun collectText(node: AccessibilityNodeInfo?, sb: StringBuilder, depth: Int) {
        if (node == null || depth > 50) return
        val text = node.text
        val desc = node.contentDescription
        if (!text.isNullOrBlank()) sb.appendLine(text)
        if (!desc.isNullOrBlank()) sb.appendLine(desc)
        for (i in 0 until node.childCount) {
            collectText(node.getChild(i), sb, depth + 1)
        }
    }

    /** Toca no primeiro elemento clicável cujo texto/descrição contém [target]. */
    fun clickByText(target: String): Boolean {
        val root = rootInActiveWindow ?: return false
        return clickByTextRecursive(root, target.lowercase())
    }

    private fun clickByTextRecursive(node: AccessibilityNodeInfo?, target: String): Boolean {
        if (node == null) return false
        val text = (node.text ?: "").toString().lowercase()
        val desc = (node.contentDescription ?: "").toString().lowercase()
        if (text.contains(target) || desc.contains(target)) {
            if (node.isClickable) {
                node.performAction(AccessibilityNodeInfo.ACTION_CLICK)
                return true
            }
            var parent = node.parent
            while (parent != null) {
                if (parent.isClickable) {
                    parent.performAction(AccessibilityNodeInfo.ACTION_CLICK)
                    return true
                }
                parent = parent.parent
            }
        }
        for (i in 0 until node.childCount) {
            if (clickByTextRecursive(node.getChild(i), target)) return true
        }
        return false
    }

    /** Rola a tela (up/down). */
    fun scroll(direction: String): Boolean {
        val root = rootInActiveWindow ?: return false
        val action = if (direction == "up") AccessibilityNodeInfo.ACTION_SCROLL_BACKWARD
        else AccessibilityNodeInfo.ACTION_SCROLL_FORWARD
        if (root.performAction(action)) return true
        var parent = root.parent
        while (parent != null) {
            if (parent.performAction(action)) return true
            parent = parent.parent
        }
        return false
    }
}
