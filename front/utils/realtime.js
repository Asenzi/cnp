import { getImWebSocketUrl } from '../api/im'

const HEARTBEAT_INTERVAL = 20000
const MAX_RECONNECT_DELAY = 30000
const listeners = new Set()

let socketTask = null
let socketToken = ''
let socketState = 'closed'
let heartbeatTimer = null
let reconnectTimer = null
let reconnectAttempt = 0
let shouldReconnect = true
let latestNotificationEvent = null

const getToken = () => String(uni.getStorageSync('token') || '').trim()

const parseJsonSafe = (value) => {
  try {
    return JSON.parse(String(value || '').trim())
  } catch (error) {
    return null
  }
}

const clearHeartbeat = () => {
  if (heartbeatTimer) {
    clearInterval(heartbeatTimer)
    heartbeatTimer = null
  }
}

const clearReconnect = () => {
  if (reconnectTimer) {
    clearTimeout(reconnectTimer)
    reconnectTimer = null
  }
}

const emitRealtimeEvent = (payload) => {
  if (payload?.event === 'notification.changed') {
    latestNotificationEvent = payload
  }
  listeners.forEach((listener) => {
    try {
      listener(payload)
    } catch (error) {
      // A page listener must not interrupt the shared socket.
    }
  })
}

const sendPayload = (payload) => {
  if (socketState !== 'open' || !socketTask) return
  socketTask.send({ data: JSON.stringify(payload) })
}

const scheduleReconnect = () => {
  clearReconnect()
  if (!shouldReconnect || !getToken()) return

  const delay = Math.min(1000 * (2 ** reconnectAttempt), MAX_RECONNECT_DELAY)
  reconnectAttempt += 1
  reconnectTimer = setTimeout(() => {
    reconnectTimer = null
    connectRealtimeSocket()
  }, delay)
}

const disposeSocket = ({ reconnect = false } = {}) => {
  clearHeartbeat()
  clearReconnect()
  const task = socketTask
  socketTask = null
  socketState = 'closed'
  socketToken = ''

  if (task) {
    try {
      task.close({ code: 1000, reason: 'client close' })
    } catch (error) {
      // The runtime may have already closed the task.
    }
  }

  if (reconnect) scheduleReconnect()
}

export function connectRealtimeSocket() {
  const token = getToken()
  shouldReconnect = true

  if (!token) {
    disposeSocket()
    return
  }

  if (socketTask && socketToken === token && ['connecting', 'open'].includes(socketState)) {
    return
  }

  disposeSocket()
  socketToken = token
  socketState = 'connecting'

  const task = uni.connectSocket({
    url: `${getImWebSocketUrl()}?token=${encodeURIComponent(token)}`,
    // Providing callbacks prevents uni-app from promisifying connectSocket.
    success: () => {},
    fail: () => {}
  })

  if (
    !task
    || typeof task.onOpen !== 'function'
    || typeof task.onMessage !== 'function'
    || typeof task.onClose !== 'function'
    || typeof task.onError !== 'function'
  ) {
    socketTask = null
    socketState = 'closed'
    socketToken = ''
    scheduleReconnect()
    return
  }
  socketTask = task

  task.onOpen(() => {
    if (socketTask !== task) return
    socketState = 'open'
    reconnectAttempt = 0
    clearReconnect()
    clearHeartbeat()
    heartbeatTimer = setInterval(() => {
      sendPayload({ action: 'ping' })
    }, HEARTBEAT_INTERVAL)
  })

  task.onMessage((event) => {
    const payload = parseJsonSafe(event?.data)
    if (payload) emitRealtimeEvent(payload)
  })

  task.onClose(() => {
    if (socketTask !== task) return
    socketTask = null
    socketState = 'closed'
    socketToken = ''
    clearHeartbeat()
    scheduleReconnect()
  })

  task.onError(() => {
    if (socketTask !== task) return
    socketState = 'closed'
    clearHeartbeat()
    scheduleReconnect()
  })
}

export function disconnectRealtimeSocket() {
  shouldReconnect = false
  reconnectAttempt = 0
  latestNotificationEvent = null
  disposeSocket()
}

export function subscribeRealtime(listener, options = {}) {
  if (typeof listener !== 'function') return () => {}

  listeners.add(listener)
  if (options.replayLatest !== false && latestNotificationEvent) {
    listener(latestNotificationEvent)
  }

  return () => {
    listeners.delete(listener)
  }
}
