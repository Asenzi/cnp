<template>
  <view class="chat-page">
    <scroll-view
      class="message-scroll"
      scroll-y
      :show-scrollbar="false"
      :upper-threshold="80"
      :scroll-into-view="scrollIntoViewId"
      scroll-with-animation
      @scrolltoupper="onScrollToUpper"
    >
      <view class="message-wrap">
        <view v-if="peerOnline !== null" class="presence-tip">
          <text class="presence-text">{{ peerOnline ? '\u5bf9\u65b9\u5728\u7ebf' : '\u5bf9\u65b9\u79bb\u7ebf' }}</text>
        </view>

        <view v-if="loading && !messages.length" class="status-wrap">
          <text class="status-text">\u52a0\u8f7d\u4e2d...</text>
        </view>

        <view v-else-if="loadError && !messages.length" class="status-wrap">
          <text class="status-text">{{ loadError }}</text>
          <button class="retry-btn" hover-class="retry-btn-active" @tap="reloadMessages">\u91cd\u65b0\u52a0\u8f7d</button>
        </view>

        <view v-else-if="!messages.length" class="status-wrap">
          <text class="status-text">\u6682\u65e0\u6d88\u606f\u8bb0\u5f55</text>
        </view>

        <view v-else>
          <view v-if="loadingMore && hasMore" class="top-load">
            <text class="top-load-text">\u52a0\u8f7d\u66f4\u65e9\u6d88\u606f...</text>
          </view>

          <template v-for="item in timelineItems" :key="item.id">
            <ChatTimeDivider v-if="item.type === 'time'" :text="item.text" />
            <view v-else :id="`msg-${item.message.id}`">
              <ChatMessageBubble
                :message="item.message"
                :peer-name="peerName"
                :peer-avatar="peerAvatar"
                :self-avatar="selfAvatar"
                @tap-card="onTapBusinessCard"
                @tap-file="onTapFileAttachment"
                @tap-location="onTapLocationAttachment"
                @tap-image="onPreviewImage"
                @retry="onRetryLocalMessage"
                @request-revoke="onRequestRevokeMessage"
              />
            </view>
          </template>
        </view>
      </view>
    </scroll-view>

    <ChatComposer
      v-model="inputText"
      :sending="sending"
      :show-quick-panel="showQuickPanel"
      :actions="quickActions"
      @send="onSend"
      @primary-action="onPrimaryAction"
      @tap-action="onTapQuickAction"
    />
  </view>
</template>

<script setup>
import { computed, onUnmounted, ref } from 'vue'
import { onHide, onLoad, onPullDownRefresh, onShow } from '@dcloudio/uni-app'
import {
  getConversationMessages,
  getImPresence,
  getImWebSocketUrl,
  markConversationRead,
  revokeConversationMessage,
  sendConversationMessage,
  uploadImAsset
} from '../../../api/im'
import { getApiBaseUrl } from '../../../utils/request'
import ChatComposer from './components/ChatComposer.vue'
import ChatMessageBubble from './components/ChatMessageBubble.vue'
import ChatTimeDivider from './components/ChatTimeDivider.vue'
import { CHAT_QUICK_ACTIONS } from './modules/chat-quick-actions'

const PAGE_SIZE = 20
const POLL_INTERVAL = 8000
const WS_HEARTBEAT_INTERVAL = 20000
const WS_RECONNECT_DELAY = 2000
const DELIVERY_PRIORITY = {
  sent: 1,
  delivered: 2,
  read: 3
}

const targetUserId = ref('')
const selfUserId = ref('')
const peerName = ref('\u804a\u5929')
const peerAvatar = ref('/static/logo.png')
const selfAvatar = ref('/static/logo.png')
const peerOnline = ref(null)

const messages = ref([])
const loading = ref(false)
const loadingMore = ref(false)
const loadError = ref('')
const hasMore = ref(true)
const nextCursor = ref('')
const sending = ref(false)
const inputText = ref('')
const scrollIntoViewId = ref('')
const hasPromptedLogin = ref(false)
const showQuickPanel = ref(true)
const quickActions = CHAT_QUICK_ACTIONS

const isPageActive = ref(false)
const socketReady = ref(false)
const socketTask = ref(null)

let pollTimer = null
let wsHeartbeatTimer = null
let wsReconnectTimer = null
const pendingDeliveryStateMap = new Map()

const canSend = computed(() => Boolean(String(inputText.value || '').trim()))

const timelineItems = computed(() => {
  const rows = []
  let prevTimestamp = 0
  messages.value.forEach((item, index) => {
    const currentTimestamp = getTimestamp(item.createdAt)
    if (index === 0 || shouldInsertTimeDivider(prevTimestamp, currentTimestamp)) {
      rows.push({
        id: `time-${item.id}`,
        type: 'time',
        text: item.timeText || formatTimestamp(currentTimestamp)
      })
    }
    rows.push({
      id: `message-${item.id}`,
      type: 'message',
      message: item
    })
    prevTimestamp = currentTimestamp || prevTimestamp
  })
  return rows
})

const showToast = (title) => {
  uni.showToast({
    title,
    icon: 'none'
  })
}

const isLoggedIn = () => Boolean(String(uni.getStorageSync('token') || '').trim())

const clearLoginState = () => {
  uni.removeStorageSync('token')
  uni.removeStorageSync('isLoggedIn')
  uni.removeStorageSync('userInfo')
}

const ensureLoggedIn = () => {
  if (isLoggedIn()) {
    return true
  }

  messages.value = []
  hasMore.value = false
  loadError.value = ''

  if (!hasPromptedLogin.value) {
    hasPromptedLogin.value = true
    showToast('\u8bf7\u5148\u767b\u5f55')
    setTimeout(() => {
      uni.navigateTo({
        url: '/pages/auth/login/index'
      })
    }, 220)
  }
  return false
}

const resolveAvatarUrl = (url) => {
  const normalized = String(url || '').trim()
  if (!normalized) {
    return '/static/logo.png'
  }
  if (/^https?:\/\//.test(normalized)) {
    return normalized
  }
  if (normalized.startsWith('/')) {
    if (normalized.startsWith('/static/')) {
      return normalized
    }
    const base = String(getApiBaseUrl() || 'http://172.20.10.3:8001').trim()
    return `${base}${normalized}`
  }
  return normalized
}

const refreshSelfProfile = () => {
  const userInfo = uni.getStorageSync('userInfo') || {}
  const avatar = userInfo.avatar_url || userInfo.avatarUrl || userInfo.avatar || '/static/logo.png'
  selfAvatar.value = resolveAvatarUrl(avatar)
  selfUserId.value = String(userInfo.user_id || userInfo.userId || '').trim()
}

const parseJsonSafe = (text) => {
  try {
    return JSON.parse(String(text || '').trim())
  } catch (err) {
    return null
  }
}

const parseBusinessCard = (rawContent, contentType) => {
  if (String(contentType || '').trim() === 'card') {
    const parsed = parseJsonSafe(rawContent)
    if (!parsed) return null
    const name = String(parsed?.name || '').trim()
    if (!name) return null
    return {
      userId: String(parsed?.user_id || parsed?.userId || '').trim(),
      name,
      subtitle: String(parsed?.subtitle || parsed?.company || '').trim() || '\u5708\u8109\u94fe\u7528\u6237',
      avatar: resolveAvatarUrl(parsed?.avatar_url || parsed?.avatar || '')
    }
  }

  const content = String(rawContent || '').trim()
  if (!content.startsWith('CARD:')) {
    return null
  }
  const parsed = parseJsonSafe(content.slice(5))
  if (!parsed) return null
  const name = String(parsed?.name || '').trim()
  if (!name) return null
  return {
    userId: String(parsed?.user_id || parsed?.userId || '').trim(),
    name,
    subtitle: String(parsed?.subtitle || parsed?.company || '').trim() || '\u5708\u8109\u94fe\u7528\u6237',
    avatar: resolveAvatarUrl(parsed?.avatar_url || parsed?.avatar || '')
  }
}

const parseFileAttachment = (rawContent, contentType) => {
  let parsed = null
  if (String(contentType || '').trim() === 'file') {
    parsed = parseJsonSafe(rawContent)
  } else {
    const text = String(rawContent || '').trim()
    if (text.startsWith('FILE:')) {
      parsed = parseJsonSafe(text.slice(5))
    }
  }
  if (!parsed) return null
  const name = String(parsed?.name || '').trim()
  const url = String(parsed?.url || '').trim()
  if (!name || !url) return null
  return {
    name,
    url,
    size: Number(parsed?.size || 0),
    mimeType: String(parsed?.mime_type || parsed?.mimeType || '').trim()
  }
}

const parseLocationAttachment = (rawContent, contentType) => {
  let parsed = null
  if (String(contentType || '').trim() === 'location') {
    parsed = parseJsonSafe(rawContent)
  } else {
    const text = String(rawContent || '').trim()
    if (text.startsWith('LOCATION:')) {
      parsed = parseJsonSafe(text.slice(9))
    }
  }
  if (!parsed) return null
  const latitude = Number(parsed?.latitude)
  const longitude = Number(parsed?.longitude)
  if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) {
    return null
  }
  return {
    name: String(parsed?.name || '').trim() || '\u5730\u7406\u4f4d\u7f6e',
    address: String(parsed?.address || '').trim(),
    latitude,
    longitude
  }
}

const mapMessage = (item = {}, options = {}) => {
  const content = String(item.content || '').trim()
  const contentType = String(item.content_type || item.contentType || 'text').trim() || 'text'
  const senderUserId = String(item.sender_user_id || item.senderUserId || '').trim()
  const isSelf = typeof item.is_self === 'boolean'
    ? Boolean(item.is_self)
    : Boolean(senderUserId && senderUserId === selfUserId.value)
  const localState = String(options.localState || item.localState || '').trim()
  const isRead = typeof item.is_read === 'boolean'
    ? Boolean(item.is_read)
    : Boolean(item.isRead)
  let deliveryState = String(options.deliveryState || item.deliveryState || '').trim()
  if (isRead) {
    deliveryState = 'read'
  } else if (!deliveryState && isSelf && !localState && contentType !== 'recalled') {
    deliveryState = 'sent'
  }

  const businessCard = parseBusinessCard(content, contentType)
  const fileAttachment = parseFileAttachment(content, contentType)
  const locationAttachment = parseLocationAttachment(content, contentType)

  return {
    id: String(item.id || ''),
    senderUserId,
    receiverUserId: String(item.receiver_user_id || item.receiverUserId || '').trim(),
    content,
    contentType,
    isSelf,
    isRead,
    deliveryState,
    timeText: String(item.time_text || item.timeText || '').trim(),
    createdAt: String(item.created_at || item.createdAt || '').trim() || new Date().toISOString(),
    businessCard,
    fileAttachment,
    locationAttachment,
    localState,
    localPayload: options.localPayload || item.localPayload || null
  }
}

const getTimestamp = (raw) => {
  const text = String(raw || '').trim()
  if (!text) {
    return 0
  }
  const normalized = text.includes('T') ? text : text.replace(' ', 'T')
  const ts = Date.parse(normalized)
  return Number.isFinite(ts) ? ts : 0
}

const formatTimestamp = (timestamp) => {
  if (!timestamp) {
    return ''
  }
  const date = new Date(timestamp)
  const hh = String(date.getHours()).padStart(2, '0')
  const mm = String(date.getMinutes()).padStart(2, '0')
  return `${hh}:${mm}`
}

const shouldInsertTimeDivider = (prevTimestamp, currentTimestamp) => {
  if (!prevTimestamp || !currentTimestamp) {
    return false
  }
  return Math.abs(currentTimestamp - prevTimestamp) >= 5 * 60 * 1000
}

const sortMessages = (items) => {
  return [...items].sort((a, b) => {
    const ta = getTimestamp(a.createdAt)
    const tb = getTimestamp(b.createdAt)
    if (ta !== tb) {
      return ta - tb
    }
    const ia = Number(String(a.id || '').replace(/[^\d]/g, '') || 0)
    const ib = Number(String(b.id || '').replace(/[^\d]/g, '') || 0)
    return ia - ib
  })
}

const mergeDeliveryState = (currentState = '', nextState = '') => {
  const current = String(currentState || '').trim()
  const next = String(nextState || '').trim()
  const currentPriority = Number(DELIVERY_PRIORITY[current] || 0)
  const nextPriority = Number(DELIVERY_PRIORITY[next] || 0)
  return currentPriority >= nextPriority ? current : next
}

const insertOrUpdateMessage = (message, replaceId = '') => {
  const nextMessage = { ...message }
  const pendingDeliveryState = pendingDeliveryStateMap.get(String(nextMessage.id || '').trim())
  if (pendingDeliveryState) {
    nextMessage.deliveryState = mergeDeliveryState(nextMessage.deliveryState, pendingDeliveryState)
    pendingDeliveryStateMap.delete(String(nextMessage.id || '').trim())
  }

  const list = [...messages.value]
  if (replaceId) {
    const replaceIndex = list.findIndex((item) => item.id === replaceId)
    if (replaceIndex >= 0) {
      list.splice(replaceIndex, 1)
    }
  }

  const index = list.findIndex((item) => item.id === nextMessage.id)
  if (index >= 0) {
    const prev = list[index]
    const merged = { ...prev, ...nextMessage }
    merged.deliveryState = mergeDeliveryState(prev.deliveryState, nextMessage.deliveryState)
    if (merged.isRead) {
      merged.deliveryState = 'read'
    }
    list[index] = merged
  } else {
    list.push(nextMessage)
  }
  messages.value = sortMessages(list)
}

const markLocalMessageFailed = (tempId) => {
  const list = [...messages.value]
  const index = list.findIndex((item) => item.id === tempId)
  if (index < 0) {
    return
  }
  list[index] = {
    ...list[index],
    localState: 'failed'
  }
  messages.value = list
}

const updateMessageById = (messageId, updater) => {
  const safeId = String(messageId || '').trim()
  if (!safeId || typeof updater !== 'function') {
    return false
  }
  const list = [...messages.value]
  const index = list.findIndex((item) => String(item.id || '').trim() === safeId)
  if (index < 0) {
    return false
  }
  const updated = updater(list[index])
  if (!updated) {
    return false
  }
  list[index] = updated
  messages.value = sortMessages(list)
  return true
}

const markMessagesRead = (messageIds = []) => {
  const idSet = new Set((Array.isArray(messageIds) ? messageIds : []).map((item) => String(item || '').trim()).filter(Boolean))
  if (!idSet.size) {
    return
  }
  messages.value = sortMessages(messages.value.map((item) => {
    if (!idSet.has(String(item.id || '').trim())) {
      return item
    }
    return {
      ...item,
      isRead: true,
      deliveryState: 'read'
    }
  }))
}

const updateScrollToBottom = () => {
  const last = messages.value[messages.value.length - 1]
  scrollIntoViewId.value = last?.id ? `msg-${last.id}` : ''
  if (scrollIntoViewId.value) {
    setTimeout(() => {
      scrollIntoViewId.value = ''
    }, 180)
  }
}

const isCurrentConversationMessage = (item = {}) => {
  const target = String(targetUserId.value || '').trim()
  if (!target) return false
  const sender = String(item.sender_user_id || item.senderUserId || item.senderUserId || '').trim()
  const receiver = String(item.receiver_user_id || item.receiverUserId || '').trim()
  return sender === target || receiver === target
}

const fetchMessages = async (reset = false, options = {}) => {
  const shouldAutoScroll = options.autoScroll !== false
  if (!targetUserId.value || !ensureLoggedIn()) {
    return
  }
  if (loading.value || loadingMore.value) {
    return
  }
  if (!reset && (!hasMore.value || !nextCursor.value)) {
    return
  }

  if (reset) {
    loading.value = true
    loadError.value = ''
  } else {
    loadingMore.value = true
  }

  try {
    const data = await getConversationMessages(targetUserId.value, {
      cursor: reset ? '' : nextCursor.value,
      limit: PAGE_SIZE
    })

    const incoming = Array.isArray(data?.items) ? data.items.map((item) => mapMessage(item)) : []
    if (reset) {
      messages.value = sortMessages(incoming)
      const peer = data?.peer || {}
      const peerNameValue = String(peer.name || '').trim()
      const peerAvatarValue = resolveAvatarUrl(peer.avatar_url)
      if (peerNameValue) {
        peerName.value = peerNameValue
        uni.setNavigationBarTitle({
          title: peerNameValue
        })
      }
      peerAvatar.value = peerAvatarValue
    } else {
      messages.value = sortMessages([...incoming, ...messages.value])
    }

    hasMore.value = Boolean(data?.has_more)
    nextCursor.value = String(data?.next_cursor || '').trim()
    loadError.value = ''

    if (reset && shouldAutoScroll) {
      updateScrollToBottom()
    }

    await markConversationRead(targetUserId.value)
  } catch (err) {
    const statusCode = Number(err?.statusCode || 0)
    if (statusCode === 401) {
      clearLoginState()
      hasPromptedLogin.value = false
      ensureLoggedIn()
      return
    }
    const message = err?.message || '\u6d88\u606f\u52a0\u8f7d\u5931\u8d25'
    if (reset && !messages.value.length) {
      loadError.value = message
    }
    showToast(message)
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

const reloadMessages = async (options = {}) => {
  await fetchMessages(true, options)
}

const stopPolling = () => {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

const refreshPresence = async () => {
  if (!targetUserId.value || !ensureLoggedIn()) return
  try {
    const data = await getImPresence(targetUserId.value)
    peerOnline.value = Boolean(data?.online)
  } catch (err) {
    peerOnline.value = null
  }
}

const startPolling = () => {
  stopPolling()
  pollTimer = setInterval(() => {
    if (!isPageActive.value) return
    if (!socketReady.value && !sending.value && !loading.value && !loadingMore.value) {
      fetchMessages(true, { autoScroll: false })
      refreshPresence()
    }
  }, POLL_INTERVAL)
}

const stopSocketHeartbeat = () => {
  if (wsHeartbeatTimer) {
    clearInterval(wsHeartbeatTimer)
    wsHeartbeatTimer = null
  }
}

const stopSocketReconnect = () => {
  if (wsReconnectTimer) {
    clearTimeout(wsReconnectTimer)
    wsReconnectTimer = null
  }
}

const sendSocketPayload = (payload) => {
  if (!socketReady.value || !socketTask.value) {
    return
  }
  socketTask.value.send({
    data: JSON.stringify(payload)
  })
}

const onSocketMessage = (event) => {
  const data = parseJsonSafe(event?.data)
  if (!data) return
  const type = String(data?.event || '').trim()
  const payload = data?.data || {}

  if (type === 'ws.ready') {
    sendSocketPayload({
      action: 'presence.check',
      target_user_id: targetUserId.value
    })
    return
  }

  if (type === 'ws.pong') {
    return
  }

  if (type === 'presence.state' || type === 'presence.changed') {
    const changedUserId = String(payload?.user_id || '').trim()
    if (changedUserId && changedUserId === targetUserId.value) {
      peerOnline.value = Boolean(payload?.online)
    }
    return
  }

  if (type === 'message.new') {
    const incoming = payload?.message || {}
    if (!isCurrentConversationMessage(incoming)) {
      return
    }
    const mapped = mapMessage(incoming)
    insertOrUpdateMessage(mapped)
    if (!mapped.isSelf) {
      markConversationRead(targetUserId.value).catch(() => {})
    }
    updateScrollToBottom()
    return
  }

  if (type === 'message.revoked') {
    const incoming = payload?.message || {}
    if (!isCurrentConversationMessage(incoming)) {
      return
    }
    const mapped = mapMessage(incoming)
    insertOrUpdateMessage(mapped)
    return
  }

  if (type === 'message.delivery') {
    const messageId = String(payload?.message_id || '').trim()
    const eventTargetUserId = String(payload?.target_user_id || '').trim()
    if (eventTargetUserId && eventTargetUserId !== targetUserId.value) {
      return
    }
    if (!messageId) {
      return
    }
    const delivered = Boolean(payload?.delivered)
    const matched = updateMessageById(messageId, (item) => {
      if (!item?.isSelf) {
        return item
      }
      if (item.isRead) {
        return {
          ...item,
          deliveryState: 'read'
        }
      }
      return {
        ...item,
        localState: '',
        deliveryState: mergeDeliveryState(item.deliveryState, delivered ? 'delivered' : 'sent')
      }
    })
    if (!matched) {
      pendingDeliveryStateMap.set(messageId, delivered ? 'delivered' : 'sent')
    }
    return
  }

  if (type === 'conversation.read') {
    const readerUserId = String(payload?.viewer_user_id || '').trim()
    if (readerUserId && readerUserId !== targetUserId.value) {
      return
    }
    markMessagesRead(payload?.read_message_ids)
  }
}

const scheduleSocketReconnect = () => {
  if (!isPageActive.value || wsReconnectTimer) {
    return
  }
  wsReconnectTimer = setTimeout(() => {
    wsReconnectTimer = null
    startSocket()
  }, WS_RECONNECT_DELAY)
}

const closeSocket = () => {
  stopSocketHeartbeat()
  stopSocketReconnect()
  socketReady.value = false
  if (socketTask.value) {
    try {
      socketTask.value.close({})
    } catch (err) {
      // ignore
    }
    socketTask.value = null
  }
}

const startSocket = () => {
  if (!isPageActive.value || !targetUserId.value || !ensureLoggedIn()) {
    return
  }

  const token = String(uni.getStorageSync('token') || '').trim()
  if (!token) {
    return
  }

  closeSocket()
  const wsUrl = `${getImWebSocketUrl()}?token=${encodeURIComponent(token)}`
  const task = uni.connectSocket({
    url: wsUrl
  })
  socketTask.value = task

  task.onOpen(() => {
    socketReady.value = true
    stopSocketReconnect()
    stopSocketHeartbeat()
    wsHeartbeatTimer = setInterval(() => {
      sendSocketPayload({ action: 'ping' })
    }, WS_HEARTBEAT_INTERVAL)
    sendSocketPayload({
      action: 'presence.check',
      target_user_id: targetUserId.value
    })
  })

  task.onMessage(onSocketMessage)

  task.onClose(() => {
    socketReady.value = false
    stopSocketHeartbeat()
    scheduleSocketReconnect()
  })

  task.onError(() => {
    socketReady.value = false
    stopSocketHeartbeat()
    scheduleSocketReconnect()
  })
}

const createLocalMessage = (payload) => {
  const nowIso = new Date().toISOString()
  return mapMessage(
    {
      id: `local-${Date.now()}-${Math.floor(Math.random() * 10000)}`,
      sender_user_id: selfUserId.value,
      receiver_user_id: targetUserId.value,
      content: String(payload.content || '').trim(),
      content_type: String(payload.content_type || 'text').trim() || 'text',
      created_at: nowIso,
      time_text: formatTimestamp(getTimestamp(nowIso)),
      is_self: true
    },
    {
      localState: 'sending',
      localPayload: payload
    }
  )
}

const sendMessageWithLocalState = async (payload) => {
  const localMessage = createLocalMessage(payload)
  insertOrUpdateMessage(localMessage)
  updateScrollToBottom()

  try {
    const serverMessage = await sendConversationMessage(targetUserId.value, payload)
    const mapped = mapMessage(serverMessage)
    insertOrUpdateMessage(mapped, localMessage.id)
    updateScrollToBottom()
    return mapped
  } catch (err) {
    markLocalMessageFailed(localMessage.id)
    throw err
  }
}

const onSend = async () => {
  const content = String(inputText.value || '').trim()
  if (!content || !targetUserId.value) {
    return
  }
  if (!ensureLoggedIn()) {
    return
  }
  if (sending.value) {
    return
  }

  sending.value = true
  try {
    await sendMessageWithLocalState({
      content,
      content_type: 'text'
    })
    inputText.value = ''
  } catch (err) {
    showToast(err?.message || '\u53d1\u9001\u5931\u8d25')
  } finally {
    sending.value = false
  }
}

const sendCardMessage = async () => {
  const userInfo = uni.getStorageSync('userInfo') || {}
  const payload = {
    user_id: String(userInfo.userId || userInfo.user_id || '').trim(),
    name: String(userInfo.nickname || '').trim() || '\u5708\u8109\u94fe\u7528\u6237',
    subtitle: [userInfo.industry_label, userInfo.city_name].filter(Boolean).join(' | ') || '\u5708\u8109\u94fe\u7528\u6237',
    avatar_url: resolveAvatarUrl(userInfo.avatar_url || userInfo.avatarUrl || userInfo.avatar || '/static/logo.png')
  }
  await sendMessageWithLocalState({
    content: JSON.stringify(payload),
    content_type: 'card'
  })
}

const sendLocationMessage = async () => {
  const location = await new Promise((resolve, reject) => {
    uni.chooseLocation({
      success: (res) => resolve(res),
      fail: (err) => reject(err)
    })
  })
  const payload = {
    name: String(location?.name || '').trim() || '\u5730\u7406\u4f4d\u7f6e',
    address: String(location?.address || '').trim(),
    latitude: Number(location?.latitude || 0),
    longitude: Number(location?.longitude || 0)
  }
  await sendMessageWithLocalState({
    content: JSON.stringify(payload),
    content_type: 'location'
  })
}

const sendImageMessage = async () => {
  const selected = await new Promise((resolve, reject) => {
    uni.chooseImage({
      count: 1,
      sizeType: ['compressed'],
      sourceType: ['album', 'camera'],
      success: (res) => resolve(res),
      fail: (err) => reject(err)
    })
  })

  const filePath = String(selected?.tempFilePaths?.[0] || '').trim()
  if (!filePath) {
    throw new Error('\u672a\u9009\u62e9\u56fe\u7247')
  }

  const uploadData = await uploadImAsset(filePath, {
    kind: 'image',
    name: 'chat-image.jpg'
  })
  const imageUrl = String(uploadData?.url || '').trim()
  if (!imageUrl) {
    throw new Error('\u56fe\u7247\u4e0a\u4f20\u5931\u8d25')
  }
  await sendMessageWithLocalState({
    content: imageUrl,
    content_type: 'image'
  })
}

const sendFileMessage = async () => {
  const selected = await new Promise((resolve, reject) => {
    uni.chooseMessageFile({
      count: 1,
      type: 'file',
      success: (res) => resolve(res),
      fail: (err) => reject(err)
    })
  })

  const file = selected?.tempFiles?.[0] || {}
  const filePath = String(file?.path || '').trim()
  if (!filePath) {
    throw new Error('\u672a\u9009\u62e9\u6587\u4ef6')
  }

  const uploadData = await uploadImAsset(filePath, {
    kind: 'file',
    name: String(file?.name || 'file').trim() || 'file'
  })

  const payload = {
    name: String(uploadData?.name || file?.name || '\u9644\u4ef6').trim() || '\u9644\u4ef6',
    url: String(uploadData?.url || '').trim(),
    size: Number(uploadData?.size || file?.size || 0),
    mime_type: String(uploadData?.mime_type || '').trim()
  }
  if (!payload.url) {
    throw new Error('\u6587\u4ef6\u4e0a\u4f20\u5931\u8d25')
  }
  await sendMessageWithLocalState({
    content: JSON.stringify(payload),
    content_type: 'file'
  })
}

const onPrimaryAction = () => {
  if (canSend.value) {
    onSend()
    return
  }
  showQuickPanel.value = !showQuickPanel.value
}

const onTapQuickAction = (action) => {
  const key = String(action?.key || '')
  if (!key) {
    return
  }
  if (!ensureLoggedIn()) {
    return
  }
  if (!targetUserId.value) {
    showToast('\u4f1a\u8bdd\u53c2\u6570\u7f3a\u5931')
    return
  }
  if (sending.value) {
    return
  }

  const taskMap = {
    'send-card': sendCardMessage,
    'choose-image': sendImageMessage,
    'choose-file': sendFileMessage,
    'share-location': sendLocationMessage
  }
  const task = taskMap[key]
  if (!task) {
    showToast('\u8be5\u529f\u80fd\u5f00\u53d1\u4e2d')
    return
  }

  sending.value = true
  Promise.resolve()
    .then(() => task())
    .catch((err) => {
      const msg = String(err?.message || err?.errMsg || '').trim()
      if (!msg || msg.includes('cancel') || msg.includes('chooseLocation:fail')) {
        return
      }
      showToast(msg)
    })
    .finally(() => {
      sending.value = false
    })
}

const onTapBusinessCard = (card) => {
  const target = String(card?.userId || card?.user_id || '').trim()
  if (!target) {
    showToast('\u540d\u7247\u7528\u6237\u4fe1\u606f\u7f3a\u5931')
    return
  }
  uni.navigateTo({
    url: `/pages/me/card/index?userId=${encodeURIComponent(target)}`
  })
}

const onTapFileAttachment = (file) => {
  const url = String(file?.url || '').trim()
  if (!url) {
    showToast('\u6587\u4ef6\u5730\u5740\u65e0\u6548')
    return
  }
  uni.showLoading({
    title: '\u6253\u5f00\u4e2d...',
    mask: true
  })
  uni.downloadFile({
    url,
    success: (res) => {
      const filePath = String(res?.tempFilePath || '').trim()
      if (!filePath) {
        showToast('\u6587\u4ef6\u4e0b\u8f7d\u5931\u8d25')
        return
      }
      uni.openDocument({
        filePath,
        showMenu: true,
        fail: () => {
          showToast('\u5f53\u524d\u6587\u4ef6\u4e0d\u652f\u6301\u9884\u89c8')
        }
      })
    },
    fail: () => {
      showToast('\u6587\u4ef6\u4e0b\u8f7d\u5931\u8d25')
    },
    complete: () => {
      uni.hideLoading()
    }
  })
}

const onTapLocationAttachment = (location) => {
  const latitude = Number(location?.latitude || 0)
  const longitude = Number(location?.longitude || 0)
  if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) {
    showToast('\u4f4d\u7f6e\u4fe1\u606f\u65e0\u6548')
    return
  }
  uni.openLocation({
    latitude,
    longitude,
    name: String(location?.name || '').trim() || '\u5730\u7406\u4f4d\u7f6e',
    address: String(location?.address || '').trim() || ''
  })
}

const onPreviewImage = (url) => {
  const imageUrl = String(url || '').trim()
  if (!imageUrl) {
    return
  }
  uni.previewImage({
    urls: [imageUrl],
    current: imageUrl
  })
}

const onRetryLocalMessage = async (message) => {
  if (!message?.localPayload || sending.value) {
    return
  }
  const tempId = String(message.id || '').trim()
  if (!tempId) return

  const list = [...messages.value]
  const index = list.findIndex((item) => item.id === tempId)
  if (index >= 0) {
    list[index] = {
      ...list[index],
      localState: 'sending'
    }
    messages.value = list
  }

  sending.value = true
  try {
    const serverMessage = await sendConversationMessage(targetUserId.value, message.localPayload)
    insertOrUpdateMessage(mapMessage(serverMessage), tempId)
  } catch (err) {
    markLocalMessageFailed(tempId)
    showToast(err?.message || '\u91cd\u8bd5\u53d1\u9001\u5931\u8d25')
  } finally {
    sending.value = false
  }
}

const onRequestRevokeMessage = (message) => {
  const messageId = String(message?.id || '').trim()
  if (!messageId || messageId.startsWith('local-')) {
    return
  }
  if (!message?.isSelf || String(message?.contentType || '') === 'recalled') {
    return
  }

  uni.showActionSheet({
    itemList: ['\u64a4\u56de\u6d88\u606f'],
    success: async () => {
      try {
        const result = await revokeConversationMessage(targetUserId.value, messageId)
        insertOrUpdateMessage(mapMessage(result))
      } catch (err) {
        showToast(err?.message || '\u64a4\u56de\u5931\u8d25')
      }
    }
  })
}

const onScrollToUpper = () => {
  fetchMessages(false)
}

onLoad((query = {}) => {
  targetUserId.value = String(query?.targetUserId || '').trim()
  if (!targetUserId.value) {
    showToast('\u4f1a\u8bdd\u53c2\u6570\u7f3a\u5931')
    setTimeout(() => {
      uni.navigateBack()
    }, 260)
    return
  }
  peerName.value = decodeURIComponent(String(query?.name || '\u804a\u5929').trim())
  peerAvatar.value = resolveAvatarUrl(decodeURIComponent(String(query?.avatar || '/static/logo.png').trim()))
  if (peerName.value) {
    uni.setNavigationBarTitle({
      title: peerName.value
    })
  }
})

onShow(() => {
  isPageActive.value = true
  hasPromptedLogin.value = false
  refreshSelfProfile()
  reloadMessages({ autoScroll: true })
  refreshPresence()
  startSocket()
  startPolling()
})

onHide(() => {
  isPageActive.value = false
  stopPolling()
  closeSocket()
})

onPullDownRefresh(async () => {
  await reloadMessages({ autoScroll: true })
  await refreshPresence()
  uni.stopPullDownRefresh()
})

onUnmounted(() => {
  stopPolling()
  closeSocket()
})
</script>

<style scoped>
.chat-page {
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: #f6f6f8;
}

.message-scroll {
  flex: 1;
}

.message-wrap {
  padding: 24rpx 24rpx 16rpx;
}

.presence-tip {
  display: flex;
  justify-content: center;
  margin-bottom: 12rpx;
}

.presence-text {
  color: #94a3b8;
  font-size: 20rpx;
  line-height: 28rpx;
  background: #e9eef5;
  padding: 6rpx 16rpx;
  border-radius: 999rpx;
}

.status-wrap,
.top-load {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  padding: 36rpx 24rpx;
}

.status-text,
.top-load-text {
  color: #64748b;
  font-size: 22rpx;
  line-height: 32rpx;
}

.retry-btn {
  margin-top: 16rpx;
  min-width: 180rpx;
  height: 64rpx;
  border: 0;
  border-radius: 999rpx;
  background: #1a57db;
  color: #ffffff;
  font-size: 24rpx;
  line-height: 64rpx;
  font-weight: 600;
}

.retry-btn::after {
  border: 0;
}

.retry-btn-active {
  opacity: 0.84;
}

@media (prefers-color-scheme: dark) {
  .chat-page {
    background: #111621;
  }

  .presence-text {
    background: rgba(30, 41, 59, 0.7);
    color: #94a3b8;
  }

  .status-text,
  .top-load-text {
    color: #94a3b8;
  }
}
</style>
