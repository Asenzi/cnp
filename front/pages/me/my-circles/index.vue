<template>
  <view class="my-circles-page">
    <view class="page-shell">
      <view class="search-area"><MyCirclesSearchBar :model-value="keyword" :placeholder="activeCategory === 'owned' ? '搜索我创建的圈子' : '搜索我加入的圈子'" @search="onSearch" /></view>

      <view class="category-tabs"><view v-for="tab in circleTabs" :key="tab.key" :class="['category-tab', {active:activeCategory===tab.key}]" @tap="switchCategory(tab.key)">{{tab.label}}</view></view>
      <view v-if="loading && !hasAny" class="status-wrap">
        <text class="status-text">加载中...</text>
      </view>

      <view v-else-if="loadError && !hasAny" class="status-wrap">
        <text class="status-text">{{ loadError }}</text>
        <button class="retry-btn" hover-class="retry-btn-active" @tap="onRetry">
          重新加载
        </button>
      </view>

      <view v-else class="cards-wrap">
        <CircleDirectoryCard
          v-for="item in circles"
          :key="item.id"
          :circle="item"
        />
      </view>

      <MyCirclesEmpty v-if="showEmpty" />

      <view v-if="hasAny && hasMore" class="load-more-wrap">
        <text class="load-more-text">{{ loadingMore ? '加载中...' : '上拉加载更多' }}</text>
      </view>

      <MyCirclesFooter v-if="hasAny && !hasMore" @discover="onDiscoverMore" />
    </view>
  </view>
</template>

<script setup>
import { computed, onUnmounted, ref } from 'vue'
import { onPullDownRefresh, onReachBottom, onShow } from '@dcloudio/uni-app'
import { getMyCircles, getOwnedCircles } from '../../../api/circle'
import CircleDirectoryCard from '../../tab/circles/components/CircleDirectoryCard.vue'
import MyCirclesEmpty from '../../tab/circles/components/MyCirclesEmpty.vue'
import MyCirclesFooter from '../../tab/circles/components/MyCirclesFooter.vue'
import MyCirclesSearchBar from '../../tab/circles/components/MyCirclesSearchBar.vue'

const PAGE_SIZE = 20

const circleTabs=[{key:'joined',label:'加入的圈子'},{key:'owned',label:'创建的圈子'}]
const activeCategory=ref('joined')
const switchCategory=async key=>{if(activeCategory.value===key || loading.value || loadingMore.value)return;activeCategory.value=key;circles.value=[];total.value=0;loaded.value=false;await fetchMyCircles(true)}
const keyword = ref('')
const circles = ref([])
const total = ref(0)
const loading = ref(false)
const loadingMore = ref(false)
const loaded = ref(false)
const loadError = ref('')
const hasPromptedLogin = ref(false)

let searchTimer = null

const hasAny = computed(() => circles.value.length > 0)
const hasMore = computed(() => circles.value.length < total.value)
const showEmpty = computed(() => loaded.value && !loading.value && !hasAny.value && !loadError.value)
const normalizedKeyword = computed(() => String(keyword.value || '').trim())

const showToast = (title) => {
  uni.showToast({
    title,
    icon: 'none'
  })
}

const isLoggedIn = () => {
  const token = String(uni.getStorageSync('token') || '').trim()
  return Boolean(token)
}

const clearLoginState = () => {
  uni.removeStorageSync('token')
  uni.removeStorageSync('isLoggedIn')
  uni.removeStorageSync('userInfo')
}

const ensureLoggedIn = () => {
  if (isLoggedIn()) {
    return true
  }
  circles.value = []
  total.value = 0
  loaded.value = true
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

const formatCount = (value) => {
  const numeric = Number(value || 0)
  if (!Number.isFinite(numeric) || numeric <= 0) {
    return '0'
  }
  if (numeric >= 10000) {
    return `${(numeric / 10000).toFixed(1)}w`
  }
  return `${Math.floor(numeric)}`
}

const sanitizeCircleImage = (value) => {
  const normalized = String(value || '').trim()
  if (!normalized) {
    return 'https://cos.cnptec.site/static/logo.png'
  }
  if (/^(https?:\/\/tmp\/|wxfile:\/\/|file:\/\/|blob:|data:image\/)/i.test(normalized)) {
    return 'https://cos.cnptec.site/static/logo.png'
  }
  return normalized
}

const mapCircleCard = (item = {}) => {
  const circleCode = String(item.circle_code || '').trim()
  const description = String(item.description || '').trim()
  const industryLabel = String(item.industry_label || '').trim()

  return {
    id: circleCode,
    circleCode,
    title: String(item.name || '').trim() || '未命名圈子',
    description: description || (industryLabel ? `行业：${industryLabel}` : '暂无圈子简介'),
    industryLabel,
    members: formatCount(item.member_count || 0),
    posts: formatCount(item.post_count || 0),
    coverImage: sanitizeCircleImage(item.avatar_url || item.cover_url || ''),
    ownerVerified: Boolean(item.owner_is_verified)
  }
}

const fetchMyCircles = async (reset = false) => {
  if (!ensureLoggedIn()) {
    return
  }
  if (loading.value || loadingMore.value) {
    return
  }
  if (!reset && !hasMore.value) {
    return
  }

  const nextOffset = reset ? 0 : circles.value.length
  if (reset) {
    loading.value = true
    loadError.value = ''
  } else {
    loadingMore.value = true
  }

  try {
    const data = await (activeCategory.value === 'owned' ? getOwnedCircles : getMyCircles)({
      offset: nextOffset,
      limit: PAGE_SIZE,
      keyword: normalizedKeyword.value
    })
    const incomingItems = Array.isArray(data?.items) ? data.items : []
    const mappedItems = incomingItems.map((item) => mapCircleCard(item))

    if (reset) {
      // 重置时直接替换，并去重
      const uniqueMap = new Map()
      mappedItems.forEach((item) => {
        if (!uniqueMap.has(item.circleCode)) {
          uniqueMap.set(item.circleCode, item)
        }
      })
      circles.value = Array.from(uniqueMap.values())
    } else {
      // 追加时去重
      const existingCodes = new Set(circles.value.map((c) => c.circleCode))
      const newItems = mappedItems.filter((item) => !existingCodes.has(item.circleCode))
      circles.value = [...circles.value, ...newItems]
    }

    const serverTotal = Number(data?.total)
    const fallbackTotal = circles.value.length
    total.value = Number.isFinite(serverTotal) ? Math.max(serverTotal, fallbackTotal) : fallbackTotal
    loaded.value = true
    loadError.value = ''
  } catch (err) {
    const statusCode = Number(err?.statusCode || 0)
    if (statusCode === 401) {
      clearLoginState()
      hasPromptedLogin.value = false
      ensureLoggedIn()
      return
    }

    const message = err?.message || '圈子加载失败，请稍后重试'
    if (reset && !hasAny.value) {
      loadError.value = message
    }
    showToast(message)
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

const onSearch = (value) => {
  keyword.value = String(value || '')
  if (searchTimer) {
    clearTimeout(searchTimer)
  }
  searchTimer = setTimeout(() => {
    fetchMyCircles(true)
  }, 280)
}

const onRetry = () => {
  fetchMyCircles(true)
}


const onDiscoverMore = () => {
  uni.switchTab({
    url: '/pages/tab/circles/index'
  })
}

onShow(() => {
  hasPromptedLogin.value = false
  fetchMyCircles(true)
})

onPullDownRefresh(async () => {
  await fetchMyCircles(true)
  uni.stopPullDownRefresh()
})

onReachBottom(() => {
  fetchMyCircles(false)
})

onUnmounted(() => {
  if (searchTimer) {
    clearTimeout(searchTimer)
    searchTimer = null
  }
})
</script>

<style scoped>
.my-circles-page {
  min-height: 100vh;
  background: #f6f6f8;
}

.page-shell {
  min-height: 100vh;
  padding: 0 0 calc(40rpx + env(safe-area-inset-bottom));
  box-sizing: border-box;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 20rpx;
  margin-bottom: 14rpx;
}

.section-header-title {
  color: #64748b;
  font-size: 22rpx;
  line-height: 30rpx;
  font-weight: 600;
  letter-spacing: 2rpx;
}

.view-all-link {
  padding: 4rpx;
}

.view-all-link-active {
  opacity: 0.7;
}

.view-all-link-text {
  color: #1a57db;
  font-size: 24rpx;
  line-height: 32rpx;
  font-weight: 500;
}

.cards-wrap {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.status-wrap {
  border-radius: 16rpx;
  border: 1rpx dashed #cbd5e1;
  background: #ffffff;
  min-height: 220rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16rpx;
}

.status-text {
  color: #64748b;
  font-size: 24rpx;
  line-height: 32rpx;
}

.retry-btn {
  height: 58rpx;
  border-radius: 999rpx;
  border: 0;
  padding: 0 28rpx;
  font-size: 24rpx;
  line-height: 58rpx;
  color: #ffffff;
  background: #1a57db;
}

.retry-btn-active {
  opacity: 0.9;
}

.load-more-wrap {
  padding: 20rpx 0 8rpx;
  text-align: center;
}

.load-more-text {
  color: #94a3b8;
  font-size: 22rpx;
  line-height: 30rpx;
}

@media (prefers-color-scheme: dark) {
  .my-circles-page {
    background: #111621;
  }

  .section-header-title {
    color: #94a3b8;
  }

  .status-wrap {
    background: #0f172a;
    border-color: #334155;
  }

  .status-text {
    color: #94a3b8;
  }

  .load-more-text {
    color: #64748b;
  }
}
.category-tabs{display:flex;gap:32rpx;padding:20rpx 24rpx;background:#f6f6f8}.category-tab{font-size:28rpx;line-height:48rpx;color:#747b8b}.category-tab.active{color:#1a57db;border-bottom:4rpx solid #1a57db}.cards-wrap{display:flex;flex-direction:column;gap:18rpx;background:#f6f6f8;padding:18rpx 24rpx}
.search-area{padding:18rpx 24rpx;background:#f6f6f8}.category-tabs{background:#f6f6f8}.my-circles-page,.page-shell,.cards-wrap{background:#f6f6f8}
</style>
