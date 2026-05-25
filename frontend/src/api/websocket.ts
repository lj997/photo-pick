/**
 * WebSocket 客户端 - 按会话 ID 建立连接，支持事件订阅，自动重连
 */
import { ref, onMounted, onUnmounted } from 'vue'

export interface WSMessage {
  type: string
  data: any
}

export function useWebSocket(sessionId: string) {
  const connected = ref(false)
  const lastMessage = ref<WSMessage | null>(null)
  let ws: WebSocket | null = null
  const listeners: Map<string, Set<(data: any) => void>> = new Map()

  function connect() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const url = `${protocol}//${window.location.host}/ws/${sessionId}`
    ws = new WebSocket(url)

    ws.onopen = () => { connected.value = true }
    ws.onclose = () => {
      connected.value = false
      setTimeout(connect, 3000)
    }
    ws.onmessage = (event) => {
      try {
        const msg: WSMessage = JSON.parse(event.data)
        lastMessage.value = msg
        const callbacks = listeners.get(msg.type)
        if (callbacks) {
          callbacks.forEach(cb => cb(msg.data))
        }
      } catch {}
    }
  }

  function on(type: string, callback: (data: any) => void) {
    if (!listeners.has(type)) {
      listeners.set(type, new Set())
    }
    listeners.get(type)!.add(callback)
  }

  function off(type: string, callback: (data: any) => void) {
    listeners.get(type)?.delete(callback)
  }

  function disconnect() {
    ws?.close()
    ws = null
  }

  onMounted(connect)
  onUnmounted(disconnect)

  return { connected, lastMessage, on, off }
}
