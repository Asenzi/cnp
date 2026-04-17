<template>
  <view class="message-page">
    <scroll-view
      class="message-scroll"
      scroll-y
      :show-scrollbar="false"
      :lower-threshold="100"
      @scrolltolower="onScrollToLower"
    >
      <view class="content-wrap">
        <view class="section action-section">
          <view
            v-for="(item, index) in topActionItems"
            :key="item.id"
            class="row-wrap"
            :class="index < topActionItems.length - 1 ? 'row-wrap-border' : ''"
          >
            <MessageActionItem :item="item" @tap="onTapAction" />
          </view>
        </view>

        <view v-if="loading && !hasAny" class="status-wrap">
          <text class="status-text">加载中...</text>
        </view>

        <view v-else-if="loadError && !hasAny" class="status-wrap">
          <text class="status-text">{{ loadError }}</text>
          <button class="retry-btn" hover-class="retry-btn-active" @tap="onRetry">重新加载</button>
        </view>

        <view v-else-if="!hasAny" class="status-wrap">
          <text class="status-text">暂无会话消息</text>
        </view>

        <view v-else class="section chat-section">
          <view
            v-for="(item, index) in chatItems"
            :key="item.id"
            class="row-wrap"
            :class="index < chatItems.length - 1 ? 'row-wrap-border' : ''"
          >
            <MessageChatItem :item="item" @tap="onTapChat" />
          </view>
        </view>

        <view v-if="hasAny && loadingMore" class="load-more-wrap">
          <text class="load-more-text">加载中...</text>
        </view>
        <view v-else-if="hasAny && hasMore" class="load-more-wrap">
          <text class="load-more-text">上拉加载更多</text>
        </view>
      </view>
    </scroll-view>
  </view>
</template>

<script setup>
import { computed, onUnmounted, ref } from 'vue'
import { onHide, onPullDownRefresh, onShow } from '@dcloudio/uni-app'
import { getImConversations, getImOverview, getImWebSocketUrl } from '../../../api/im'
import { getApiBaseUrl } from '../../../utils/request'
import MessageActionItem from './components/MessageActionItem.vue'
import MessageChatItem from './components/MessageChatItem.vue'

const PAGE_SIZE = 20
const WS_HEARTBEAT_INTERVAL = 20000
const WS_RECONNECT_DELAY = 2500
const SOCKET_RELOAD_THROTTLE = 900

const topActionItems = ref([
  {
    id: 'friend-apply',
    icon: 'person_add',
    iconTone: 'orange',
    title: '好友申请',
    preview: '暂无新的好友申请',
    badge: 0
  },
  {
    id: 'system-notice',
    icon: 'notifications',
    iconTone: 'primary',
    title: '系统通知',
    preview: '暂无系统通知',
    badge: 0
  }
])

const chatItems = ref([])
const loading = ref(false)
const loadingMore = ref(false)
const loadError = ref('')
const hasMore = ref(true)
const nextCursor = ref('')
const hasPromptedLogin = ref(false)
const socketReady = ref(false)
const isPageActive = ref(false)
const socketTask = ref(null)
let wsHeartbeatTimer = null
let wsReconnectTimer = null
let socketReloadTimer = null

const hasAny = computed(() => chatItems.value.length > 0)

const showToast = (title) => {
  uni.showToast({
    title,
    icon: 'none'
  })
}

const parseJsonSafe = (text) => {
  try {
    return JSON.parse(String(text || '').trim())
  } catch (err) {
    return null
  }
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

  chatItems.value = []
  hasMore.value = false
  loadError.value = ''

  if (!hasPromptedLogin.value) {
    hasPromptedLogin.value = true
    showToast('请先登录')
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

const mapConversation = (item = {}) => {
  const targetUserId = String(item.target_user_id || item.id || '').trim()
  return {
    id: String(item.id || ''),
    targetUserId,
    name: String(item.name || '').trim() || '未命名联系人',
    company: String(item.company || '').trim() || '好友',
    timeText: String(item.time_text || '').trim(),
    preview: String(item.last_message || '').trim() || '暂无消息',
    unread: Number(item.unread_count || 0),
    avatar: resolveAvatarUrl(item.avatar_url)
  }
}

const fetchOverview = async () => {
  if (!ensureLoggedIn()) {
    return
  }
  try {
    const data = await getImOverview()
    const friendApply = data?.friend_apply || {}
    const systemNotice = data?.system_notice || {}
    topActionItems.value = [
      {
        id: 'friend-apply',
        icon: 'person_add',
        iconTone: 'orange',
        title: '好友申请',
        preview: String(friendApply.latest_text || '暂无新的好友申请'),
        badge: Number(friendApply.unread_count || 0)
      },
      {
        id: 'system-notice',
        icon: 'notifications',
        iconTone: 'primary',
        title: '系统通知',
        preview: String(systemNotice.latest_text || '暂无系统通知'),
        badge: Number(systemNotice.unread_count || 0)
      }
    ]
  } catch (err) {
    const statusCode = Number(err?.statusCode || 0)
    if (statusCode === 401) {
      clearLoginState()
      hasPromptedLogin.value = false
      ensureLoggedIn()
      return
    }
    showToast(err?.message || '消息概览加载失败')
  }
}

const fetchConversations = async (reset = false) => {
  if (!ensureLoggedIn()) {
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
    const data = await getImConversations({
      cursor: reset ? '' : nextCursor.value,
      limit: PAGE_SIZE
    })
    const incoming = Array.isArray(data?.items) ? data.items.map((item) => mapConversation(item)) : []
    if (reset) {
      chatItems.value = incoming
    } else {
      chatItems.value = [...chatItems.value, ...incoming]
    }
    hasMore.value = Boolean(data?.has_more)
    nextCursor.value = String(data?.next_cursor || '').trim()
    loadError.value = ''
  } catch (err) {
    const statusCode = Number(err?.statusCode || 0)
    if (statusCode === 401) {
      clearLoginState()
      hasPromptedLogin.value = false
      ensureLoggedIn()
      return
    }
    const message = err?.message || '会话加载失败，请稍后重试'
    if (reset && !hasAny.value) {
      loadError.value = message
    }
    showToast(message)
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

const reloadAll = async () => {
  await fetchOverview()
  await fetchConversations(true)
}

const scheduleSocketReload = () => {
  if (socketReloadTimer || !isPageActive.value) {
    return
  }
  socketReloadTimer = setTimeout(() => {
    socketReloadTimer = null
    reloadAll()
  }, SOCKET_RELOAD_THROTTLE)
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

const stopSocketReloadTimer = () => {
  if (socketReloadTimer) {
    clearTimeout(socketReloadTimer)
    socketReloadTimer = null
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

  if (type === 'ws.ready' || type === 'ws.pong') {
    return
  }

  if (type === 'message.new' || type === 'message.revoked' || type === 'conversation.read') {
    scheduleSocketReload()
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
  if (!isPageActive.value || !ensureLoggedIn()) {
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

const onRetry = () => {
  reloadAll()
}

const onTapAction = (item) => {
  if (item?.id === 'friend-apply') {
    uni.navigateTo({
      url: '/pages/messages/friend-apply/index'
    })
    return
  }
  if (item?.id === 'system-notice') {
    uni.navigateTo({
      url: '/pages/messages/system-notice/index'
    })
    return
  }
  showToast('功能开发中')
}

const onTapChat = (item) => {
  const targetUserId = String(item?.targetUserId || '').trim()
  if (!targetUserId) {
    showToast('会话目标缺失')
    return
  }
  const name = encodeURIComponent(String(item?.name || '').trim())
  const avatar = encodeURIComponent(String(item?.avatar || '').trim())
  uni.navigateTo({
    url: `/pages/messages/chat/index?targetUserId=${encodeURIComponent(targetUserId)}&name=${name}&avatar=${avatar}`
  })
}

const onScrollToLower = () => {
  fetchConversations(false)
}

onShow(() => {
  isPageActive.value = true
  hasPromptedLogin.value = false
  reloadAll()
  startSocket()
})

onHide(() => {
  isPageActive.value = false
  stopSocketReloadTimer()
  closeSocket()
})

onPullDownRefresh(async () => {
  await reloadAll()
  uni.stopPullDownRefresh()
})

onUnmounted(() => {
  isPageActive.value = false
  stopSocketReloadTimer()
  closeSocket()
})
</script>

<style scoped>
.message-page {
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: #f6f6f8;
  font-family: 'Manrope', 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

.message-scroll {
  flex: 1;
  background: #f6f6f8;
}

.content-wrap {
  padding: 0 0 calc(24rpx + env(safe-area-inset-bottom));
}

.section {
  background: #ffffff;
}

.action-section {
  margin-bottom: 14rpx;
}

.chat-section {
  margin-bottom: 20rpx;
}

.row-wrap-border {
  border-bottom: 1rpx solid #f8fafc;
}

.status-wrap,
.load-more-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  padding: 36rpx 24rpx;
}

.status-text,
.load-more-text {
  color: #64748b;
  font-size: 24rpx;
  line-height: 34rpx;
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
  .message-page,
  .message-scroll {
    background: #111621;
  }

  .section {
    background: #0f172a;
  }

  .row-wrap-border {
    border-bottom-color: #1f2937;
  }

  .status-text,
  .load-more-text {
    color: #94a3b8;
  }
}
</style>
