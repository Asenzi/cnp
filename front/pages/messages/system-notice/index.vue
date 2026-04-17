<template>
  <view class="notice-page">
    <scroll-view
      class="notice-scroll"
      scroll-y
      :show-scrollbar="false"
      :lower-threshold="100"
      @scrolltolower="onScrollToLower"
    >
      <view v-if="loading && !items.length" class="status-wrap">
        <text class="status-text">加载中...</text>
      </view>

      <view v-else-if="loadError && !items.length" class="status-wrap">
        <text class="status-text">{{ loadError }}</text>
        <button class="retry-btn" hover-class="retry-btn-active" @tap="onRetry">重新加载</button>
      </view>

      <view v-else-if="!items.length" class="status-wrap">
        <text class="status-text">暂无系统通知</text>
      </view>

      <view v-else class="list-wrap">
        <SystemNoticeItem
          v-for="item in items"
          :key="item.id"
          :notice="item"
        />
      </view>

      <view v-if="items.length && loadingMore" class="load-more-wrap">
        <text class="load-more-text">加载中...</text>
      </view>
      <view v-else-if="items.length && hasMore" class="load-more-wrap">
        <text class="load-more-text">上拉加载更多</text>
      </view>
    </scroll-view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onPullDownRefresh, onShow } from '@dcloudio/uni-app'
import { getSystemNotices } from '../../../api/im'
import SystemNoticeItem from './components/SystemNoticeItem.vue'

const PAGE_SIZE = 20

const items = ref([])
const loading = ref(false)
const loadingMore = ref(false)
const loadError = ref('')
const hasMore = ref(true)
const nextCursor = ref('')
const hasPromptedLogin = ref(false)

const hasAny = computed(() => items.value.length > 0)

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

  items.value = []
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

const mapItem = (item = {}) => {
  return {
    id: String(item.id || ''),
    title: String(item.title || '').trim() || '系统通知',
    content: String(item.content || '').trim() || '',
    timeText: String(item.time_text || '').trim(),
    isUnread: Boolean(item.is_unread)
  }
}

const fetchNotices = async (reset = false) => {
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
    const data = await getSystemNotices({
      cursor: reset ? '' : nextCursor.value,
      limit: PAGE_SIZE
    })
    const incoming = Array.isArray(data?.items) ? data.items.map((item) => mapItem(item)) : []
    if (reset) {
      items.value = incoming
    } else {
      items.value = [...items.value, ...incoming]
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
    const message = err?.message || '系统通知加载失败'
    if (reset && !hasAny.value) {
      loadError.value = message
    }
    showToast(message)
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

const onRetry = () => {
  fetchNotices(true)
}

const onScrollToLower = () => {
  fetchNotices(false)
}

onShow(() => {
  hasPromptedLogin.value = false
  fetchNotices(true)
})

onPullDownRefresh(async () => {
  await fetchNotices(true)
  uni.stopPullDownRefresh()
})
</script>

<style scoped>
.notice-page {
  height: 100vh;
  background: #f8f6f6;
}

.notice-scroll {
  height: 100vh;
}

.list-wrap {
  background: #ffffff;
}

.status-wrap,
.load-more-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  padding: 48rpx 24rpx;
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
  .notice-page,
  .notice-scroll {
    background: #111621;
  }

  .list-wrap {
    background: #0f172a;
  }

  .status-text,
  .load-more-text {
    color: #94a3b8;
  }
}
</style>
