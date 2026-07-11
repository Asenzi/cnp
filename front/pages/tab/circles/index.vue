<template>
  <view class="discover-page">
    <view class="page-shell">
      <view class="header-fixed">
        <TopSearchFilterHeader
          v-model="keyword"
          :search-placeholder="texts.searchPlaceholder"
          :top-padding-px="topPaddingPx"
          :right-inset-px="capsuleAvoidRightInsetPx"
          :search-bar-height-px="capsuleRowHeightPx"
          :left-items="topTabs"
          :active-left-key="activeTab"
          :right-items="circleRightControls"
          :active-right-keys="circleActiveRightKeys"
          @change-left="onChangeTab"
          @tap-right="onTapRightControl"
        />
      </view>

      <scroll-view
        class="circle-scroll"
        scroll-y
        :show-scrollbar="false"
        :lower-threshold="120"
        :refresher-enabled="true"
        :refresher-triggered="refreshing"
        refresher-background="#f6f6f8"
        :style="circleScrollStyle"
        @scrolltolower="onScrollToLower"
        @refresherrefresh="onRefresherRefresh"
        @refresherrestore="onRefresherRestore"
        @refresherabort="onRefresherRestore"
      >
        <template v-if="loading && !hasAny">
          <view v-for="i in 4" :key="`skeleton-${i}`" class="skeleton-card">
            <view class="skeleton-header">
              <view class="skeleton-avatar"></view>
              <view class="skeleton-info">
                <view class="skeleton-line skeleton-name"></view>
                <view class="skeleton-line skeleton-desc"></view>
              </view>
            </view>
            <view class="skeleton-stats">
              <view class="skeleton-stat"></view>
              <view class="skeleton-stat"></view>
            </view>
            <view class="skeleton-footer">
              <view class="skeleton-tag"></view>
              <view class="skeleton-tag"></view>
            </view>
          </view>
        </template>

        <view v-else-if="loadError && !hasAny" class="status-wrap">
          <text class="status-text">{{ loadError }}</text>
          <button class="retry-btn" hover-class="retry-btn-active" @tap="onRetry">
            {{ texts.retry }}
          </button>
        </view>

        <template v-else>
          <view v-if="showEmpty" class="empty-state">
            <image class="empty-icon-image" src="https://cos.cnptec.site/static/icon/data-block.png" mode="aspectFit" />
            <text class="empty-title">{{ texts.empty }}</text>
            <text class="empty-desc">试试调整筛选条件或搜索关键词</text>
          </view>

          <DiscoverList :items="circles" @interest="onToggleInterest" />

          <view v-if="loadingMore" class="load-more-wrap">
            <view class="loading-spinner loading-spinner-small"></view>
            <text class="load-more-text">{{ texts.loading }}</text>
          </view>
          <view v-else-if="hasMore && hasAny" class="load-more-wrap">
            <text class="load-more-text">{{ texts.loadMore }}</text>
          </view>
          <view v-else-if="loaded && hasAny" class="load-more-wrap">
            <text class="load-more-text">{{ texts.noMore }}</text>
          </view>
        </template>
      </scroll-view>
    </view>

    <NetworkFilterPanel
      :visible="filterVisible"
      :value="filters"
      :options="filterOptions"
      @close="onCloseFilter"
      @reset="onResetFilter"
      @apply="onApplyFilter"
    />
  </view>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { onPullDownRefresh, onShow } from '@dcloudio/uni-app'
import TopSearchFilterHeader from '../components/TopSearchFilterHeader.vue'
import { getDiscoverCircles } from '../../../api/circle'
import { toggleCircleCollection } from '../../../api/circle'
import DiscoverList from './components/DiscoverList.vue'
import NetworkFilterPanel from '../discover/components/NetworkFilterPanel.vue'
import { buildCityQueryCandidates } from '../discover/modules/city-query'
import { DEFAULT_INDUSTRY_OPTIONS } from '../discover/modules/industry-options'
import {
  getLocationErrorMessage,
  loadLocationFilterCache,
  resolveCurrentCityByGps,
  saveCurrentCity,
  saveLocationFilterCache
} from '../discover/modules/location'
import {
  consumeLatestCircleInterestChange,
  publishCircleInterestChange,
  subscribeCircleInterestChange,
  unsubscribeCircleInterestChange
} from '../../../utils/circle-interest'

const PAGE_SIZE = 20
const FIRST_PAGE_HISTORY_STORAGE_KEY = 'circle_first_page_history_v1'
const FIRST_PAGE_HISTORY_LIMIT = 60
const LOCATION_PAGE_RESULT_STORAGE_KEY = 'discover_location_page_result_v1'
let hasShownOnce = false
const initialLocationCache = loadLocationFilterCache()
const hasInitialLocationCache = Boolean(
  initialLocationCache.currentCity
  || initialLocationCache.selectedCity
  || initialLocationCache.mode === 'national'
)

const texts = {
  searchPlaceholder: '搜索圈子名称或关键词',
  loading: '加载中...',
  retry: '重新加载',
  empty: '暂无可推荐圈子',
  loadMore: '上拉加载更多',
  noMore: '没有更多圈子了',
  recommend: '推荐',
  industry: '行业',
  locating: '定位中...',
  defaultCity: '深圳',
  nationwideCity: '全国',
  pleaseLogin: '请先登录',
  defaultDesc: '欢迎进入圈子详情了解更多',
  unnamedCircle: '未命名圈子',
  fetchError: '圈子推荐加载失败，请稍后重试'
}

const keyword = ref('')
const activeTab = ref('recommend')
const circles = ref([])
const loading = ref(false)
const loadingMore = ref(false)
const loaded = ref(false)
const loadError = ref('')
const hasMore = ref(true)
const hasPromptedLogin = ref(false)
const recommendRequestId = ref('')
const firstPageHistoryByContext = ref({})
const refreshing = ref(false)
const filterVisible = ref(false)
const isNationalScope = ref(initialLocationCache.mode === 'national')
const initialSelectedCity = String(initialLocationCache.selectedCity || '').trim()
const filters = ref({
  city_name: isNationalScope.value ? '' : initialSelectedCity,
  industry_label: ''
})
const filterOptions = ref({
  industries: DEFAULT_INDUSTRY_OPTIONS
})
const isPageAlive = ref(true) // 页面生命周期标记
const loginRedirectTimer = ref(null) // 登录跳转定时器
const currentRequestId = ref(0) // 请求ID，用于取消过期请求
// 暂时隐藏城市定位筛选入口，但保留相关状态和逻辑，便于后续恢复
const showLocationFilter = false
let searchTimer = null
const interestSubmittingCodes = new Set()

const topTabs = [
  { key: 'recommend', label: texts.recommend }
]

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
const pxPerRpx = windowWidth / 750
const circleScrollTopPx = Math.ceil(
  topPaddingPx
  + capsuleRowHeightPx
  + 8
  + (84 * pxPerRpx)
  + (10 * pxPerRpx)
  + 12
)
const circleScrollStyle = computed(() => `padding-top:${circleScrollTopPx}px;`)

const cachedCity = String(
  initialLocationCache.currentCity
  || uni.getStorageSync('currentCity')
  || uni.getStorageSync('locationCity')
  || ''
).trim()
const locationText = ref(cachedCity || texts.defaultCity)
const locating = ref(false)
const activeCityQuery = ref('')

const hasAny = computed(() => circles.value.length > 0)
const showEmpty = computed(() => loaded.value && !loading.value && !hasAny.value && !loadError.value)
const normalizedKeyword = computed(() => String(keyword.value || '').trim())
const displayCityName = computed(() => {
  if (isNationalScope.value) {
    return texts.nationwideCity
  }
  return String(filters.value.city_name || '').trim() || locationText.value || texts.defaultCity
})
const effectiveCityName = computed(() => {
  if (!showLocationFilter) {
    return ''
  }
  if (isNationalScope.value) {
    return ''
  }
  const selectedCity = String(filters.value.city_name || '').trim()
  if (selectedCity) {
    return selectedCity
  }
  const normalizedCurrentCity = String(locationText.value || '').trim()
  return normalizedCurrentCity === texts.nationwideCity ? '' : normalizedCurrentCity
})
const hasCityOverride = computed(() => {
  if (isNationalScope.value) {
    return false
  }
  const selectedCity = String(filters.value.city_name || '').trim()
  return Boolean(selectedCity) && selectedCity !== locationText.value
})
const hasActiveFilter = computed(() => Boolean(filters.value.industry_label))
const industryControlText = computed(() => {
  return String(filters.value.industry_label || '').trim() || texts.industry
})
const circleRightControls = computed(() => [
  ...(showLocationFilter ? [{ key: 'locate', label: locating.value ? texts.locating : displayCityName.value, dot: hasCityOverride.value }] : []),
  { key: 'industry', label: industryControlText.value, dot: hasActiveFilter.value }
])
const circleActiveRightKeys = computed(() => {
  const keys = []
  if (showLocationFilter && hasCityOverride.value) {
    keys.push('locate')
  }
  if (hasActiveFilter.value) {
    keys.push('industry')
  }
  return keys
})

const buildRecoContextKey = ({ tab, keyword: nextKeyword, cityName, industryLabel }) => {
  return [
    String(tab || 'recommend').trim() || 'recommend',
    String(nextKeyword || '').trim().toLowerCase(),
    String(cityName || '').trim(),
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

const applySelectedCity = (city) => {
  const selectedCity = String(city || '').trim()
  if (!selectedCity) {
    return
  }
  activeCityQuery.value = ''
  if (selectedCity === texts.nationwideCity) {
    isNationalScope.value = true
    saveLocationFilterCache({
      mode: 'national',
      currentCity: locationText.value,
      selectedCity: ''
    })
    filters.value = {
      ...filters.value,
      city_name: ''
    }
    fetchCircles(true)
    return
  }
  isNationalScope.value = false
  const effectiveSelectedCity = selectedCity === locationText.value ? '' : selectedCity
  saveLocationFilterCache({
    mode: 'city',
    currentCity: locationText.value,
    selectedCity: effectiveSelectedCity
  })
  filters.value = {
    ...filters.value,
    city_name: effectiveSelectedCity
  }
  fetchCircles(true)
}

const applyRelocatedCity = (city) => {
  const relocatedCity = String(city || '').trim()
  if (!relocatedCity) {
    return
  }
  locationText.value = relocatedCity
  isNationalScope.value = false
  activeCityQuery.value = ''
  saveCurrentCity(relocatedCity)
  saveLocationFilterCache({
    mode: 'city',
    currentCity: relocatedCity,
    selectedCity: ''
  })
  filters.value = {
    ...filters.value,
    city_name: ''
  }
  fetchCircles(true)
}

const consumePendingLocationResult = () => {
  try {
    const payload = uni.getStorageSync(LOCATION_PAGE_RESULT_STORAGE_KEY)
    if (!payload || typeof payload !== 'object') {
      return
    }
    uni.removeStorageSync(LOCATION_PAGE_RESULT_STORAGE_KEY)
    if (payload.type === 'select') {
      applySelectedCity(payload.city)
      return
    }
    if (payload.type === 'relocate') {
      applyRelocatedCity(payload.city)
    }
  } catch {
    uni.removeStorageSync(LOCATION_PAGE_RESULT_STORAGE_KEY)
  }
}

const isLoggedIn = () => Boolean(String(uni.getStorageSync('token') || '').trim())

const ensureLoggedIn = () => {
  if (isLoggedIn()) {
    return true
  }

  if (!hasPromptedLogin.value) {
    hasPromptedLogin.value = true
    showToast(texts.pleaseLogin)
  }

  return false
}

const formatCompactNumber = (value) => {
  const numeric = Math.max(Number(value || 0), 0)
  if (numeric >= 10000) {
    const wan = numeric / 10000
    return wan >= 10 ? `${Math.floor(wan)}w` : `${wan.toFixed(1)}w`
  }
  if (numeric >= 1000) {
    const k = numeric / 1000
    return k >= 10 ? `${Math.floor(k)}k` : `${k.toFixed(1)}k`
  }
  return `${Math.floor(numeric)}`
}

const sanitizeCircleImage = (value) => {
  const normalized = String(value || '').trim()
  if (!normalized) {
    return ''
  }
  if (normalized === 'https://cos.cnptec.site/static/logo.png' || /\/static\/logo\.png(?:[?#].*)?$/i.test(normalized)) {
    return ''
  }
  if (/^(https?:\/\/tmp\/|wxfile:\/\/|file:\/\/|blob:|data:image\/)/i.test(normalized)) {
    return ''
  }
  return normalized
}

const mapCircleCard = (item = {}, index = 0) => {
  const industryLabel = String(item.industry_label || '').trim()
  const ownerCity = String(item.owner_city_name || '').trim()
  const description = String(item.description || '').trim()

  return {
    id: String(item.circle_code || '').trim() || `circle-${index}`,
    circleCode: String(item.circle_code || '').trim(),
    title: String(item.name || '').trim() || texts.unnamedCircle,
    description: description || texts.defaultDesc,
    industryLabel,
    ownerCity,
    members: formatCompactNumber(item.member_count || 0),
    posts: formatCompactNumber(item.post_count || 0),
    coverImage: sanitizeCircleImage(item.avatar_url || item.cover_url || ''),
    ownerName: String(item.owner_nickname || '').trim(),
    ownerAvatar: String(item.owner_avatar_url || '').trim(),
    ownerVerified: Boolean(item.owner_is_verified),
    collectCount: Number(item.collect_count ?? item.favorite_count ?? 0),
    collected: Boolean(item.is_collected ?? item.collected ?? item.is_interested ?? item.interested),
    isCollected: Boolean(item.is_collected ?? item.collected ?? item.is_interested ?? item.interested),
    is_collected: Boolean(item.is_collected ?? item.collected ?? item.is_interested ?? item.interested),
    interested: Boolean(item.is_collected ?? item.collected ?? item.is_interested ?? item.interested),
    isInterested: Boolean(item.is_collected ?? item.collected ?? item.is_interested ?? item.interested),
    is_interested: Boolean(item.is_collected ?? item.collected ?? item.is_interested ?? item.interested)
  }
}

const applyCircleInterestChange = (payload) => {
  const circleCode = String(payload?.circleCode || '').trim()
  if (!circleCode) {
    return
  }
  const interested = Boolean(payload?.interested)
  circles.value = circles.value.map((item) => {
    if (String(item?.circleCode || '').trim() !== circleCode) {
      return item
    }
    return {
      ...item,
      collected: interested,
      isCollected: interested,
      is_collected: interested,
      interested,
      isInterested: interested,
      is_interested: interested
    }
  })
}

const fetchCircles = async (reset = false) => {
  if (loading.value || loadingMore.value) {
    return
  }

  if (!reset && !hasMore.value) {
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
    const offset = reset ? 0 : circles.value.length
    const isRecommendTab = activeTab.value === 'recommend'
    const contextKey = buildRecoContextKey({
      tab: activeTab.value,
      keyword: normalizedKeyword.value,
      cityName: effectiveCityName.value,
      industryLabel: filters.value.industry_label || ''
    })
    const excludeCircleCodes = []
    const requestId = isRecommendTab
      ? (reset ? '' : String(recommendRequestId.value || '').trim())
      : ''
    const cityCandidates = reset
      ? (String(effectiveCityName.value || '').trim()
        ? buildCityQueryCandidates(effectiveCityName.value)
        : [])
      : [activeCityQuery.value || effectiveCityName.value]
    const queryCandidates = cityCandidates.filter(Boolean)
    const fallbackCandidates = queryCandidates.length ? queryCandidates : ['']

    let payload = null
    let selectedQueryCity = ''

    for (let index = 0; index < fallbackCandidates.length; index += 1) {
      const candidateCityName = fallbackCandidates[index]
      payload = await getDiscoverCircles({
        tab: activeTab.value,
        offset,
        limit: PAGE_SIZE,
        keyword: normalizedKeyword.value,
        city_name: candidateCityName,
        industry_label: filters.value.industry_label || '',
        request_id: requestId,
        exclude_circle_codes: excludeCircleCodes
      })

      // 检查请求是否已过期
      if (!isPageAlive.value || thisRequestId !== currentRequestId.value) {
        return
      }

      selectedQueryCity = candidateCityName
      const incomingItems = Array.isArray(payload?.items)
        ? payload.items.map((item, index2) => mapCircleCard(item, offset + index2))
        : []
      if (!reset || incomingItems.length > 0 || index === fallbackCandidates.length - 1) {
        break
      }
    }

    // 再次检查请求是否已过期
    if (!isPageAlive.value || thisRequestId !== currentRequestId.value) {
      return
    }

    if (isRecommendTab) {
      recommendRequestId.value = String(payload?.request_id || requestId || '').trim()
    } else {
      recommendRequestId.value = ''
    }

    const incoming = Array.isArray(payload?.items)
      ? payload.items.map((item, index) => mapCircleCard(item, offset + index))
      : []

    if (reset) {
      activeCityQuery.value = selectedQueryCity
    }

    if (isRecommendTab && reset && incoming.length) {
      appendFirstPageHistory(
        contextKey,
        incoming.map((item) => String(item.circleCode || '').trim()).filter(Boolean)
      )
    }

    if (reset) {
      circles.value = incoming
    } else {
      // 优化：使用 Map 提高去重性能
      const existedMap = new Map(circles.value.map((item) => [item.id, true]))
      const appended = incoming.filter((item) => !existedMap.has(item.id))
      circles.value = [...circles.value, ...appended]
    }

    hasMore.value = Boolean(payload?.has_more)
    loaded.value = true
    loadError.value = ''
  } catch (err) {
    // 检查请求是否已过期
    if (!isPageAlive.value || thisRequestId !== currentRequestId.value) {
      return
    }

    const statusCode = Number(err?.statusCode || 0)
    if (statusCode === 401) {
      uni.removeStorageSync('token')
      uni.removeStorageSync('isLoggedIn')
      uni.removeStorageSync('userInfo')
      if (reset && !hasAny.value) {
        loadError.value = texts.fetchError
      }
      return
    }

    const message = err?.message || texts.fetchError
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

const refreshLocation = async ({ silent = false } = {}) => {
  if (locating.value) {
    return
  }

  locating.value = true
  try {
    const city = await resolveCurrentCityByGps()
    locationText.value = city
    isNationalScope.value = false
    activeCityQuery.value = ''
    saveCurrentCity(city)
    saveLocationFilterCache({
      mode: 'city',
      currentCity: city,
      selectedCity: ''
    })
  } catch (error) {
    if (!silent) {
      showToast(getLocationErrorMessage(error))
    }
  } finally {
    locating.value = false
  }
}

const onChangeTab = (key) => {
  activeTab.value = key || 'recommend'
  fetchCircles(true)
}

const onOpenLocation = async () => {
  uni.navigateTo({
    url: `/pages/tab/discover/city/index?currentCity=${encodeURIComponent(locationText.value)}&selectedCity=${encodeURIComponent(displayCityName.value)}`,
    success: (res) => {
      res.eventChannel.emit('locationPage:init', {
        currentCity: locationText.value,
        selectedCity: displayCityName.value
      })
      res.eventChannel.on('locationPage:select', ({ city }) => {
        applySelectedCity(city)
      })
      res.eventChannel.on('locationPage:relocate', ({ city }) => {
        applyRelocatedCity(city)
      })
    }
  })
}

const onTapRightControl = async (key) => {
  if (key === 'locate') {
    onOpenLocation()
    return
  }
  if (key === 'industry') {
    filterVisible.value = true
  }
}

const onCloseFilter = () => {
  filterVisible.value = false
}

const onResetFilter = () => {
  filters.value = {
    industry_label: ''
  }
  filterVisible.value = false
  fetchCircles(true)
}

const onApplyFilter = (nextFilters) => {
  filters.value = {
    industry_label: String(nextFilters?.industry_label || '').trim()
  }
  filterVisible.value = false
  fetchCircles(true)
}

const onRetry = () => {
  fetchCircles(true)
}

const onToggleInterest = async (circle) => {
  if (!ensureLoggedIn()) {
    return
  }

  const circleCode = String(circle?.circleCode || '').trim()
  if (!circleCode || interestSubmittingCodes.has(circleCode)) {
    return
  }
  interestSubmittingCodes.add(circleCode)

  const wasInterested = Boolean(
    circle?.collected ||
    circle?.isCollected ||
    circle?.is_collected ||
    circle?.interested ||
    circle?.isInterested ||
    circle?.is_interested ||
    circle?.followed ||
    circle?.isFollowed ||
    circle?.is_followed
  )

  // 乐观更新UI
  const targetIndex = circles.value.findIndex((item) => item.circleCode === circleCode)
  if (targetIndex >= 0) {
    circles.value[targetIndex] = {
      ...circles.value[targetIndex],
      collected: !wasInterested,
      isCollected: !wasInterested,
      is_collected: !wasInterested,
      interested: !wasInterested,
      isInterested: !wasInterested,
      is_interested: !wasInterested
    }
  }

  try {
    const result = await toggleCircleCollection(circleCode, !wasInterested)
    const nextInterested = Boolean(result?.is_collected ?? result?.collected ?? result?.is_interested ?? result?.interested)
    applyCircleInterestChange({ circleCode, interested: nextInterested })
    publishCircleInterestChange(circleCode, nextInterested)

    uni.showToast({
      title: nextInterested ? '已收藏' : '已取消收藏',
      icon: 'none'
    })
  } catch (err) {
    // 失败时回滚
    if (targetIndex >= 0) {
      circles.value[targetIndex] = {
        ...circles.value[targetIndex],
        collected: wasInterested,
        isCollected: wasInterested,
        is_collected: wasInterested,
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
  } finally {
    interestSubmittingCodes.delete(circleCode)
  }
}

const onScrollToLower = () => {
  fetchCircles(false)
}

const refreshCircleData = async () => {
  firstPageHistoryByContext.value = loadStoredFirstPageHistory()
  await fetchCircles(true)
}

const runRefreshCircleData = async () => {
  // 防抖：如果正在刷新，忽略
  if (refreshing.value) {
    return
  }

  refreshing.value = true
  try {
    await refreshCircleData()
  } finally {
    refreshing.value = false
    uni.stopPullDownRefresh()
  }
}

const onRefresherRefresh = async () => {
  await runRefreshCircleData()
}

const onRefresherRestore = () => {
  refreshing.value = false
}

const stopKeywordWatch = watch(keyword, () => {
  if (searchTimer) {
    clearTimeout(searchTimer)
    searchTimer = null
  }
  searchTimer = setTimeout(() => {
    if (isPageAlive.value) {
      fetchCircles(true)
    }
    searchTimer = null
  }, 280)
})

onMounted(async () => {
  isPageAlive.value = true
  subscribeCircleInterestChange(applyCircleInterestChange)
  hasPromptedLogin.value = false
  firstPageHistoryByContext.value = loadStoredFirstPageHistory()
  if (!hasInitialLocationCache) {
    await refreshLocation({ silent: true })
  }
  await refreshCircleData()
})

onShow(() => {
  isPageAlive.value = true
  applyCircleInterestChange(consumeLatestCircleInterestChange())
  if (!hasShownOnce) {
    hasShownOnce = true
    return
  }
  consumePendingLocationResult()
})

onPullDownRefresh(async () => {
  await runRefreshCircleData()
})

onUnmounted(() => {
  isPageAlive.value = false
  unsubscribeCircleInterestChange(applyCircleInterestChange)

  // 停止 watch
  if (stopKeywordWatch) {
    stopKeywordWatch()
  }

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
.discover-page {
  height: 100vh;
  overflow: hidden;
  background: #f6f6f8;
  color: #111318;
  font-family: 'Manrope', 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

.page-shell {
  width: 100%;
  max-width: 750rpx;
  margin: 0 auto;
  height: 100vh;
  background: #ffffff;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 12rpx 32rpx rgba(15, 23, 42, 0.08);
}

.header-fixed {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 10;
  width: 100%;
  max-width: 750rpx;
  margin: 0 auto;
  background: #ffffff;
}

.circle-scroll {
  flex: 1;
  height: 0;
  min-height: 0;
  box-sizing: border-box;
  background: #f6f6f8;
}

/* 骨架屏样式 */
.skeleton-card {
  margin: 0 24rpx 16rpx;
  border-radius: 24rpx;
  background: #ffffff;
  padding: 32rpx;
  box-shadow: 0 4rpx 16rpx rgba(15, 23, 42, 0.04);
}

.skeleton-header {
  display: flex;
  align-items: center;
  gap: 20rpx;
  margin-bottom: 24rpx;
}

.skeleton-avatar {
  width: 88rpx;
  height: 88rpx;
  border-radius: 44rpx;
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
  width: 200rpx;
}

.skeleton-desc {
  width: 280rpx;
}

.skeleton-stats {
  display: flex;
  gap: 32rpx;
  margin-bottom: 24rpx;
}

.skeleton-stat {
  width: 120rpx;
  height: 32rpx;
  border-radius: 16rpx;
  background: linear-gradient(90deg, #f1f5f9 0%, #e2e8f0 50%, #f1f5f9 100%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}

.skeleton-footer {
  display: flex;
  gap: 12rpx;
}

.skeleton-tag {
  width: 100rpx;
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

.status-wrap,
.load-more-wrap {
  padding: 32rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16rpx;
}

.status-wrap {
  margin: 24rpx 32rpx;
  border-radius: 24rpx;
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
  min-height: 280rpx;
  box-shadow: 0 4rpx 16rpx rgba(15, 23, 42, 0.04);
}

/* 空状态样式 */
.empty-state {
  margin: 24rpx 32rpx;
  padding: 120rpx 32rpx 80rpx;
  border-radius: 0;
  background: transparent;
  box-shadow: none;
  min-height: auto;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20rpx;
}

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

.empty-desc {
  color: #64748b;
  font-size: 26rpx;
  line-height: 36rpx;
  text-align: center;
}

.status-text,
.load-more-text {
  color: #64748b;
  font-size: 26rpx;
  line-height: 36rpx;
}

.load-more-wrap {
  flex-direction: row;
  gap: 12rpx;
  justify-content: center;
}

.retry-btn {
  min-width: 240rpx;
  height: 72rpx;
  border: 0;
  border-radius: 36rpx;
  background: linear-gradient(135deg, #1a57db 0%, #1e40af 100%);
  color: #ffffff;
  font-size: 28rpx;
  line-height: 72rpx;
  font-weight: 700;
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

@media (prefers-color-scheme: dark) {
  .discover-page {
    background: #0f172a;
    color: #f8fafc;
  }

  .page-shell {
    background: #0f172a;
    box-shadow: none;
  }

  .header-fixed {
    background: #0f172a;
  }

  .skeleton-card {
    background: #1e293b;
    box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.3);
  }

  .skeleton-avatar,
  .skeleton-line,
  .skeleton-stat,
  .skeleton-tag {
    background: linear-gradient(90deg, #1e293b 0%, #334155 50%, #1e293b 100%);
    background-size: 200% 100%;
  }

  .status-wrap {
    background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
    box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.3);
  }

  .empty-state {
    background: transparent;
    box-shadow: none;
  }

  .empty-icon-wrap {
    background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
  }

  .loading-spinner {
    border-color: #334155;
    border-top-color: #3b82f6;
  }

  .empty-desc,
  .status-text,
  .load-more-text {
    color: #94a3b8;
  }

  .retry-btn {
    background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%);
    box-shadow: 0 8rpx 16rpx rgba(37, 99, 235, 0.3);
  }
}
</style>
