<template>
  <view class="resource-page">
    <TopSearchFilterHeader
      v-model="keyword"
      search-placeholder="搜索资源、需求或合作项目"
      :top-padding-px="topPaddingPx"
      :right-inset-px="capsuleAvoidRightInsetPx"
      :search-bar-height-px="capsuleRowHeightPx"
      :left-items="resourceLeftTabs"
      :active-left-key="activeMode"
      :right-items="resourceRightControls"
      :active-right-keys="resourceActiveRightKeys"
      @change-left="onChangeFilter"
      @tap-right="onTapRightControl"
    />

    <scroll-view
      class="feed-scroll"
      scroll-y
      :show-scrollbar="false"
      :lower-threshold="360"
      :refresher-enabled="true"
      :refresher-triggered="refreshing"
      refresher-background="#f6f6f8"
      @scrolltolower="onScrollToLower"
      @refresherrefresh="onRefresherRefresh"
      @refresherrestore="onRefresherRestore"
      @refresherabort="onRefresherRestore"
    >
      <view class="feed-wrap">
        <template v-if="loading && !hasAny">
          <view v-for="i in 4" :key="`skeleton-${i}`" class="skeleton-card">
            <view class="skeleton-header">
              <view class="skeleton-avatar"></view>
              <view class="skeleton-info">
                <view class="skeleton-line skeleton-name"></view>
                <view class="skeleton-line skeleton-time"></view>
              </view>
            </view>
            <view class="skeleton-content">
              <view class="skeleton-line skeleton-text"></view>
              <view class="skeleton-line skeleton-text"></view>
              <view class="skeleton-line skeleton-text-short"></view>
            </view>
            <view class="skeleton-footer">
              <view class="skeleton-tag"></view>
              <view class="skeleton-tag"></view>
            </view>
          </view>
        </template>

        <view v-else-if="loadError && !hasAny" class="status-wrap">
          <text class="status-text">{{ loadError }}</text>
          <button class="retry-btn" hover-class="retry-btn-active" @tap="onRetry">重新加载</button>
        </view>

        <template v-else>
          <!-- 活动卡片 -->
          <template v-for="(post, index) in feedCards">
            <VenueEventCard
              v-if="post.type === 'venue'"
              :key="post.id"
              :item="post"
              :show-interest="true"
              :style="{ animationDelay: `${index * 50}ms` }"
              class="feed-card-enter"
              @detail="onTapDetail"
              @interest="onToggleInterest"
            />
            <ProfilePostCard
              v-else
              :key="post.id"
              :item="post"
              :show-interest="true"
              :style="{ animationDelay: `${index * 50}ms` }"
              class="feed-card-enter"
              @detail="onTapDetail"
              @interest="onToggleInterest"
            />
          </template>

          <view v-if="showEmpty" class="empty-wrap">
            <image class="empty-icon-image" src="https://cos.cnptec.site/static/icon/data-block.png" mode="aspectFit" />
            <text class="empty-title">暂无匹配内容</text>
            <text class="empty-desc">换个关键词或筛选条件试试</text>
          </view>

          <template v-if="loadingMore">
            <view v-for="i in 2" :key="`paging-skeleton-${i}`" class="skeleton-card paging-skeleton-card">
              <view class="skeleton-header">
                <view class="skeleton-avatar"></view>
                <view class="skeleton-info">
                  <view class="skeleton-line skeleton-name"></view>
                  <view class="skeleton-line skeleton-time"></view>
                </view>
              </view>
              <view class="skeleton-content">
                <view class="skeleton-line skeleton-text"></view>
                <view class="skeleton-line skeleton-text-short"></view>
              </view>
            </view>
            <view class="load-more-wrap">
              <view class="loading-spinner loading-spinner-small"></view>
              <text class="load-more-text">加载中...</text>
            </view>
          </template>
          <view v-else-if="hasMore && hasAny" class="load-more-wrap">
            <text class="load-more-text">上拉加载更多</text>
          </view>
        </template>
      </view>
    </scroll-view>

    <ResourcePublishFab @tap="onTapPublish" />

    <NetworkFilterPanel
      :visible="filterVisible"
      :value="{ industry_label: selectedIndustry }"
      :options="{ industries: filterOptions.industries }"
      @close="onCloseFilter"
      @reset="onResetFilter"
      @apply="onApplyFilter"
    />
  </view>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { onPullDownRefresh, onShow } from '@dcloudio/uni-app'
import {
  getResourceFeed,
  getResourceFilters,
  reportResourceFeedback,
  reportResourceImpressions,
  toggleResourceInterest
} from '../../../api/post'
import TopSearchFilterHeader from '../components/TopSearchFilterHeader.vue'
import ProfilePostCard from '../../me/card/components/ProfilePostCard.vue'
import NetworkFilterPanel from '../discover/components/NetworkFilterPanel.vue'
// import VenueEventCard from './components/VenueEventCard.vue' // 第二版上线
import ResourcePublishFab from './components/ResourcePublishFab.vue'
import { mapProfilePostItem } from '../../me/card/modules/profile-home-view-model'
import { getLocationErrorMessage, resolveCurrentCityByGps, saveCurrentCity } from '../discover/modules/location'
import { INDUSTRY_OPTIONS } from '../../../utils/industry-options'

const PAGE_SIZE = 20
const FIRST_PAGE_HISTORY_STORAGE_KEY = 'resource_first_page_history_v1'
const FIRST_PAGE_HISTORY_LIMIT = 60

const texts = {
  loginFirst: '请先登录',
  loadError: '资源列表加载失败，请稍后重试',
  missingPostCode: '资源编号缺失',
  noIndustryOptions: '暂无可选行业',
  locating: '定位中...',
  defaultCity: '全部'
}

const keyword = ref('')
const activeMode = ref('cooperate')
const sortKey = ref('latest')
const selectedIndustry = ref('')

const posts = ref([])
const loading = ref(false)
const loadingMore = ref(false)
const loaded = ref(false)
const loadError = ref('')
const hasMore = ref(true)
const nextCursor = ref('')
const requestId = ref('')
const hasPromptedLogin = ref(false)
const firstPageHistoryByContext = ref({})
const refreshing = ref(false)
const filterVisible = ref(false)
const filterOptions = ref({
  industries: []
})
const currentCity = ref(String(uni.getStorageSync('currentCity') || uni.getStorageSync('locationCity') || '').trim() || texts.defaultCity)
const locating = ref(false)
const isPageAlive = ref(true) // 页面生命周期标记
const loginRedirectTimer = ref(null) // 登录跳转定时器
const currentRequestId = ref(0) // 请求ID，用于取消过期请求
const reportedImpressionKeys = ref(new Set())
// 暂时隐藏城市定位筛选入口，但保留相关状态和逻辑，便于后续恢复
const showLocationFilter = false

let searchTimer = null

const systemInfo = uni.getSystemInfoSync()
const menuButtonRect = typeof uni.getMenuButtonBoundingClientRect === 'function'
  ? uni.getMenuButtonBoundingClientRect()
  : null

const statusBarHeight = Number(systemInfo?.statusBarHeight || 0)
const capsuleTop = Number(menuButtonRect?.top || 0)
const capsuleHeight = Number(menuButtonRect?.height || 0)
const capsuleLeft = Number(menuButtonRect?.left || 0)
const windowWidth = Number(systemInfo?.windowWidth || 375)
const topPaddingPx = capsuleTop > 0 ? capsuleTop : statusBarHeight + 6
const capsuleRowHeightPx = capsuleHeight > 0 ? capsuleHeight : 32
const capsuleAvoidRightInsetPx = capsuleLeft > 0
  ? Math.max(windowWidth - capsuleLeft - 8, 0)
  : 0

const hasAny = computed(() => posts.value.length > 0)

// 优化：缓存 feedCards，避免每次都重新 map
const feedCards = computed(() => {
  return posts.value.map((post) => ({
    ...mapProfilePostItem(post),
    rawPost: post
  }))
})

const getFeedCardAnimationDelay = (index) => {
  return `${Math.min(Number(index || 0) % PAGE_SIZE, 4) * 35}ms`
}

const showEmpty = computed(() => loaded.value && !loading.value && !hasAny.value && !loadError.value)
const normalizedKeyword = computed(() => String(keyword.value || '').trim())
const hasActiveFilter = computed(() => Boolean(selectedIndustry.value))
const sortLabel = computed(() => (sortKey.value === 'latest' ? '最新' : '热门'))

const resourceLeftTabs = computed(() => [
  { key: 'cooperate', label: '需求' },
  { key: 'resource', label: '供应' },
  { key: 'venue', label: '活动' }
])

const resourceRightControls = computed(() => [
  ...(showLocationFilter ? [{ key: 'locate', label: locating.value ? texts.locating : currentCity.value, showArrow: false }] : []),
  { key: 'industry', label: selectedIndustry.value || '行业', dot: hasActiveFilter.value },
  { key: 'sort', label: sortLabel.value },
  { key: 'manage', label: '管理', showArrow: false }
])

const resourceActiveRightKeys = computed(() => {
  const keys = []
  if (hasActiveFilter.value) {
    keys.push('industry')
  }
  if (sortKey.value !== 'latest') {
    keys.push('sort')
  }
  return keys
})

const buildRecoContextKey = ({ mode, sort, keyword: nextKeyword, industryLabel }) => {
  return [
    String(mode || 'cooperate').trim() || 'cooperate',
    String(sort || 'latest').trim() || 'latest',
    String(nextKeyword || '').trim().toLowerCase(),
    String(industryLabel || '').trim()
  ].join('|')
}

const loadStoredFirstPageHistory = () => {
  try {
    const raw = uni.getStorageSync(FIRST_PAGE_HISTORY_STORAGE_KEY)
    if (!raw) {
      return {}
    }
    const parsed = typeof raw === 'string' ? JSON.parse(raw) : raw
    return parsed && typeof parsed === 'object' ? parsed : {}
  } catch {
    return {}
  }
}

const persistFirstPageHistory = () => {
  try {
    uni.setStorageSync(FIRST_PAGE_HISTORY_STORAGE_KEY, firstPageHistoryByContext.value)
  } catch {
    // ignore storage errors
  }
}

const appendFirstPageHistory = (contextKey, currentIds) => {
  const previousIds = Array.isArray(firstPageHistoryByContext.value[contextKey])
    ? firstPageHistoryByContext.value[contextKey]
    : []
  const merged = [...currentIds, ...previousIds]
  const deduped = []
  const seen = new Set()
  for (const item of merged) {
    const normalized = String(item || '').trim()
    if (!normalized || seen.has(normalized)) {
      continue
    }
    seen.add(normalized)
    deduped.push(normalized)
    if (deduped.length >= FIRST_PAGE_HISTORY_LIMIT) {
      break
    }
  }
  firstPageHistoryByContext.value = {
    ...firstPageHistoryByContext.value,
    [contextKey]: deduped
  }
  persistFirstPageHistory()
}

const showToast = (title) => {
  uni.showToast({
    title,
    icon: 'none'
  })
}

const reportFeedImpressions = (items = [], feedRequestId = '', tabKey = activeMode.value) => {
  const requestKey = String(feedRequestId || '').trim()
  if (!requestKey || !Array.isArray(items) || !items.length) {
    return
  }
  const postCodes = []
  const nextReportedKeys = new Set(reportedImpressionKeys.value)
  items.forEach((item) => {
    const postCode = String(item?.post_code || item?.postCode || '').trim()
    if (!postCode) {
      return
    }
    const key = `${requestKey}:${postCode}`
    if (nextReportedKeys.has(key)) {
      return
    }
    nextReportedKeys.add(key)
    postCodes.push(postCode)
  })
  reportedImpressionKeys.value = nextReportedKeys
  if (!postCodes.length) {
    return
  }
  reportResourceImpressions({
    request_id: requestKey,
    tab: tabKey,
    post_codes: postCodes
  }).catch(() => {
    // 曝光失败不影响浏览。
  })
}

const reportFeedFeedback = (postCode, eventType, ext = {}) => {
  const normalizedCode = String(postCode || '').trim()
  const normalizedEvent = String(eventType || '').trim()
  if (!normalizedCode || !normalizedEvent) {
    return
  }
  reportResourceFeedback({
    request_id: requestId.value,
    tab: activeMode.value,
    post_code: normalizedCode,
    event_type: normalizedEvent,
    ext
  }).catch(() => {
    // 行为反馈失败不阻塞用户操作。
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

  if (!hasPromptedLogin.value) {
    hasPromptedLogin.value = true
    showToast(texts.loginFirst)
  }
  return false
}

const fetchFilterOptions = async () => {
  try {
    await getResourceFilters()
    // 使用本地中文行业列表，忽略后端返回的英文列表
    filterOptions.value = {
      industries: INDUSTRY_OPTIONS
    }
  } catch {
    // 使用本地默认行业列表
    filterOptions.value = {
      industries: INDUSTRY_OPTIONS
    }
  }
}

const refreshLocation = async ({ silent = false } = {}) => {
  if (locating.value) {
    return
  }

  locating.value = true
  try {
    const city = await resolveCurrentCityByGps()
    currentCity.value = city
    saveCurrentCity(city)
  } catch (error) {
    if (!silent) {
      showToast(getLocationErrorMessage(error))
    }
  } finally {
    locating.value = false
  }
}

const fetchFeed = async (reset = false) => {
  if (loading.value || loadingMore.value) {
    return
  }
  if (!reset && (!hasMore.value || !nextCursor.value)) {
    return
  }

  // 生成新的请求ID
  const thisRequestId = ++currentRequestId.value

  if (reset) {
    loading.value = true
    loadError.value = ''
  } else {
    loadingMore.value = true
  }

  try {
    const params = {
      mode: activeMode.value,
      sort: sortKey.value,
      keyword: normalizedKeyword.value,
      industry_label: selectedIndustry.value,
      request_id: reset ? '' : requestId.value,
      cursor: reset ? '' : nextCursor.value,
      limit: PAGE_SIZE
    }
    const recoContextKey = buildRecoContextKey({
      mode: activeMode.value,
      sort: sortKey.value,
      keyword: normalizedKeyword.value,
      industryLabel: selectedIndustry.value
    })
    if (reset) {
      const historyIds = Array.isArray(firstPageHistoryByContext.value[recoContextKey])
        ? firstPageHistoryByContext.value[recoContextKey].slice(0, FIRST_PAGE_HISTORY_LIMIT)
        : []
      if (historyIds.length) {
        params.exclude_post_codes = historyIds
      }
    }

    const data = await getResourceFeed(params)

    // 检查请求是否已过期
    if (!isPageAlive.value || thisRequestId !== currentRequestId.value) {
      return
    }

    const incoming = Array.isArray(data?.items) ? data.items : []
    if (reset) {
      posts.value = incoming
    } else {
      // 优化：使用 Map 提高去重性能
      const existsMap = new Map(posts.value.map((item) => [item.post_code, true]))
      const appended = incoming.filter((item) => !existsMap.has(item.post_code))
      posts.value = [...posts.value, ...appended]
    }

    requestId.value = String(data?.request_id || '').trim()
    nextCursor.value = String(data?.next_cursor || '').trim()
    hasMore.value = Boolean(data?.has_more) && Boolean(nextCursor.value)
    loaded.value = true
    loadError.value = ''
    reportFeedImpressions(incoming, requestId.value, params.mode)

    if (reset && incoming.length) {
      const currentFirstPageIds = incoming
        .map((item) => String(item?.post_code || '').trim())
        .filter(Boolean)
        .slice(0, PAGE_SIZE)
      appendFirstPageHistory(recoContextKey, currentFirstPageIds)
    }
  } catch (err) {
    // 检查请求是否已过期
    if (!isPageAlive.value || thisRequestId !== currentRequestId.value) {
      return
    }

    const statusCode = Number(err?.statusCode || 0)
    if (statusCode === 401) {
      clearLoginState()
      if (reset && !hasAny.value) {
        loadError.value = texts.loadError
      }
      return
    }

    const message = err?.message || texts.loadError
    if (reset && !hasAny.value) {
      loadError.value = message
    }
    showToast(message)
  } finally {
    // 只有当前请求才更新 loading 状态
    if (thisRequestId === currentRequestId.value) {
      loading.value = false
      loadingMore.value = false
    }
  }
}

const onChangeFilter = (key) => {
  const nextMode = String(key || '').trim()
  activeMode.value = ['resource', 'venue'].includes(nextMode) ? nextMode : 'cooperate'
  fetchFeed(true)
}

const onSelectIndustry = () => {
  filterVisible.value = true
}

const onCloseFilter = () => {
  filterVisible.value = false
}

const onResetFilter = () => {
  selectedIndustry.value = ''
  filterVisible.value = false
  fetchFeed(true)
}

const onApplyFilter = (filters) => {
  selectedIndustry.value = filters?.industry_label || ''
  filterVisible.value = false
  fetchFeed(true)
}

const onToggleSort = () => {
  sortKey.value = sortKey.value === 'latest' ? 'popular' : 'latest'
  fetchFeed(true)
}

const onTapRightControl = (key) => {
  if (key === 'locate') {
    refreshLocation({ silent: false })
    return
  }
  if (key === 'manage') {
    if (!ensureLoggedIn()) {
      return
    }
    uni.navigateTo({
      url: '/pages/resources/manage/index'
    })
    return
  }
  if (key === 'industry') {
    onSelectIndustry()
    return
  }
  if (key === 'sort') {
    onToggleSort()
  }
}

const onTapDetail = (post) => {
  const postCode = String(post?.postCode || post?.rawPost?.post_code || post?.post_code || '').trim()
  if (!postCode) {
    showToast(texts.missingPostCode)
    return
  }

  // 判断是否为活动类型
  const type = String(post?.type || '').trim().toLowerCase()
  const isVenue = type === 'venue'

  const url = isVenue
    ? `/pages/resources/venue-detail/index?postCode=${encodeURIComponent(postCode)}`
    : `/pages/resources/detail/index?postCode=${encodeURIComponent(postCode)}`

  reportFeedFeedback(postCode, 'click_detail', { source: 'resource_feed' })
  uni.navigateTo({ url })
}

const onTapPublish = () => {
  if (!ensureLoggedIn()) {
    return
  }

  uni.navigateTo({
    url: '/pages/resources/publish/index',
    events: {
      created: () => {
        fetchFilterOptions()
        fetchFeed(true)
      }
    }
  })
}

const onToggleInterest = async (post) => {
  if (!ensureLoggedIn()) {
    return
  }

  const postCode = String(post?.postCode || post?.rawPost?.post_code || post?.post_code || '').trim()
  if (!postCode) {
    return
  }

  const wasInterested = Boolean(
    post?.interested ||
    post?.isInterested ||
    post?.is_interested ||
    post?.rawPost?.interested ||
    post?.rawPost?.isInterested ||
    post?.rawPost?.is_interested ||
    post?.followed ||
    post?.isFollowed ||
    post?.is_followed
  )

  // 乐观更新UI - 更新原始posts数组
  const targetIndex = posts.value.findIndex((item) => item.post_code === postCode)

  if (targetIndex >= 0) {
    posts.value[targetIndex] = {
      ...posts.value[targetIndex],
      interested: !wasInterested,
      isInterested: !wasInterested,
      is_interested: !wasInterested
    }
  }

  try {
    await toggleResourceInterest(postCode)
    reportFeedFeedback(postCode, wasInterested ? 'cancel_interest' : 'interest', { source: 'resource_feed' })

    uni.showToast({
      title: wasInterested ? '已取消感兴趣' : '已标记感兴趣',
      icon: 'none'
    })
  } catch (err) {
    // 失败时回滚
    if (targetIndex >= 0) {
      posts.value[targetIndex] = {
        ...posts.value[targetIndex],
        interested: wasInterested,
        isInterested: wasInterested,
        is_interested: wasInterested
      }
    }

    const message = err?.message || '操作失败，请稍后重试'
    uni.showToast({
      title: message,
      icon: 'none'
    })
  }
}

const onRetry = () => {
  fetchFeed(true)
}

const onScrollToLower = () => {
  fetchFeed(false)
}

const refreshResourceData = async () => {
  firstPageHistoryByContext.value = loadStoredFirstPageHistory()
  await refreshLocation({ silent: true })
  await fetchFilterOptions()
  await fetchFeed(true)
}

const runRefreshResourceData = async () => {
  // 防抖：如果正在刷新，忽略
  if (refreshing.value) {
    return
  }

  refreshing.value = true
  try {
    await refreshResourceData()
  } finally {
    refreshing.value = false
    uni.stopPullDownRefresh()
  }
}

const onRefresherRefresh = async () => {
  await runRefreshResourceData()
}

const onRefresherRestore = () => {
  refreshing.value = false
}

watch(keyword, () => {
  if (searchTimer) {
    clearTimeout(searchTimer)
    searchTimer = null
  }
  searchTimer = setTimeout(() => {
    if (isPageAlive.value) {
      fetchFeed(true)
    }
    searchTimer = null
  }, 280)
})

onShow(() => {
  isPageAlive.value = true
  hasPromptedLogin.value = false
  currentCity.value = String(uni.getStorageSync('currentCity') || uni.getStorageSync('locationCity') || '').trim() || currentCity.value || texts.defaultCity
  refreshLocation({ silent: true })
})

onMounted(async () => {
  isPageAlive.value = true
  await refreshResourceData()
})

onPullDownRefresh(async () => {
  await runRefreshResourceData()
})

onUnmounted(() => {
  isPageAlive.value = false

  // 清理所有定时器
  if (searchTimer) {
    clearTimeout(searchTimer)
    searchTimer = null
  }

  if (loginRedirectTimer.value) {
    clearTimeout(loginRedirectTimer.value)
    loginRedirectTimer.value = null
  }

  // 取消所有进行中的请求
  currentRequestId.value++
})
</script>

<style scoped>
.resource-page {
  height: 100vh;
  overflow: hidden;
  background: #f6f6f8;
  font-family: 'Manrope', 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

.feed-scroll {
  height: calc(100vh - 248rpx);
  background: #f6f6f8;
}

.feed-wrap {
  padding: 24rpx 32rpx calc(120rpx + env(safe-area-inset-bottom));
  display: flex;
  flex-direction: column;
  gap: 24rpx;
}

/* 卡片进入动画 */
.feed-card-enter {
  animation: fadeInUp 0.4s ease-out forwards;
  opacity: 0;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20rpx);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 骨架屏样式 */
.skeleton-card {
  border-radius: 24rpx;
  background: #ffffff;
  padding: 32rpx;
  box-shadow: 0 4rpx 16rpx rgba(15, 23, 42, 0.04);
  animation: fadeInUp 0.4s ease-out forwards;
}

.paging-skeleton-card {
  animation: none;
}

.skeleton-header {
  display: flex;
  align-items: center;
  gap: 20rpx;
  margin-bottom: 24rpx;
}

.skeleton-avatar {
  width: 80rpx;
  height: 80rpx;
  border-radius: 40rpx;
  background: linear-gradient(90deg, #f1f5f9 0%, #e2e8f0 50%, #f1f5f9 100%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  flex-shrink: 0;
}

.skeleton-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.skeleton-line {
  height: 24rpx;
  border-radius: 12rpx;
  background: linear-gradient(90deg, #f1f5f9 0%, #e2e8f0 50%, #f1f5f9 100%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}

.skeleton-name {
  width: 160rpx;
}

.skeleton-time {
  width: 120rpx;
}

.skeleton-content {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
  margin-bottom: 24rpx;
}

.skeleton-text {
  width: 100%;
  height: 28rpx;
}

.skeleton-text-short {
  width: 60%;
  height: 28rpx;
}

.skeleton-footer {
  display: flex;
  gap: 16rpx;
}

.skeleton-tag {
  width: 120rpx;
  height: 48rpx;
  border-radius: 24rpx;
  background: linear-gradient(90deg, #f1f5f9 0%, #e2e8f0 50%, #f1f5f9 100%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}

@keyframes shimmer {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}

.status-wrap,
.empty-wrap {
  min-height: 320rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 20rpx;
  padding: 120rpx 32rpx 80rpx;
}

/* 加载动画 */
.loading-spinner {
  width: 48rpx;
  height: 48rpx;
  border: 4rpx solid #e2e8f0;
  border-top-color: #1a57db;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.loading-spinner-small {
  width: 32rpx;
  height: 32rpx;
  border-width: 3rpx;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.status-text,
.empty-desc {
  color: #64748b;
  font-size: 26rpx;
  line-height: 36rpx;
}

/* 空状态图标 */
.empty-icon-image {
  width: 200rpx;
  height: 200rpx;
  margin-bottom: 12rpx;
}

.empty-icon-wrap {
  width: 120rpx;
  height: 120rpx;
  border-radius: 60rpx;
  background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 8rpx;
}

.empty-title {
  color: #1e293b;
  font-size: 32rpx;
  line-height: 44rpx;
  font-weight: 600;
  margin-top: 8rpx;
}

.retry-btn {
  height: 72rpx;
  border-radius: 36rpx;
  border: 0;
  padding: 0 40rpx;
  font-size: 28rpx;
  line-height: 72rpx;
  color: #ffffff;
  background: linear-gradient(135deg, #1a57db 0%, #1e40af 100%);
  box-shadow: 0 8rpx 16rpx rgba(26, 87, 219, 0.2);
  margin-top: 8rpx;
}

.retry-btn::after {
  border: 0;
}

.retry-btn-active {
  opacity: 0.85;
  transform: scale(0.98);
}

.load-more-wrap {
  padding: 20rpx 0 12rpx;
  text-align: center;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16rpx;
}

.load-more-text {
  color: #94a3b8;
  font-size: 24rpx;
  line-height: 32rpx;
}

@media (prefers-color-scheme: dark) {
  .resource-page,
  .feed-scroll,
  .feed-wrap {
    background: #0f172a;
  }

  .skeleton-card {
    background: #1e293b;
    box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.3);
  }

  .skeleton-avatar,
  .skeleton-line,
  .skeleton-tag {
    background: linear-gradient(90deg, #1e293b 0%, #334155 50%, #1e293b 100%);
    background-size: 200% 100%;
  }

  .status-wrap,
  .empty-wrap {
    background: transparent;
  }

  .loading-spinner {
    border-color: #334155;
    border-top-color: #3b82f6;
  }

  .empty-icon-wrap {
    background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
  }

  .status-text,
  .empty-desc {
    color: #94a3b8;
  }

  .empty-title {
    color: #f1f5f9;
  }

  .retry-btn {
    background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%);
    box-shadow: 0 8rpx 16rpx rgba(37, 99, 235, 0.3);
  }
}
</style>
