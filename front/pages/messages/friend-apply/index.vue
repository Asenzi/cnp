<template>
  <view class="friend-apply-page">
    <FriendApplyTabs
      :tabs="friendApplyTabs"
      :active-key="activeTab"
      @change="onChangeTab"
    />

    <scroll-view
      class="content-scroll"
      scroll-y
      :show-scrollbar="false"
      :lower-threshold="120"
      @scrolltolower="onScrollToLower"
    >
      <view class="content-wrap">
        <view class="list-header">
          <text class="list-header-text">{{ listHeaderText }}</text>
        </view>

        <view v-if="currentState.loading && !currentRequests.length" class="status-wrap">
          <text class="status-text">加载中...</text>
        </view>

        <view v-else-if="currentState.error && !currentRequests.length" class="status-wrap">
          <text class="status-text">{{ currentState.error }}</text>
          <button class="retry-btn" hover-class="retry-btn-active" @tap="onRetry">重新加载</button>
        </view>

        <view v-else-if="currentRequests.length" class="request-list">
          <FriendApplyRequestCard
            v-for="request in currentRequests"
            :key="request.id"
            :request="request"
            @accept="onAccept"
            @ignore="onIgnore"
          />
        </view>

        <FriendApplyEmpty v-else @discover="onDiscover" />

        <view v-if="currentRequests.length && currentState.loadingMore" class="load-more-wrap">
          <text class="load-more-text">加载中...</text>
        </view>
        <view v-else-if="currentRequests.length && currentState.hasMore" class="load-more-wrap">
          <text class="load-more-text">上拉加载更多</text>
        </view>

        <view v-if="activeTab === 'pending'" class="suggest-section">
          <text class="suggest-title">可能认识的人</text>
          <view class="suggest-grid">
            <FriendSuggestCard
              v-for="user in suggestionUsers"
              :key="user.id"
              :user="user"
              @tap="onTapSuggestion"
              @add="onAddSuggestion"
            />
          </view>
        </view>
      </view>
    </scroll-view>
  </view>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { onPullDownRefresh, onShow } from '@dcloudio/uni-app'
import { acceptFriendRequest, getFriendRequests, ignoreFriendRequest } from '../../../api/im'
import { getApiBaseUrl } from '../../../utils/request'
import FriendApplyEmpty from './components/FriendApplyEmpty.vue'
import FriendApplyRequestCard from './components/FriendApplyRequestCard.vue'
import FriendApplyTabs from './components/FriendApplyTabs.vue'
import FriendSuggestCard from './components/FriendSuggestCard.vue'
import { friendApplyTabs, suggestionUsers } from './modules/friend-apply-data'

const PAGE_SIZE = 20
const activeTab = ref('pending')
const hasPromptedLogin = ref(false)

const pendingState = reactive({
  items: [],
  total: 0,
  hasMore: true,
  nextCursor: '',
  loading: false,
  loadingMore: false,
  error: ''
})

const sentState = reactive({
  items: [],
  total: 0,
  hasMore: true,
  nextCursor: '',
  loading: false,
  loadingMore: false,
  error: ''
})

const getState = (tab) => (tab === 'pending' ? pendingState : sentState)

const currentState = computed(() => getState(activeTab.value))
const currentRequests = computed(() => currentState.value.items)

const listHeaderText = computed(() => {
  if (activeTab.value === 'pending') {
    return `最近申请 (${currentState.value.total})`
  }
  return `已发送申请 (${currentState.value.total})`
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

  pendingState.items = []
  sentState.items = []
  pendingState.hasMore = false
  sentState.hasMore = false

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

const mapRequest = (item = {}) => {
  return {
    id: String(item.id || ''),
    name: String(item.name || '').trim() || '未命名用户',
    role: String(item.role || '').trim() || '职场人士',
    timeText: String(item.time_text || '').trim(),
    message: String(item.message || '').trim() || '希望和你建立联系。',
    unread: Boolean(item.unread),
    faded: false,
    canOperate: Boolean(item.can_operate),
    avatar: resolveAvatarUrl(item.avatar_url)
  }
}

const fetchRequests = async (tab, reset = false) => {
  if (!ensureLoggedIn()) {
    return
  }
  const state = getState(tab)
  if (state.loading || state.loadingMore) {
    return
  }
  if (!reset && (!state.hasMore || !state.nextCursor)) {
    return
  }

  if (reset) {
    state.loading = true
    state.error = ''
  } else {
    state.loadingMore = true
  }

  try {
    const data = await getFriendRequests({
      tab,
      cursor: reset ? '' : state.nextCursor,
      limit: PAGE_SIZE
    })
    const incoming = Array.isArray(data?.items) ? data.items.map((item) => mapRequest(item)) : []
    state.items = reset ? incoming : [...state.items, ...incoming]
    state.total = Number(data?.total || state.items.length)
    state.hasMore = Boolean(data?.has_more)
    state.nextCursor = String(data?.next_cursor || '').trim()
    state.error = ''
  } catch (err) {
    const statusCode = Number(err?.statusCode || 0)
    if (statusCode === 401) {
      clearLoginState()
      hasPromptedLogin.value = false
      ensureLoggedIn()
      return
    }
    const message = err?.message || '好友申请加载失败'
    if (reset && !state.items.length) {
      state.error = message
    }
    showToast(message)
  } finally {
    state.loading = false
    state.loadingMore = false
  }
}

const reloadActive = async () => {
  await fetchRequests(activeTab.value, true)
}

const onChangeTab = (key) => {
  const tab = key || 'pending'
  activeTab.value = tab
  const state = getState(tab)
  if (!state.items.length && !state.loading) {
    fetchRequests(tab, true)
  }
}

const onAccept = async (request) => {
  if (!request?.id) {
    return
  }
  try {
    await acceptFriendRequest(request.id)
    showToast(`已接受 ${request?.name || ''}`)
    await fetchRequests('pending', true)
  } catch (err) {
    showToast(err?.message || '操作失败，请稍后重试')
  }
}

const onIgnore = async (request) => {
  if (!request?.id) {
    return
  }
  try {
    await ignoreFriendRequest(request.id)
    showToast(`已忽略 ${request?.name || ''}`)
    await fetchRequests('pending', true)
  } catch (err) {
    showToast(err?.message || '操作失败，请稍后重试')
  }
}

const onRetry = () => {
  reloadActive()
}

const onDiscover = () => {
  uni.switchTab({
    url: '/pages/tab/discover/index'
  })
}

const onTapSuggestion = (user) => {
  showToast(`查看 ${user?.name || ''}`)
}

const onAddSuggestion = (user) => {
  showToast(`已发送给 ${user?.name || ''}`)
}

const onScrollToLower = () => {
  fetchRequests(activeTab.value, false)
}

onShow(() => {
  hasPromptedLogin.value = false
  reloadActive()
})

onPullDownRefresh(async () => {
  await reloadActive()
  uni.stopPullDownRefresh()
})
</script>

<style scoped>
.friend-apply-page {
  height: 100vh;
  overflow: hidden;
  background: #f8f6f6;
  color: #0f172a;
  font-family: 'Public Sans', 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

.content-scroll {
  height: calc(100vh - 76rpx);
}

.content-wrap {
  padding-bottom: calc(40rpx + env(safe-area-inset-bottom));
}

.list-header {
  background: rgba(241, 245, 249, 0.65);
  padding: 18rpx 24rpx;
}

.list-header-text {
  color: #64748b;
  font-size: 20rpx;
  line-height: 28rpx;
  font-weight: 600;
  letter-spacing: 1rpx;
}

.request-list {
  background: transparent;
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

.suggest-section {
  margin-top: 24rpx;
  padding: 0 24rpx;
}

.suggest-title {
  display: block;
  color: #0f172a;
  font-size: 26rpx;
  line-height: 36rpx;
  font-weight: 700;
  margin-bottom: 14rpx;
}

.suggest-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16rpx;
}

@media (prefers-color-scheme: dark) {
  .friend-apply-page {
    background: #221610;
    color: #f8fafc;
  }

  .list-header {
    background: rgba(30, 41, 59, 0.32);
  }

  .list-header-text,
  .status-text,
  .load-more-text {
    color: #9ca3af;
  }

  .suggest-title {
    color: #f8fafc;
  }
}
</style>
