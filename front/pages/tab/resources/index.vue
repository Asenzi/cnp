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
      :lower-threshold="120"
      :refresher-enabled="true"
      :refresher-triggered="refreshing"
      refresher-background="#f6f6f8"
      @scrolltolower="onScrollToLower"
      @refresherrefresh="onRefresherRefresh"
      @refresherrestore="onRefresherRestore"
      @refresherabort="onRefresherRestore"
    >
      <view class="feed-wrap">
        <view v-if="loading && !hasAny" class="status-wrap">
          <text class="status-text">加载中...</text>
        </view>

        <view v-else-if="loadError && !hasAny" class="status-wrap">
          <text class="status-text">{{ loadError }}</text>
          <button class="retry-btn" hover-class="retry-btn-active" @tap="onRetry">重新加载</button>
        </view>

        <template v-else>
          <ProfilePostCard
            v-for="post in feedCards"
            :key="post.id"
            :item="post"
            @detail="onTapDetail"
          />

          <view v-if="showEmpty" class="empty-wrap">
            <text class="empty-title">暂无匹配内容</text>
            <text class="empty-desc">换个关键词或筛选条件试试</text>
          </view>

          <view v-if="loadingMore" class="load-more-wrap">
            <text class="load-more-text">加载中...</text>
          </view>
          <view v-else-if="hasMore && hasAny" class="load-more-wrap">
            <text class="load-more-text">上拉加载更多</text>
          </view>
        </template>
      </view>
    </scroll-view>

    <ResourcePublishFab @tap="onTapPublish" />
  </view>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { onPullDownRefresh, onShow } from '@dcloudio/uni-app'
import { getResourceFeed, getResourceFilters } from '../../../api/post'
import TopSearchFilterHeader from '../components/TopSearchFilterHeader.vue'
import ProfilePostCard from '../../me/card/components/ProfilePostCard.vue'
import ResourcePublishFab from './components/ResourcePublishFab.vue'
import { mapProfilePostItem } from '../../me/card/modules/profile-home-view-model'
import { getLocationErrorMessage, resolveCurrentCityByGps, saveCurrentCity } from '../discover/modules/location'

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
const filterOptions = ref({
  industries: []
})
const currentCity = ref(String(uni.getStorageSync('currentCity') || uni.getStorageSync('locationCity') || '').trim() || texts.defaultCity)
const locating = ref(false)
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
const feedCards = computed(() => {
  return posts.value.map((post) => ({
    ...mapProfilePostItem(post),
    rawPost: post
  }))
})
const showEmpty = computed(() => loaded.value && !loading.value && !hasAny.value && !loadError.value)
const normalizedKeyword = computed(() => String(keyword.value || '').trim())
const hasActiveFilter = computed(() => Boolean(selectedIndustry.value))
const sortLabel = computed(() => (sortKey.value === 'latest' ? '最新' : '热门'))

const resourceLeftTabs = computed(() => [
  { key: 'cooperate', label: '找合作' },
  { key: 'resource', label: '找资源' },
  { key: 'venue', label: '活动' }
])

const resourceRightControls = computed(() => [
  ...(showLocationFilter ? [{ key: 'locate', label: locating.value ? texts.locating : currentCity.value, showArrow: false }] : []),
  { key: 'industry', label: selectedIndustry.value || '按行业', dot: hasActiveFilter.value },
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

  posts.value = []
  loaded.value = true
  loadError.value = ''
  hasMore.value = false
  requestId.value = ''

  if (!hasPromptedLogin.value) {
    hasPromptedLogin.value = true
    showToast(texts.loginFirst)
    setTimeout(() => {
      uni.navigateTo({
        url: '/pages/auth/login/index'
      })
    }, 220)
  }
  return false
}

const fetchFilterOptions = async () => {
  if (!ensureLoggedIn()) {
    return
  }
  try {
    const data = await getResourceFilters()
    filterOptions.value = {
      industries: Array.isArray(data?.industries) ? data.industries : []
    }
  } catch {
    // Keep fallback options.
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
    const incoming = Array.isArray(data?.items) ? data.items : []
    if (reset) {
      posts.value = incoming
    } else {
      const exists = new Set(posts.value.map((item) => item.post_code))
      const appended = incoming.filter((item) => !exists.has(item.post_code))
      posts.value = [...posts.value, ...appended]
    }

    requestId.value = String(data?.request_id || '').trim()
    nextCursor.value = String(data?.next_cursor || '').trim()
    hasMore.value = Boolean(data?.has_more) && Boolean(nextCursor.value)
    loaded.value = true
    loadError.value = ''

    if (reset && incoming.length) {
      const currentFirstPageIds = incoming
        .map((item) => String(item?.post_code || '').trim())
        .filter(Boolean)
        .slice(0, PAGE_SIZE)
      appendFirstPageHistory(recoContextKey, currentFirstPageIds)
    }
  } catch (err) {
    const statusCode = Number(err?.statusCode || 0)
    if (statusCode === 401) {
      clearLoginState()
      hasPromptedLogin.value = false
      ensureLoggedIn()
      return
    }

    const message = err?.message || texts.loadError
    if (reset && !hasAny.value) {
      loadError.value = message
    }
    showToast(message)
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

const onChangeFilter = (key) => {
  const nextMode = String(key || '').trim()
  activeMode.value = ['resource', 'venue'].includes(nextMode) ? nextMode : 'cooperate'
  fetchFeed(true)
}

const onSelectIndustry = () => {
  const options = ['全部行业', ...filterOptions.value.industries]
  if (!options.length) {
    showToast(texts.noIndustryOptions)
    return
  }
  uni.showActionSheet({
    itemList: options,
    success: (res) => {
      const index = Number(res?.tapIndex || 0)
      selectedIndustry.value = index === 0 ? '' : String(options[index] || '').trim()
      fetchFeed(true)
    }
  })
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
  uni.navigateTo({
    url: `/pages/resources/detail/index?postCode=${encodeURIComponent(postCode)}`
  })
}

const onTapPublish = () => {
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
  }
  searchTimer = setTimeout(() => {
    fetchFeed(true)
  }, 280)
})

onShow(() => {
  hasPromptedLogin.value = false
  currentCity.value = String(uni.getStorageSync('currentCity') || uni.getStorageSync('locationCity') || '').trim() || currentCity.value || texts.defaultCity
  refreshLocation({ silent: true })
})

onMounted(async () => {
  await refreshResourceData()
})

onPullDownRefresh(async () => {
  await runRefreshResourceData()
})

onUnmounted(() => {
  if (searchTimer) {
    clearTimeout(searchTimer)
    searchTimer = null
  }
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
  padding: 16rpx 24rpx calc(180rpx + env(safe-area-inset-bottom));
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.status-wrap,
.empty-wrap {
  border-radius: 16rpx;
  border: 1rpx dashed #cbd5e1;
  background: #ffffff;
  min-height: 220rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 14rpx;
}

.status-text,
.empty-desc {
  color: #64748b;
  font-size: 24rpx;
  line-height: 32rpx;
}

.empty-title {
  color: #111827;
  font-size: 30rpx;
  line-height: 38rpx;
  font-weight: 700;
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

.retry-btn::after {
  border: 0;
}

.retry-btn-active {
  opacity: 0.9;
}

.load-more-wrap {
  padding: 14rpx 0 8rpx;
  text-align: center;
}

.load-more-text {
  color: #94a3b8;
  font-size: 22rpx;
  line-height: 30rpx;
}

@media (prefers-color-scheme: dark) {
  .resource-page,
  .feed-scroll,
  .feed-wrap {
    background: #111621;
  }

  .status-wrap,
  .empty-wrap {
    background: #0f172a;
    border-color: #334155;
  }

  .status-text,
  .empty-desc {
    color: #94a3b8;
  }

  .empty-title {
    color: #f8fafc;
  }
}
</style>

