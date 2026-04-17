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
        <view v-if="loading && !hasAny" class="status-wrap">
          <text class="status-text">{{ texts.loading }}</text>
        </view>

        <view v-else-if="loadError && !hasAny" class="status-wrap">
          <text class="status-text">{{ loadError }}</text>
          <button class="retry-btn" hover-class="retry-btn-active" @tap="onRetry">
            {{ texts.retry }}
          </button>
        </view>

        <template v-else>
          <view v-if="showEmpty" class="status-wrap">
            <text class="status-text">{{ texts.empty }}</text>
          </view>

          <DiscoverList :items="circles" />

          <view v-if="loadingMore" class="load-more-wrap">
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
  searchPlaceholder: '\u641c\u7d22\u5708\u5b50\u540d\u79f0\u6216\u5173\u952e\u8bcd',
  loading: '\u52a0\u8f7d\u4e2d...',
  retry: '\u91cd\u65b0\u52a0\u8f7d',
  empty: '\u6682\u65e0\u53ef\u63a8\u8350\u5708\u5b50',
  loadMore: '\u4e0a\u62c9\u52a0\u8f7d\u66f4\u591a',
  noMore: '\u6ca1\u6709\u66f4\u591a\u5708\u5b50\u4e86',
  recommend: '\u63a8\u8350',
  industry: '\u884c\u4e1a',
  locating: '\u5b9a\u4f4d\u4e2d...',
  defaultCity: '\u6df1\u5733',
  nationwideCity: '\u5168\u56fd',
  pleaseLogin: '\u8bf7\u5148\u767b\u5f55',
  defaultDesc: '\u6b22\u8fce\u8fdb\u5165\u5708\u5b50\u8be6\u60c5\u4e86\u89e3\u66f4\u591a',
  unnamedCircle: '\u672a\u547d\u540d\u5708\u5b50',
  fetchError: '\u5708\u5b50\u63a8\u8350\u52a0\u8f7d\u5931\u8d25\uff0c\u8bf7\u7a0d\u540e\u91cd\u8bd5'
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
// 暂时隐藏城市定位筛选入口，但保留相关状态和逻辑，便于后续恢复
const showLocationFilter = false
let searchTimer = null

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

  circles.value = []
  hasMore.value = false
  loaded.value = true
  loadError.value = ''

  if (!hasPromptedLogin.value) {
    hasPromptedLogin.value = true
    showToast(texts.pleaseLogin)
    setTimeout(() => {
      uni.navigateTo({
        url: '/pages/auth/login/index'
      })
    }, 220)
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

const mapCircleCard = (item = {}, index = 0) => {
  const industryLabel = String(item.industry_label || '').trim()
  const ownerCity = String(item.owner_city_name || '').trim()
  const description = String(item.description || '').trim()
  const reasonTags = Array.isArray(item.reason_tags)
    ? item.reason_tags.map((tag) => String(tag || '').trim()).filter(Boolean)
    : []

  let descText = description
  if (!descText) {
    descText = [industryLabel, ownerCity].filter(Boolean).join(' / ') || texts.defaultDesc
  } else if (reasonTags.length) {
    descText = `${reasonTags.join(' 路 ')} 路 ${description}`
  }

  return {
    id: String(item.circle_code || '').trim() || `circle-${index}`,
    circleCode: String(item.circle_code || '').trim(),
    title: String(item.name || '').trim() || texts.unnamedCircle,
    description: descText,
    industryLabel,
    ownerCity,
    members: formatCompactNumber(item.member_count || 0),
    posts: formatCompactNumber(item.post_count || 0),
    coverImage: String(item.cover_url || item.avatar_url || '').trim(),
    ownerName: String(item.owner_nickname || '').trim(),
    ownerAvatar: String(item.owner_avatar_url || '').trim(),
    ownerVerified: Boolean(item.owner_is_verified)
  }
}

const fetchCircles = async (reset = false) => {
  if (!ensureLoggedIn()) {
    return
  }

  if (loading.value || loadingMore.value) {
    return
  }

  if (!reset && !hasMore.value) {
    return
  }

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
    const excludeCircleCodes = isRecommendTab && reset
      ? (
        Array.isArray(firstPageHistoryByContext.value[contextKey])
          ? firstPageHistoryByContext.value[contextKey]
          : []
      )
      : []
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

      selectedQueryCity = candidateCityName
      const incomingItems = Array.isArray(payload?.items)
        ? payload.items.map((item, index2) => mapCircleCard(item, offset + index2))
        : []
      if (!reset || incomingItems.length > 0 || index === fallbackCandidates.length - 1) {
        break
      }
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
      const existed = new Set(circles.value.map((item) => item.id))
      const appended = incoming.filter((item) => !existed.has(item.id))
      circles.value = [...circles.value, ...appended]
    }

    hasMore.value = Boolean(payload?.has_more)
    loaded.value = true
    loadError.value = ''
  } catch (err) {
    const statusCode = Number(err?.statusCode || 0)
    if (statusCode === 401) {
      uni.removeStorageSync('token')
      uni.removeStorageSync('isLoggedIn')
      uni.removeStorageSync('userInfo')
      hasPromptedLogin.value = false
      ensureLoggedIn()
      return
    }

    const message = err?.message || texts.fetchError
    if (reset && !hasAny.value) {
      loadError.value = message
    }
    showToast(message)
  } finally {
    loading.value = false
    loadingMore.value = false
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

const onScrollToLower = () => {
  fetchCircles(false)
}

const refreshCircleData = async () => {
  firstPageHistoryByContext.value = loadStoredFirstPageHistory()
  await fetchCircles(true)
}

const runRefreshCircleData = async () => {
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

watch(keyword, () => {
  if (searchTimer) {
    clearTimeout(searchTimer)
  }
  searchTimer = setTimeout(() => {
    fetchCircles(true)
  }, 280)
})

onMounted(async () => {
  hasPromptedLogin.value = false
  firstPageHistoryByContext.value = loadStoredFirstPageHistory()
  if (!hasInitialLocationCache) {
    await refreshLocation({ silent: true })
  }
  await refreshCircleData()
})

onShow(() => {
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
  if (searchTimer) {
    clearTimeout(searchTimer)
    searchTimer = null
  }
})
</script>

<style scoped>
.discover-page {
  height: 100vh;
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
  box-sizing: border-box;
}

.status-wrap,
.load-more-wrap {
  padding: 24rpx 32rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12rpx;
}

.status-text,
.load-more-text {
  color: #94a3b8;
  font-size: 24rpx;
  line-height: 32rpx;
}

.retry-btn {
  min-width: 200rpx;
  height: 68rpx;
  border: 0;
  border-radius: 14rpx;
  background: #1a57db;
  color: #ffffff;
  font-size: 24rpx;
  line-height: 68rpx;
  font-weight: 700;
}

.retry-btn::after {
  border: 0;
}

.retry-btn-active {
  opacity: 0.86;
}

@media (prefers-color-scheme: dark) {
  .discover-page {
    background: #111621;
    color: #f8fafc;
  }

  .page-shell {
    background: #111621;
    box-shadow: none;
  }

  .header-fixed {
    background: #111621;
  }

  .status-text,
  .load-more-text {
    color: #94a3b8;
  }
}
</style>
