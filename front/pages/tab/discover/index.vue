<template>
  <view class="network-page">
    <view class="page-shell">
      <view class="tools-sticky">
        <TopSearchFilterHeader
          v-model="keyword"
          :search-placeholder="uiText.searchPlaceholder"
          :top-padding-px="topPaddingPx"
          :right-inset-px="capsuleAvoidRightInsetPx"
          :search-bar-height-px="capsuleRowHeightPx"
          :left-items="topTabs"
          :active-left-key="activeTab"
          :right-items="discoverRightControls"
          :active-right-keys="discoverActiveRightKeys"
          @change-left="onChangeTab"
          @tap-right="onTapRightControl"
        />
      </view>

      <scroll-view
        class="member-scroll"
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
        <view class="list-container">
          <template v-if="loading && !hasAny">
            <view v-for="i in 4" :key="`skeleton-${i}`" class="skeleton-card">
              <view class="skeleton-header">
                <view class="skeleton-avatar"></view>
                <view class="skeleton-info">
                  <view class="skeleton-line skeleton-name"></view>
                  <view class="skeleton-line skeleton-detail"></view>
                </view>
              </view>
              <view class="skeleton-tags">
                <view class="skeleton-tag"></view>
                <view class="skeleton-tag"></view>
              </view>
              <view class="skeleton-footer">
                <view class="skeleton-line skeleton-active"></view>
              </view>
            </view>
          </template>

          <view v-else-if="loadError && !hasAny" class="status-wrap">
            <text class="status-text">{{ loadError }}</text>
            <button class="retry-btn" hover-class="retry-btn-active" @tap="onRetry">{{ uiText.retry }}</button>
          </view>

          <template v-else>
            <view v-if="showEmpty" class="status-wrap">
              <text class="status-text">{{ uiText.empty }}</text>
            </view>

            <NetworkMemberCard
              v-for="item in members"
              :key="item.id"
              :member="item"
              @view="onViewProfile"
              @interest="onInterestMember"
              @verify="onGoVerify"
            />

            <view v-if="loadingMore" class="load-more-wrap">
              <text class="load-more-text">{{ uiText.loading }}</text>
            </view>
            <view v-else-if="hasMore && hasAny" class="load-more-wrap">
              <text class="load-more-text">{{ uiText.loadMore }}</text>
            </view>

            <NetworkEndHint v-if="!hasMore && hasAny" />
          </template>
        </view>
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
import {
  getNetworkFilterOptions,
  getNetworkRecommendations,
  reportNetworkFeedback,
  reportNetworkImpressions,
  toggleUserInterest
} from '../../../api/network'
import { getApiBaseUrl } from '../../../utils/request'
import TopSearchFilterHeader from '../components/TopSearchFilterHeader.vue'
import NetworkEndHint from './components/NetworkEndHint.vue'
import NetworkFilterPanel from './components/NetworkFilterPanel.vue'
import NetworkMemberCard from './components/NetworkMemberCard.vue'
import { buildCityQueryCandidates } from './modules/city-query'
import { DEFAULT_INDUSTRY_OPTIONS } from './modules/industry-options'
import {
  getLocationErrorMessage,
  loadLocationFilterCache,
  resolveCurrentCityByGps,
  saveCurrentCity,
  saveLocationFilterCache
} from './modules/location'

const PAGE_SIZE = 20
const FIRST_PAGE_HISTORY_STORAGE_KEY = 'network_first_page_history_v2'
const FIRST_PAGE_HISTORY_LIMIT = 20
const SPARSE_FIRST_PAGE_THRESHOLD = 3
const LOCATION_HISTORY_STORAGE_KEY = 'network_location_history_v1'
const LOCATION_HISTORY_LIMIT = 8
const LOCATION_PAGE_RESULT_STORAGE_KEY = 'discover_location_page_result_v1'
let hasShownOnce = false
const initialLocationCache = loadLocationFilterCache()
const hasInitialLocationCache = Boolean(
  initialLocationCache.currentCity
  || initialLocationCache.selectedCity
  || initialLocationCache.mode === 'national'
)

const uiText = {
  searchPlaceholder: '\u641c\u7d22\u4eba\u8109\u3001\u516c\u53f8\u6216\u804c\u4f4d',
  loading: '\u52a0\u8f7d\u4e2d...',
  retry: '\u91cd\u65b0\u52a0\u8f7d',
  empty: '\u6682\u65e0\u63a8\u8350\u4eba\u8109',
  loadMore: '\u4e0a\u62c9\u52a0\u8f7d\u66f4\u591a',
  recommend: '\u63a8\u8350',
  industry: '\u884c\u4e1a',
  locating: '\u5b9a\u4f4d\u4e2d...',
  loginFirst: '\u8bf7\u5148\u767b\u5f55',
  recommendedTag: '\u63a8\u8350\u4eba\u8109',
  sameCityTag: '\u540c\u57ce',
  unnamedUser: '\u672a\u547d\u540d\u7528\u6237',
  verifyLv1: 'LV1 \u5df2\u8ba4\u8bc1',
  defaultRole: '\u5546\u52a1\u4eba\u8109',
  activeFallback: '\u6700\u8fd1\u6d3b\u8dc3',
  recommendationLoadError: '\u4eba\u8109\u63a8\u8350\u52a0\u8f7d\u5931\u8d25\uff0c\u8bf7\u7a0d\u540e\u91cd\u8bd5',
  missingTarget: '\u76ee\u6807\u7528\u6237\u4fe1\u606f\u7f3a\u5931',
  viewerNickname: '\u5708\u8109\u94fe\u7528\u6237',
  friendIntroPrefix: '\u4f60\u597d\uff0c\u6211\u662f',
  friendIntroSuffix: '\uff0c\u60f3\u548c\u4f60\u5efa\u7acb\u8054\u7cfb\u3002',
  interestMarked: '\u5df2\u6807\u8bb0\u4e3a\u611f\u5174\u8da3',
  locatedPrefix: '\u5df2\u5b9a\u4f4d\u5230\uff1a',
  defaultCity: '\u5168\u90e8',
  nationwideCity: '\u5168\u56fd'
}

const topTabs = [
  { key: 'recommend', label: uiText.recommend }
]

const keyword = ref('')
const activeTab = ref('recommend')
const members = ref([])
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
const isNationalScope = ref(initialLocationCache.mode === 'national')
const initialSelectedCity = String(initialLocationCache.selectedCity || '').trim()

const filterVisible = ref(false)
const filters = ref({
  city_name: isNationalScope.value ? '' : initialSelectedCity,
  industry_label: ''
})
const filterOptions = ref({
  cities: [],
  industries: DEFAULT_INDUSTRY_OPTIONS
})
const loadedFilterOptions = ref(false)
const locationHistoryCities = ref([])

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

const cachedCity = String(
  initialLocationCache.currentCity
  || uni.getStorageSync('currentCity')
  || uni.getStorageSync('locationCity')
  || ''
).trim()
const currentCity = ref(cachedCity || uiText.defaultCity)
const locating = ref(false)
const activeCityQuery = ref('')

const hasAny = computed(() => members.value.length > 0)
const showEmpty = computed(() => loaded.value && !loading.value && !hasAny.value && !loadError.value)
const normalizedKeyword = computed(() => String(keyword.value || '').trim())
const displayCityName = computed(() => {
  if (isNationalScope.value) {
    return uiText.nationwideCity
  }
  return String(filters.value.city_name || '').trim() || currentCity.value || uiText.defaultCity
})
const effectiveCityName = computed(() => {
  if (isNationalScope.value) {
    return ''
  }
  const selectedCity = String(filters.value.city_name || '').trim()
  if (selectedCity) {
    return selectedCity
  }
  const normalizedCurrentCity = String(currentCity.value || '').trim()
  return normalizedCurrentCity === uiText.defaultCity ? '' : normalizedCurrentCity
})
const hasCityOverride = computed(() => {
  if (isNationalScope.value) {
    return false
  }
  const selectedCity = String(filters.value.city_name || '').trim()
  return Boolean(selectedCity) && selectedCity !== currentCity.value
})
const hasIndustryFilter = computed(() => {
  return Boolean(filters.value.industry_label)
})
const hotCities = computed(() => {
  const preferred = [
    currentCity.value,
    ...locationHistoryCities.value,
    ...filterOptions.value.cities,
    '\u5317\u4eac',
    '\u4e0a\u6d77',
    '\u5e7f\u5dde',
    '\u6df1\u5733',
    '\u676d\u5dde',
    '\u6210\u90fd',
    '\u6b66\u6c49',
    '\u82cf\u5dde',
    '\u897f\u5b89',
    '\u5929\u6d25',
    '\u91cd\u5e86',
    '\u5357\u4eac',
    '鍖椾含',
    '涓婃捣',
    '骞垮窞',
    '娣卞湷',
    '鏉窞',
    '鎴愰兘',
    '姝︽眽',
    '鑻忓窞',
    '瑗垮畨',
    '澶╂触',
    '閲嶅簡',
    '鍗椾含'
  ]
  return [...new Set(preferred.map((item) => String(item || '').trim()).filter(Boolean))].slice(0, 12)
})
const industryControlText = computed(() => {
  return String(filters.value.industry_label || '').trim() || uiText.industry
})
const discoverRightControls = computed(() => {
  return [
    {
      key: 'locate',
      label: locating.value ? uiText.locating : displayCityName.value,
      dot: hasCityOverride.value
    },
    { key: 'industry', label: industryControlText.value, dot: hasIndustryFilter.value }
  ]
})
const discoverActiveRightKeys = computed(() => {
  const keys = []
  if (hasCityOverride.value) {
    keys.push('locate')
  }
  if (hasIndustryFilter.value) {
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

const loadLocationHistory = () => {
  try {
    const raw = uni.getStorageSync(LOCATION_HISTORY_STORAGE_KEY)
    const parsed = typeof raw === 'string' ? JSON.parse(raw) : raw
    return Array.isArray(parsed)
      ? parsed.map((item) => String(item || '').trim()).filter(Boolean)
      : []
  } catch {
    return []
  }
}

const persistLocationHistory = () => {
  try {
    uni.setStorageSync(LOCATION_HISTORY_STORAGE_KEY, locationHistoryCities.value)
  } catch {
    // ignore storage errors
  }
}

const rememberVisitedCity = (city) => {
  const normalized = String(city || '').trim()
  if (!normalized || normalized === uiText.defaultCity) {
    return
  }
  const merged = [normalized, ...locationHistoryCities.value]
  locationHistoryCities.value = [...new Set(merged)].slice(0, LOCATION_HISTORY_LIMIT)
  persistLocationHistory()
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

const clearFirstPageHistory = (contextKey) => {
  if (!contextKey || !(contextKey in firstPageHistoryByContext.value)) {
    return
  }
  const nextValue = { ...firstPageHistoryByContext.value }
  delete nextValue[contextKey]
  firstPageHistoryByContext.value = nextValue
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
  if (selectedCity === uiText.nationwideCity) {
    isNationalScope.value = true
    saveLocationFilterCache({
      mode: 'national',
      currentCity: currentCity.value,
      selectedCity: ''
    })
    filters.value = {
      ...filters.value,
      city_name: ''
    }
    fetchRecommendations(true)
    return
  }
  isNationalScope.value = false
  const effectiveSelectedCity = selectedCity === currentCity.value ? '' : selectedCity
  saveLocationFilterCache({
    mode: 'city',
    currentCity: currentCity.value,
    selectedCity: effectiveSelectedCity
  })
  filters.value = {
    ...filters.value,
    city_name: effectiveSelectedCity
  }
  rememberVisitedCity(selectedCity)
  fetchRecommendations(true)
}

const applyRelocatedCity = (city) => {
  const relocatedCity = String(city || '').trim()
  if (!relocatedCity) {
    return
  }
  currentCity.value = relocatedCity
  isNationalScope.value = false
  activeCityQuery.value = ''
  saveLocationFilterCache({
    mode: 'city',
    currentCity: relocatedCity,
    selectedCity: ''
  })
  filters.value = {
    ...filters.value,
    city_name: ''
  }
  rememberVisitedCity(relocatedCity)
  fetchRecommendations(true)
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

const clearLoginState = () => {
  uni.removeStorageSync('token')
  uni.removeStorageSync('isLoggedIn')
  uni.removeStorageSync('userInfo')
}

const ensureLoggedIn = () => {
  if (isLoggedIn()) {
    return true
  }

  members.value = []
  loaded.value = true
  loadError.value = ''
  hasMore.value = false

  if (!hasPromptedLogin.value) {
    hasPromptedLogin.value = true
    showToast(uiText.loginFirst)
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
    const base = String(getApiBaseUrl() || 'http://172.20.10.3:8001').trim()
    return `${base}${normalized}`
  }
  return normalized
}

const isCorruptedTag = (text) => {
  const value = String(text || '').trim()
  if (!value) {
    return true
  }
  if (value.includes('???')) {
    return true
  }
  const questionCount = (value.match(/[?]/g) || []).length
  return questionCount >= 2 && questionCount >= Math.max(Math.floor(value.length / 2), 1)
}

const normalizeTag = (text) => {
  const value = String(text || '').trim()
  if (isCorruptedTag(value)) {
    return ''
  }
  return value.replace(/[\s\u3000]+/g, ' ')
}

const dedupeTags = (items = []) => {
  const seen = new Set()
  return items
    .map((item) => normalizeTag(item))
    .filter((item) => {
      if (!item || seen.has(item)) {
        return false
      }
      seen.add(item)
      return true
    })
}

const parseReasonDetail = (value) => {
  if (!value) {
    return {}
  }
  if (typeof value === 'object') {
    return value
  }
  if (typeof value !== 'string') {
    return {}
  }
  try {
    const parsed = JSON.parse(value)
    return parsed && typeof parsed === 'object' ? parsed : {}
  } catch {
    return {}
  }
}

const normalizeStringList = (value) => {
  if (Array.isArray(value)) {
    return dedupeTags(value)
  }
  if (typeof value === 'string') {
    return dedupeTags(
      value
        .split(/[，,、|]/)
        .map((item) => item.trim())
        .filter(Boolean)
    )
  }
  return []
}

const normalizeCircleList = (value) => {
  if (Array.isArray(value)) {
    return dedupeTags(value)
  }
  if (typeof value === 'string') {
    return dedupeTags(
      value
        .replace(/\uFF0C/g, ',')
        .replace(/\u3001/g, ',')
        .split(/[|,]/)
        .map((item) => item.trim())
        .filter(Boolean)
    )
  }
  return []
}

const joinNonEmpty = (...values) => {
  return values.map((item) => String(item || '').trim()).filter(Boolean).join(' | ')
}

const mapMemberCard = (item = {}) => {
  const businessUserId = String(item.user_id || '').trim()
  const cityName = String(item.city_name || '').trim()
  const intro = String(item.intro || '').trim()
  const industryLabel = String(item.industry_label || '').trim()
  const companyName = String(item.company_name || '').trim()
  const jobTitle = String(item.job_title || '').trim()
  const reasonTags = Array.isArray(item.reason_tags)
    ? item.reason_tags.map((tag) => normalizeTag(tag)).filter(Boolean)
    : []
  const reasonDetail = parseReasonDetail(item?.reason_detail)

  const rawCandidateCircles = normalizeCircleList(item.circle_names)
  const candidateCircles = rawCandidateCircles.length
    ? rawCandidateCircles
    : normalizeCircleList(reasonDetail.circle_names)
  const sharedCircles = normalizeCircleList(reasonDetail.shared_circle_names)
  const sharedSource = normalizeTag(reasonDetail.shared_connection_source || '')
  const fallbackCity = String(cityName || effectiveCityName.value || currentCity.value || '').trim()
  const visibleCircleTags = intro
    ? [intro]
    : candidateCircles.length
      ? candidateCircles.slice(0, 2)
      : [fallbackCity || uiText.sameCityTag]
  const circleTags = candidateCircles.length
    ? candidateCircles.slice(0, 2).map((circleName) => `同圈·${circleName}`)
    : [fallbackCity || uiText.sameCityTag]

  return {
    id: businessUserId || `${String(item.nickname || 'guest').trim()}-${cityName || 'city'}`,
    businessUserId,
    name: String(item.nickname || '').trim() || uiText.unnamedUser,
    verifyType: Boolean(item.is_verified) ? 'lv1' : '',
    verifyText: Boolean(item.is_verified) ? uiText.verifyLv1 : '',
    detailLine: joinNonEmpty(industryLabel, companyName, jobTitle) || industryLabel || cityName || uiText.defaultRole,
    circleTags: visibleCircleTags,
    reasonTags,
    activeText: String(item.active_text || '').trim() || uiText.activeFallback,
    avatar: resolveAvatarUrl(item.avatar_url),
    interested: Boolean(
      item.is_interested
      || item.interested
      || item.interest_status === 'interested'
      || item.is_followed
      || item.followed
      || item.follow_status === 'followed'
    ),
    score: Number(item.score || 0),
    reasonDetail: {
      ...reasonDetail,
      circle_names: candidateCircles,
      shared_circle_names: sharedCircles,
      shared_connection_source: sharedSource
    }
  }
}

const updateMemberInterestState = (memberId, interested) => {
  const targetId = String(memberId || '').trim()
  if (!targetId) {
    return
  }

  members.value = members.value.map((item) => {
    if (String(item.id || '').trim() !== targetId) {
      return item
    }
    return {
      ...item,
      interested: Boolean(interested)
    }
  })
}

const reportImpressions = async (items, currentRequestId) => {
  const targetUserIds = items
    .map((item) => String(item.businessUserId || '').trim())
    .filter(Boolean)
  if (!targetUserIds.length) {
    return
  }
  try {
    await reportNetworkImpressions({
      request_id: currentRequestId,
      scene: 'discover',
      tab: activeTab.value,
      target_user_ids: targetUserIds
    })
  } catch {
    // ignore telemetry errors
  }
}

const sendFeedback = async (member, eventType, ext = null) => {
  const targetUserId = String(member?.businessUserId || '').trim()
  if (!targetUserId) {
    return
  }
  try {
    await reportNetworkFeedback({
      request_id: requestId.value,
      scene: 'discover',
      tab: activeTab.value,
      target_user_id: targetUserId,
      event_type: eventType,
      ext: ext || {}
    })
  } catch {
    // ignore telemetry errors
  }
}

const fetchFilterOptions = async () => {
  if (loadedFilterOptions.value || !ensureLoggedIn()) {
    return
  }

  filterOptions.value = {
    cities: [],
    industries: DEFAULT_INDUSTRY_OPTIONS
  }
  loadedFilterOptions.value = true

  try {
    const remoteOptions = await getNetworkFilterOptions()
    const cities = Array.isArray(remoteOptions?.cities)
      ? remoteOptions.cities.map((item) => String(item || '').trim()).filter(Boolean)
      : []

    filterOptions.value = {
      cities,
      industries: DEFAULT_INDUSTRY_OPTIONS
    }
  } catch {
    // keep local options only
  }
}

const fetchRecommendations = async (reset = false) => {
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
    const recoContextKey = buildRecoContextKey({
      tab: activeTab.value,
      keyword: normalizedKeyword.value,
      cityName: effectiveCityName.value,
      industryLabel: filters.value.industry_label || ''
    })
    const historyIds = reset && Array.isArray(firstPageHistoryByContext.value[recoContextKey])
      ? firstPageHistoryByContext.value[recoContextKey].slice(0, FIRST_PAGE_HISTORY_LIMIT)
      : []
    const cityCandidates = reset
      ? (String(effectiveCityName.value || '').trim()
        ? buildCityQueryCandidates(effectiveCityName.value)
        : [])
      : [activeCityQuery.value || effectiveCityName.value]
    const queryCandidates = cityCandidates.filter(Boolean)
    const fallbackCandidates = queryCandidates.length ? queryCandidates : ['']

    let data = null
    let incoming = []
    let selectedQueryCity = ''
    let shouldRetryWithoutHistory = false

    for (let index = 0; index < fallbackCandidates.length; index += 1) {
      const candidateCityName = fallbackCandidates[index]
      const params = {
        tab: activeTab.value,
        request_id: reset ? '' : requestId.value,
        limit: PAGE_SIZE,
        cursor: reset ? '' : nextCursor.value,
        keyword: normalizedKeyword.value,
        city_name: candidateCityName,
        industry_label: filters.value.industry_label || ''
      }
      if (reset && historyIds.length) {
        params.exclude_user_ids = historyIds
      }

      data = await getNetworkRecommendations(params)
      incoming = Array.isArray(data?.items) ? data.items : []
      selectedQueryCity = candidateCityName
      shouldRetryWithoutHistory = reset
        && historyIds.length > 0
        && !normalizedKeyword.value
        && !filters.value.city_name
        && !filters.value.industry_label
        && incoming.length <= SPARSE_FIRST_PAGE_THRESHOLD

      if (!reset || incoming.length > 0 || index === fallbackCandidates.length - 1) {
        break
      }
    }

    if (shouldRetryWithoutHistory) {
      clearFirstPageHistory(recoContextKey)
      const retryParams = {
        tab: activeTab.value,
        request_id: reset ? '' : requestId.value,
        limit: PAGE_SIZE,
        cursor: reset ? '' : nextCursor.value,
        keyword: normalizedKeyword.value,
        city_name: selectedQueryCity,
        industry_label: filters.value.industry_label || ''
      }
      data = await getNetworkRecommendations(retryParams)
      incoming = Array.isArray(data?.items) ? data.items : []
    }

    const mapped = incoming.map((item) => mapMemberCard(item))

    if (reset) {
      members.value = mapped
    } else {
      const exists = new Set(members.value.map((item) => item.id))
      const appended = mapped.filter((item) => !exists.has(item.id))
      members.value = [...members.value, ...appended]
    }

    requestId.value = String(data?.request_id || '').trim()
    nextCursor.value = String(data?.next_cursor || '').trim()
    hasMore.value = Boolean(data?.has_more) && Boolean(nextCursor.value)
    loaded.value = true
    loadError.value = ''
    if (reset) {
      activeCityQuery.value = selectedQueryCity
    }

    if (reset) {
      const currentFirstPageIds = mapped
        .map((item) => String(item.businessUserId || '').trim())
        .filter(Boolean)
        .slice(0, PAGE_SIZE)
      if (mapped.length) {
        appendFirstPageHistory(recoContextKey, currentFirstPageIds)
      }
    }

    if (mapped.length) {
      reportImpressions(mapped, requestId.value)
    }
  } catch (err) {
    const statusCode = Number(err?.statusCode || 0)
    if (statusCode === 401) {
      clearLoginState()
      hasPromptedLogin.value = false
      ensureLoggedIn()
      return
    }

    const message = err?.message || uiText.recommendationLoadError
    if (reset && !hasAny.value) {
      loadError.value = message
    }
    showToast(message)
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

const onChangeTab = (tabKey) => {
  activeTab.value = tabKey || 'recommend'
  fetchRecommendations(true)
}

const onOpenFilter = async () => {
  await fetchFilterOptions()
  filterVisible.value = true
}

const onOpenLocation = async () => {
  await fetchFilterOptions()
  uni.navigateTo({
    url: `/pages/tab/discover/city/index?currentCity=${encodeURIComponent(currentCity.value)}&selectedCity=${encodeURIComponent(displayCityName.value)}`,
    success: (res) => {
      res.eventChannel.emit('locationPage:init', {
        currentCity: currentCity.value,
        selectedCity: displayCityName.value,
        historyCities: locationHistoryCities.value,
        hotCities: hotCities.value
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

const onTapRightControl = (key) => {
  if (key === 'locate') {
    onOpenLocation()
    return
  }
  if (key === 'industry') {
    onOpenFilter()
  }
}

const onCloseFilter = () => {
  filterVisible.value = false
}

const onResetFilter = () => {
  filters.value = {
    city_name: String(filters.value.city_name || '').trim(),
    industry_label: ''
  }
  filterVisible.value = false
  fetchRecommendations(true)
}

const onApplyFilter = (nextFilters) => {
  filters.value = {
    city_name: String(filters.value.city_name || '').trim(),
    industry_label: String(nextFilters?.industry_label || '').trim()
  }
  filterVisible.value = false
  fetchRecommendations(true)
}

const onViewProfile = (member) => {
  const targetUserId = String(member?.businessUserId || '').trim()
  if (!targetUserId) {
    showToast(uiText.missingTarget)
    return
  }
  sendFeedback(member, 'click_card')
  uni.navigateTo({
    url: `/pages/me/card/index?userId=${encodeURIComponent(targetUserId)}`
  })
}

const onInterestMember = async (member) => {
  const targetUserId = String(member?.businessUserId || '').trim()
  if (!targetUserId) {
    showToast(uiText.missingTarget)
    return
  }

  try {
    // 调用后端API切换感兴趣状态
    const response = await toggleUserInterest(targetUserId)

    // 根据后端返回的状态更新前端
    const newInterestState = Boolean(response?.is_interested)
    updateMemberInterestState(member.id, newInterestState)

    // 发送反馈事件用于推荐算法
    if (newInterestState) {
      await sendFeedback(member, 'apply_friend', {
        source: 'discover_interest_icon'
      })
      showToast(uiText.interestMarked)
    } else {
      await sendFeedback(member, 'cancel_interest', {
        source: 'discover_interest_icon'
      })
      showToast('已取消感兴趣')
    }
  } catch (error) {
    console.error('Toggle interest failed:', error)
    showToast('操作失败，请稍后重试')
  }
}

const onGoVerify = () => {
  uni.navigateTo({
    url: '/pages/me/auth/index'
  })
}

const onRetry = () => {
  fetchRecommendations(true)
}

const onScrollToLower = () => {
  fetchRecommendations(false)
}

const refreshLocation = async ({ silent = false, notifySuccess = false } = {}) => {
  if (locating.value) {
    return
  }

  locating.value = true
  try {
    const city = await resolveCurrentCityByGps()
    currentCity.value = city
    isNationalScope.value = false
    activeCityQuery.value = ''
    saveCurrentCity(city)
    saveLocationFilterCache({
      mode: 'city',
      currentCity: city,
      selectedCity: ''
    })
    rememberVisitedCity(city)

    if (notifySuccess) {
      showToast(`${uiText.locatedPrefix}${city}`)
    }
  } catch (error) {
    if (!silent) {
      showToast(getLocationErrorMessage(error))
    }
  } finally {
    locating.value = false
  }
}

const refreshDiscoverData = async () => {
  firstPageHistoryByContext.value = loadStoredFirstPageHistory()
  locationHistoryCities.value = loadLocationHistory()
  await fetchFilterOptions()
  await fetchRecommendations(true)
}

const runRefreshDiscoverData = async () => {
  if (refreshing.value) {
    return
  }
  refreshing.value = true
  try {
    await refreshDiscoverData()
  } finally {
    refreshing.value = false
    uni.stopPullDownRefresh()
  }
}

const onRefresherRefresh = async () => {
  await runRefreshDiscoverData()
}

const onRefresherRestore = () => {
  refreshing.value = false
}

watch(keyword, () => {
  if (searchTimer) {
    clearTimeout(searchTimer)
  }
  searchTimer = setTimeout(() => {
    fetchRecommendations(true)
  }, 280)
})

onMounted(async () => {
  hasPromptedLogin.value = false
  firstPageHistoryByContext.value = loadStoredFirstPageHistory()
  locationHistoryCities.value = loadLocationHistory()
  await fetchFilterOptions()
  if (!hasInitialLocationCache) {
    await refreshLocation({ silent: true, notifySuccess: false })
  }
  await fetchRecommendations(true)
})

onPullDownRefresh(async () => {
  await runRefreshDiscoverData()
})

onShow(() => {
  if (!hasShownOnce) {
    hasShownOnce = true
    return
  }
  consumePendingLocationResult()
})

onUnmounted(() => {
  if (searchTimer) {
    clearTimeout(searchTimer)
    searchTimer = null
  }
})
</script>

<style scoped>
.network-page {
  height: 100vh;
  overflow: hidden;
  background: #f6f6f8;
  font-family: 'Manrope', 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

.page-shell {
  width: 100%;
  max-width: 750rpx;
  margin: 0 auto;
  height: 100vh;
  background: #ffffff;
  overflow: hidden;
  box-shadow: 0 12rpx 32rpx rgba(15, 23, 42, 0.08);
  display: flex;
  flex-direction: column;
}

.tools-sticky {
  flex-shrink: 0;
  position: relative;
  z-index: 10;
  background: #ffffff;
  border-bottom: 1rpx solid #f1f5f9;
}

.member-scroll {
  flex: 1;
  min-height: 0;
  height: 0;
  background: #f6f6f8;
}

.list-container {
  background: #f6f6f8;
  padding: 0 24rpx calc(28rpx + env(safe-area-inset-bottom));
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

/* 骨架屏样式 */
.skeleton-card {
  border-radius: 20rpx;
  background: #ffffff;
  padding: 28rpx;
  box-shadow: 0 2rpx 12rpx rgba(15, 23, 42, 0.04);
}

.skeleton-header {
  display: flex;
  align-items: center;
  gap: 20rpx;
  margin-bottom: 20rpx;
}

.skeleton-avatar {
  width: 96rpx;
  height: 96rpx;
  border-radius: 48rpx;
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
  width: 180rpx;
}

.skeleton-detail {
  width: 240rpx;
}

.skeleton-tags {
  display: flex;
  gap: 12rpx;
  margin-bottom: 20rpx;
}

.skeleton-tag {
  width: 140rpx;
  height: 44rpx;
  border-radius: 22rpx;
  background: linear-gradient(90deg, #f1f5f9 0%, #e2e8f0 50%, #f1f5f9 100%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}

.skeleton-footer {
  padding-top: 16rpx;
  border-top: 1rpx solid #f1f5f9;
}

.skeleton-active {
  width: 160rpx;
}

@keyframes shimmer {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
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
  padding: 16rpx 0 8rpx;
  text-align: center;
}

.load-more-text {
  color: #94a3b8;
  font-size: 22rpx;
  line-height: 30rpx;
}

@media (prefers-color-scheme: dark) {
  .network-page {
    background: #111621;
  }

  .page-shell {
    background: #111621;
    box-shadow: none;
  }

  .tools-sticky {
    background: #111621;
    border-bottom-color: #1e293b;
  }

  .member-scroll,
  .list-container {
    background: rgba(17, 22, 33, 0.6);
  }

  .skeleton-card {
    background: #1e293b;
    box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.3);
  }

  .skeleton-avatar,
  .skeleton-line,
  .skeleton-tag {
    background: linear-gradient(90deg, #1e293b 0%, #334155 50%, #1e293b 100%);
    background-size: 200% 100%;
  }

  .skeleton-footer {
    border-top-color: #334155;
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
</style>
