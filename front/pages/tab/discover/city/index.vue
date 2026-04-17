<template>
  <view class="city-page">
    <view class="page-shell">
      <view class="top-nav" :style="navStyle">
        <view class="back-btn" hover-class="back-btn-hover" @tap="goBack">
          <image class="back-icon" mode="aspectFit" src="/static/me-icons/arrow-back-dark.png" />
        </view>
        <text class="nav-title">{{ uiText.title }}</text>
        <view class="nav-placeholder"></view>
      </view>

      <view class="search-wrap">
        <view class="search-box">
          <view class="search-icon">
            <view class="search-ring"></view>
            <view class="search-tail"></view>
          </view>
          <input
            :value="keyword"
            class="search-input"
            :placeholder="uiText.searchPlaceholder"
            placeholder-class="search-placeholder"
            @input="onInputKeyword"
          />
          <view
            class="all-city-btn"
            :class="isSelected(DEFAULT_CITY) ? 'all-city-btn-active' : ''"
            hover-class="all-city-btn-hover"
            @tap="onSelectAllCity"
          >
            <text class="all-city-btn-text" :class="isSelected(DEFAULT_CITY) ? 'all-city-btn-text-active' : ''">
              {{ uiText.allCity }}
            </text>
          </view>
        </view>
      </view>

      <view class="content-wrap">
        <scroll-view
          class="city-scroll"
          scroll-y
          :show-scrollbar="false"
          :scroll-into-view="scrollIntoView"
          scroll-with-animation
        >
          <view class="section">
            <view class="section-head">
              <text class="section-title">{{ uiText.currentSection }}</text>
              <button class="relocate-btn" hover-class="relocate-btn-hover" @tap="onRefreshLocation">
                {{ locating ? uiText.locating : uiText.relocate }}
              </button>
            </view>
            <view class="city-grid city-grid-current">
              <view
                class="city-chip"
                :class="isSelected(currentCity) ? 'city-chip-active' : ''"
                @tap="onSelectCity(currentCity)"
              >
                <text class="city-chip-text" :class="isSelected(currentCity) ? 'city-chip-text-active' : ''">
                  {{ currentCity }}
                </text>
              </view>
            </view>
          </view>

          <view v-if="visibleHotCities.length" class="section">
            <text class="section-title">{{ uiText.hotSection }}</text>
            <view class="city-grid">
              <view
                v-for="city in visibleHotCities"
                :key="`hot-${city}`"
                class="city-chip"
                :class="isSelected(city) ? 'city-chip-active' : ''"
                @tap="onSelectCity(city)"
              >
                <text class="city-chip-text" :class="isSelected(city) ? 'city-chip-text-active' : ''">
                  {{ city }}
                </text>
              </view>
            </view>
          </view>

          <view
            v-for="group in groupedCities"
            :id="`letter-${group.letter}`"
            :key="group.letter"
            class="section section-letter"
          >
            <text class="section-letter-title">{{ group.letter }}</text>
            <view class="city-grid">
              <view
                v-for="city in group.cities"
                :key="`${group.letter}-${city.label}`"
                class="city-chip"
                :class="isSelected(city.label) ? 'city-chip-active' : ''"
                @tap="onSelectCity(city.label)"
              >
                <text class="city-chip-text" :class="isSelected(city.label) ? 'city-chip-text-active' : ''">
                  {{ city.label }}
                </text>
              </view>
            </view>
          </view>

          <view v-if="keyword && !groupedCities.length && !visibleHotCities.length" class="empty-wrap">
            <text class="empty-text">{{ uiText.empty }}</text>
          </view>
        </scroll-view>

        <view v-if="indexedLetters.length" class="letter-index">
          <view
            v-for="letter in indexedLetters"
            :key="`idx-${letter}`"
            class="letter-item"
            hover-class="letter-item-hover"
            @tap="onTapIndex(letter)"
          >
            <text class="letter-item-text">{{ letter }}</text>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { PROVINCE_CITY_OPTIONS } from '../../../me/editInfo/modules/city-picker-data'
import {
  getLocationErrorMessage,
  loadLocationFilterCache,
  resolveCurrentCityByGps,
  saveCurrentCity
} from '../modules/location'

const uiText = {
  title: '\u9009\u62e9\u57ce\u5e02',
  searchPlaceholder: '\u641c\u7d22\u57ce\u5e02/\u62fc\u97f3',
  currentSection: '\u5f53\u524d\u5b9a\u4f4d',
  hotSection: '\u70ed\u95e8\u57ce\u5e02',
  relocate: '\u5237\u65b0\u5b9a\u4f4d',
  locating: '\u5b9a\u4f4d\u4e2d...',
  allCity: '\u5168\u56fd',
  empty: '\u672a\u627e\u5230\u5339\u914d\u57ce\u5e02',
  locateSuccessPrefix: '\u5df2\u5b9a\u4f4d\u5230\uff1a'
}
const DEFAULT_CITY = '\u5168\u56fd'
const LOCATION_PAGE_RESULT_STORAGE_KEY = 'discover_location_page_result_v1'
const FALLBACK_HOT_CITIES = [
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
  '\u5357\u4eac'
]

const systemInfo = uni.getSystemInfoSync()
const statusBarHeight = Number(systemInfo?.statusBarHeight || 0)
const capsuleRect = typeof uni.getMenuButtonBoundingClientRect === 'function'
  ? uni.getMenuButtonBoundingClientRect()
  : null
const navHeight = Number(capsuleRect?.height || 32)
const navTop = Number(capsuleRect?.top || 0)
const navStyle = `padding-top:${navTop > 0 ? navTop : statusBarHeight + 6}px;min-height:${navHeight}px;`

const openerEventChannel = ref(null)
const keyword = ref('')
const currentCity = ref('')
const selectedCity = ref('')
const hotCities = ref([])
const locating = ref(false)
const scrollIntoView = ref('')
const cachedLocationFilter = loadLocationFilterCache()

const decodeText = (value) => {
  const raw = String(value || '')
  if (!raw) {
    return ''
  }
  try {
    return decodeURIComponent(raw)
  } catch {
    return raw
  }
}

const normalizeText = (value) => decodeText(value).trim()

const buildHotCityList = (...sources) => {
  return [...new Set([
    ...sources.flatMap((items) => {
      if (Array.isArray(items)) {
        return items.map((item) => normalizeText(item))
      }
      return [normalizeText(items)]
    }),
    ...FALLBACK_HOT_CITIES
  ].filter((item) => item && item !== DEFAULT_CITY))].slice(0, 12)
}

const nationwideCityEntries = computed(() => {
  const deduped = new Map()
  for (const province of PROVINCE_CITY_OPTIONS) {
    const cities = Array.isArray(province?.cities) ? province.cities : []
    for (const city of cities) {
      const label = normalizeText(city?.label)
      const value = normalizeText(city?.value)
      if (!label || deduped.has(label)) {
        continue
      }
      deduped.set(label, {
        label,
        value
      })
    }
  }
  return Array.from(deduped.values())
})

const normalizedKeyword = computed(() => normalizeText(keyword.value).toLowerCase())

const visibleHotCities = computed(() => {
  const base = [...new Set(hotCities.value.map((item) => normalizeText(item)).filter(Boolean))]
  if (!normalizedKeyword.value) {
    return base
  }
  return base.filter((city) => city.toLowerCase().includes(normalizedKeyword.value))
})

const groupedCities = computed(() => {
  const groups = new Map()
  for (const item of nationwideCityEntries.value) {
    const keywordText = normalizedKeyword.value
    const matched = !keywordText
      || item.label.toLowerCase().includes(keywordText)
      || item.value.toLowerCase().includes(keywordText)
    if (!matched) {
      continue
    }

    const letter = (item.value.charAt(0) || '#').toUpperCase()
    if (!groups.has(letter)) {
      groups.set(letter, [])
    }
    groups.get(letter).push(item)
  }

  return Array.from(groups.entries())
    .sort((a, b) => a[0].localeCompare(b[0]))
    .map(([letter, cities]) => ({
      letter,
      cities: cities.sort((a, b) => a.value.localeCompare(b.value))
    }))
})

const indexedLetters = computed(() => groupedCities.value.map((group) => group.letter))

const showToast = (title) => {
  uni.showToast({
    title,
    icon: 'none'
  })
}

const isSelected = (city) => normalizeText(city) === normalizeText(selectedCity.value || currentCity.value)

const onInputKeyword = (event) => {
  keyword.value = String(event?.detail?.value || '')
}

const goBack = () => {
  uni.navigateBack()
}

const onTapIndex = (letter) => {
  scrollIntoView.value = ''
  setTimeout(() => {
    scrollIntoView.value = `letter-${letter}`
  }, 0)
}

const onSelectCity = (city) => {
  const normalizedCity = normalizeText(city)
  if (!normalizedCity) {
    return
  }
  selectedCity.value = normalizedCity
  uni.setStorageSync(LOCATION_PAGE_RESULT_STORAGE_KEY, {
    type: 'select',
    city: normalizedCity,
    timestamp: Date.now()
  })
  openerEventChannel.value?.emit('locationPage:select', { city: normalizedCity })
  setTimeout(() => {
    uni.navigateBack()
  }, 0)
}

const onSelectAllCity = () => {
  selectedCity.value = DEFAULT_CITY
  uni.setStorageSync(LOCATION_PAGE_RESULT_STORAGE_KEY, {
    type: 'select',
    city: DEFAULT_CITY,
    timestamp: Date.now()
  })
  openerEventChannel.value?.emit('locationPage:select', { city: DEFAULT_CITY })
  setTimeout(() => {
    uni.navigateBack()
  }, 0)
}

const onRefreshLocation = async () => {
  if (locating.value) {
    return
  }
  locating.value = true
  try {
    const city = await resolveCurrentCityByGps()
    currentCity.value = city
    selectedCity.value = city
    saveCurrentCity(city)
    uni.setStorageSync(LOCATION_PAGE_RESULT_STORAGE_KEY, {
      type: 'relocate',
      city,
      timestamp: Date.now()
    })
    openerEventChannel.value?.emit('locationPage:relocate', { city })
    showToast(`${uiText.locateSuccessPrefix}${city}`)
  } catch (error) {
    showToast(getLocationErrorMessage(error))
  } finally {
    locating.value = false
  }
}

onLoad((query) => {
  const queryCurrentCity = normalizeText(query?.currentCity)
  const querySelectedCity = normalizeText(query?.selectedCity)
  currentCity.value = queryCurrentCity || cachedLocationFilter.currentCity || DEFAULT_CITY
  selectedCity.value = querySelectedCity
    || (cachedLocationFilter.mode === 'national'
      ? DEFAULT_CITY
      : cachedLocationFilter.selectedCity || currentCity.value)
  hotCities.value = buildHotCityList(currentCity.value)

  const eventChannel = typeof getOpenerEventChannel === 'function'
    ? getOpenerEventChannel()
    : null
  openerEventChannel.value = eventChannel || null

  eventChannel?.on('locationPage:init', (payload = {}) => {
    const nextCurrentCity = normalizeText(payload.currentCity)
    const nextSelectedCity = normalizeText(payload.selectedCity)
    const nextHotCities = Array.isArray(payload.hotCities) ? payload.hotCities : []
    const historyCities = Array.isArray(payload.historyCities) ? payload.historyCities : []

    if (nextCurrentCity) {
      currentCity.value = nextCurrentCity
    }
    selectedCity.value = nextSelectedCity || currentCity.value
    hotCities.value = buildHotCityList(
      currentCity.value,
      historyCities,
      nextHotCities
    )
  })
})
</script>

<style scoped>
.city-page {
  height: 100vh;
  overflow: hidden;
  background: #ffffff;
  font-family: 'Manrope', 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

.page-shell {
  width: 100%;
  height: 100vh;
  background: #ffffff;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.top-nav {
  padding-left: 24rpx;
  padding-right: 24rpx;
  padding-bottom: 14rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
  background: #ffffff;
}

.back-btn,
.nav-placeholder {
  width: 72rpx;
  height: 72rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.back-btn-hover {
  opacity: 0.72;
}

.back-icon {
  width: 40rpx;
  height: 40rpx;
}

.nav-title {
  flex: 1;
  text-align: center;
  color: #0f172a;
  font-size: 38rpx;
  line-height: 52rpx;
  font-weight: 700;
}

.search-wrap {
  padding: 0 24rpx 16rpx;
  flex-shrink: 0;
  background: #ffffff;
}

.search-box {
  height: 76rpx;
  border-radius: 16rpx;
  background: #f3f4f6;
  display: flex;
  align-items: center;
  padding: 0 22rpx;
  gap: 12rpx;
}

.search-icon {
  width: 32rpx;
  height: 32rpx;
  position: relative;
  flex-shrink: 0;
}

.search-ring {
  width: 18rpx;
  height: 18rpx;
  border: 3rpx solid #9ca3af;
  border-radius: 999rpx;
}

.search-tail {
  position: absolute;
  right: 0;
  bottom: 4rpx;
  width: 10rpx;
  height: 3rpx;
  border-radius: 999rpx;
  background: #9ca3af;
  transform: rotate(45deg);
}

.search-input {
  flex: 1;
  min-width: 0;
  height: 76rpx;
  color: #111827;
  font-size: 26rpx;
}

.search-placeholder {
  color: #9ca3af;
}

.all-city-btn {
  flex-shrink: 0;
  min-width: 100rpx;
  height: 56rpx;
  padding: 0 18rpx;
  border-radius: 14rpx;
  border: 1rpx solid rgba(37, 99, 235, 0.18);
  background: rgba(255, 255, 255, 0.72);
  display: flex;
  align-items: center;
  justify-content: center;
}

.all-city-btn-active {
  border-color: rgba(37, 99, 235, 0.28);
  background: rgba(37, 99, 235, 0.12);
}

.all-city-btn-hover {
  opacity: 0.84;
}

.all-city-btn-text {
  color: #6b7280;
  font-size: 24rpx;
  line-height: 1;
  font-weight: 700;
}

.all-city-btn-text-active {
  color: #2563eb;
}

.content-wrap {
  position: relative;
  flex: 1;
  min-height: 0;
}

.city-scroll {
  height: 100%;
  box-sizing: border-box;
  padding: 0 56rpx 32rpx 24rpx;
}

.section {
  margin-top: 18rpx;
}

.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
}

.section-title,
.section-letter-title {
  color: #111827;
  font-size: 30rpx;
  line-height: 42rpx;
  font-weight: 700;
}

.section-letter {
  scroll-margin-top: 20rpx;
}

.relocate-btn {
  height: 54rpx;
  padding: 0 18rpx;
  border: 0;
  border-radius: 999rpx;
  background: rgba(37, 99, 235, 0.1);
  color: #2563eb;
  font-size: 22rpx;
  line-height: 54rpx;
  font-weight: 700;
}

.relocate-btn::after {
  border: 0;
}

.relocate-btn-hover {
  opacity: 0.84;
}

.city-grid {
  margin-top: 16rpx;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14rpx;
}

.city-grid-current {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.city-chip {
  min-height: 72rpx;
  border-radius: 14rpx;
  border: 1rpx solid #edf0f5;
  background: #f8fafc;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 16rpx;
  text-align: center;
}

.city-chip-active {
  background: rgba(37, 99, 235, 0.12);
  border-color: rgba(37, 99, 235, 0.32);
}

.city-chip-text {
  color: #4b5563;
  font-size: 26rpx;
  line-height: 34rpx;
  font-weight: 500;
}

.city-chip-text-active {
  color: #2563eb;
  font-weight: 700;
}

.letter-index {
  position: absolute;
  top: 8rpx;
  right: 10rpx;
  bottom: calc(24rpx + env(safe-area-inset-bottom));
  width: 32rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4rpx;
}

.letter-item {
  width: 28rpx;
  height: 28rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 999rpx;
}

.letter-item-hover {
  background: rgba(37, 99, 235, 0.1);
}

.letter-item-text {
  color: #2563eb;
  font-size: 18rpx;
  line-height: 1;
  font-weight: 700;
}

.empty-wrap {
  min-height: 260rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.empty-text {
  color: #94a3af;
  font-size: 24rpx;
}
 </style>
