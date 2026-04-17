<template>
  <view class="page">
    <text class="title">Debug</text>

    <view class="card">
      <text class="row">{{ uiText.currentTimeLabel }}{{ currentTime }}</text>
      <text class="row">{{ uiText.currentRouteLabel }}{{ currentRoute }}</text>
      <text class="row">{{ uiText.currentApiLabel }}{{ currentApiBaseUrl }}</text>
      <text class="row">{{ uiText.suggestedApiLabel }}{{ suggestedApiBaseUrl }}</text>
    </view>

    <view class="card">
      <text class="section-title">{{ uiText.locationSection }}</text>
      <text class="row">{{ uiText.locationKeySourceLabel }}{{ locationKeySource }}</text>
      <text class="row">{{ uiText.locationKeyVarLabel }}{{ locationKeySourceKey }}</text>
      <text class="row">{{ uiText.locationKeyPreviewLabel }}{{ maskedLocationKey }}</text>
      <input
        v-model.trim="locationKeyInput"
        class="base-url-input location-key-input"
        type="text"
        :placeholder="uiText.locationKeyInputPlaceholder"
      />
      <text class="row">{{ uiText.cachedCityLabel }}{{ cachedCityText }}</text>
      <text class="row">{{ uiText.currentCityLabel }}{{ currentCityText }}</text>
      <text class="row">{{ uiText.tencentStatusLabel }}{{ locationStatusText }}</text>
      <text class="row">{{ uiText.tencentMessageLabel }}{{ locationMessageText }}</text>
      <text class="row">{{ uiText.requestIdLabel }}{{ locationRequestIdText }}</text>
      <view class="actions">
        <button class="action-btn primary" @tap="onSaveLocationKey">{{ uiText.saveKeyButton }}</button>
        <button class="action-btn primary" @tap="onRunLocationDiagnosis">{{ uiText.runDiagnosisButton }}</button>
        <button class="action-btn" @tap="onClearLocationKeyCache">{{ uiText.clearKeyButton }}</button>
        <button class="action-btn" @tap="onClearLocationCityCache">{{ uiText.clearCityButton }}</button>
      </view>
    </view>

    <view class="card">
      <text class="section-title">{{ uiText.apiSection }}</text>
      <input
        v-model.trim="apiBaseUrlInput"
        class="base-url-input"
        type="text"
        :placeholder="uiText.apiInputPlaceholder"
      />
      <view class="actions">
        <button class="action-btn primary" @tap="onApplyApiBaseUrl">{{ uiText.applyApiButton }}</button>
        <button class="action-btn" @tap="onUseSuggestedApiBaseUrl">{{ uiText.useSuggestedApiButton }}</button>
        <button class="action-btn" @tap="onClearApiBaseUrl">{{ uiText.clearApiButton }}</button>
      </view>
    </view>

    <view class="card">
      <text class="section-title">{{ uiText.querySection }}</text>
      <view v-if="queryEntries.length > 0">
        <view class="query-item" v-for="[key, value] in queryEntries" :key="key">
          <text>{{ key }} = {{ value }}</text>
        </view>
      </view>
      <text v-else>{{ uiText.noQuery }}</text>
    </view>

    <button class="back-btn" type="default" @tap="goBack">{{ uiText.backButton }}</button>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onLoad, onShow, onUnload } from '@dcloudio/uni-app'
import { clearApiBaseUrl, getApiBaseUrl, getSuggestedApiBaseUrl, setApiBaseUrl } from '../../utils/request'
import {
  clearLocationSessionCache,
  getLocationErrorMessage,
  getQqMapKeyInfo,
  loadLocationFilterCache,
  resolveCurrentCityByGps
} from '../tab/discover/modules/location'

const uiText = {
  currentTimeLabel: '\u5f53\u524d\u65f6\u95f4\uff1a',
  currentRouteLabel: '\u5f53\u524d\u8def\u7531\uff1a',
  currentApiLabel: '\u5f53\u524d API\uff1a',
  suggestedApiLabel: '\u5efa\u8bae\u5c40\u57df\u7f51\u5730\u5740\uff1a',
  locationSection: '\u5b9a\u4f4d\u8bca\u65ad',
  locationKeySourceLabel: '\u5730\u56fe Key \u6765\u6e90\uff1a',
  locationKeyVarLabel: '\u5730\u56fe Key \u53d8\u91cf\uff1a',
  locationKeyPreviewLabel: '\u5730\u56fe Key \u9884\u89c8\uff1a',
  locationKeyInputPlaceholder: '\u624b\u52a8\u8f93\u5165\u817e\u8baf\u5730\u56fe WebService Key',
  cachedCityLabel: '\u5f53\u524d\u57ce\u5e02\u7f13\u5b58\uff1a',
  currentCityLabel: '\u5f53\u524d\u5b9a\u4f4d\u7ed3\u679c\uff1a',
  tencentStatusLabel: '\u817e\u8baf\u56de\u5305\uff1a',
  tencentMessageLabel: '\u56de\u5305\u8bf4\u660e\uff1a',
  requestIdLabel: '\u8bf7\u6c42 ID\uff1a',
  saveKeyButton: '\u4fdd\u5b58\u5730\u56fe Key',
  runDiagnosisButton: '\u8fd0\u884c\u5b9a\u4f4d\u8bca\u65ad',
  clearKeyButton: '\u6e05\u9664\u5730\u56fe Key \u7f13\u5b58',
  clearCityButton: '\u6e05\u9664\u57ce\u5e02\u548c\u5b9a\u4f4d\u7f13\u5b58',
  apiSection: '\u63a5\u53e3\u5730\u5740',
  apiInputPlaceholder: '\u8bf7\u8f93\u5165 API \u57fa\u5730\u5740\uff0c\u4f8b\u5982\uff1ahttp://172.20.10.3:8001',
  applyApiButton: '\u5e94\u7528\u5730\u5740',
  useSuggestedApiButton: '\u4f7f\u7528\u5efa\u8bae\u5730\u5740',
  clearApiButton: '\u6e05\u9664\u8986\u76d6',
  querySection: 'Query \u53c2\u6570',
  noQuery: '\u65e0 query \u53c2\u6570',
  backButton: '\u8fd4\u56de',
  running: '\u8bca\u65ad\u4e2d...',
  ok: '\u5b9a\u4f4d\u6210\u529f',
  inputMissing: '\u8bf7\u8f93\u5165\u5730\u56fe Key',
  keySaved: '\u5730\u56fe Key \u5df2\u4fdd\u5b58\u5230\u672c\u5730\u7f13\u5b58',
  apiUpdated: '\u63a5\u53e3\u5730\u5740\u5df2\u66f4\u65b0',
  apiSwitched: '\u5df2\u5207\u6362\u5230\u5efa\u8bae\u5730\u5740',
  apiCleared: '\u5df2\u6e05\u9664\u8986\u76d6\u5730\u5740',
  keyCleared: '\u5df2\u6e05\u9664\u5730\u56fe Key \u7f13\u5b58',
  cacheCleared: '\u5df2\u6e05\u9664\u57ce\u5e02\u548c\u5b9a\u4f4d\u7f13\u5b58',
  diagnoseSuccess: '\u5b9a\u4f4d\u6210\u529f'
}

const currentTime = ref('')
const currentRoute = ref('')
const currentApiBaseUrl = ref('')
const apiBaseUrlInput = ref('')
const query = ref({})

const locationKeySource = ref('-')
const locationKeySourceKey = ref('-')
const maskedLocationKey = ref('-')
const locationKeyInput = ref('')

const cachedCityText = ref('-')
const currentCityText = ref('-')
const locationStatusText = ref('-')
const locationMessageText = ref('-')
const locationRequestIdText = ref('-')

let timer = null

const queryEntries = computed(() => Object.entries(query.value))
const suggestedApiBaseUrl = computed(() => String(getSuggestedApiBaseUrl() || '').trim())

const pad = (value) => String(value).padStart(2, '0')

const formatTime = () => {
  const now = new Date()
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())} ${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`
}

const showToast = (title) => {
  uni.showToast({
    title,
    icon: 'none'
  })
}

const maskSecret = (value) => {
  const text = String(value || '').trim()
  if (!text) {
    return '-'
  }
  if (text.length <= 8) {
    return `${text.slice(0, 2)}****${text.slice(-2)}`
  }
  return `${text.slice(0, 4)}****${text.slice(-4)}`
}

const refreshLocationCacheView = () => {
  const sessionCache = loadLocationFilterCache()
  cachedCityText.value = String(
    sessionCache.currentCity
      || uni.getStorageSync('currentCity')
      || uni.getStorageSync('locationCity')
      || ''
  ).trim() || '-'
}

const refreshApiBaseUrl = () => {
  const current = String(getApiBaseUrl() || '').trim()
  currentApiBaseUrl.value = current
  if (!String(apiBaseUrlInput.value || '').trim()) {
    apiBaseUrlInput.value = current
  }
}

const updateTime = () => {
  currentTime.value = formatTime()
}

const updateRoute = () => {
  const pages = getCurrentPages()
  const current = pages[pages.length - 1]
  currentRoute.value = current ? `/${current.route}` : '-'
}

const goBack = () => {
  uni.navigateBack({
    delta: 1
  })
}

const refreshLocationKeyView = () => {
  const info = getQqMapKeyInfo()
  locationKeySource.value = info.source
  locationKeySourceKey.value = info.sourceKey || '-'
  maskedLocationKey.value = maskSecret(info.key)
  if (!String(locationKeyInput.value || '').trim()) {
    locationKeyInput.value = info.key || ''
  }
}

const onSaveLocationKey = () => {
  const value = String(locationKeyInput.value || '').trim()
  if (!value) {
    showToast(uiText.inputMissing)
    return
  }
  uni.setStorageSync('__QQ_MAP_KEY__', value)
  refreshLocationKeyView()
  showToast(uiText.keySaved)
}

const onRunLocationDiagnosis = async () => {
  refreshLocationKeyView()
  refreshLocationCacheView()
  locationStatusText.value = uiText.running
  locationMessageText.value = uiText.running
  locationRequestIdText.value = '-'

  try {
    const city = await resolveCurrentCityByGps()
    currentCityText.value = city || '-'
    locationStatusText.value = 'ok'
    locationMessageText.value = uiText.diagnoseSuccess
  } catch (error) {
    currentCityText.value = '-'
    locationStatusText.value = String(error?.tencentStatus || error?.code || 'error')
    locationMessageText.value = getLocationErrorMessage(error)
    locationRequestIdText.value = String(error?.requestId || '').trim() || '-'
  }
}

const onClearLocationKeyCache = () => {
  uni.removeStorageSync('__QQ_MAP_KEY__')
  uni.removeStorageSync('QQ_MAP_KEY')
  uni.removeStorageSync('qqMapKey')
  uni.removeStorageSync('qq_map_key')
  locationKeyInput.value = ''
  refreshLocationKeyView()
  showToast(uiText.keyCleared)
}

const onClearLocationCityCache = () => {
  clearLocationSessionCache()
  refreshLocationCacheView()
  showToast(uiText.cacheCleared)
}

const onApplyApiBaseUrl = () => {
  const value = String(apiBaseUrlInput.value || '').trim()
  if (!value) {
    showToast('\u8bf7\u8f93\u5165\u63a5\u53e3\u5730\u5740')
    return
  }
  setApiBaseUrl(value)
  refreshApiBaseUrl()
  showToast(uiText.apiUpdated)
}

const onUseSuggestedApiBaseUrl = () => {
  const suggested = String(getSuggestedApiBaseUrl() || '').trim()
  apiBaseUrlInput.value = suggested
  setApiBaseUrl(suggested)
  refreshApiBaseUrl()
  showToast(uiText.apiSwitched)
}

const onClearApiBaseUrl = () => {
  clearApiBaseUrl()
  apiBaseUrlInput.value = getApiBaseUrl()
  refreshApiBaseUrl()
  showToast(uiText.apiCleared)
}

onLoad((options) => {
  query.value = options || {}
  updateTime()
  updateRoute()
  refreshApiBaseUrl()
  refreshLocationKeyView()
  refreshLocationCacheView()
  timer = setInterval(updateTime, 1000)
})

onShow(() => {
  updateRoute()
  refreshApiBaseUrl()
  refreshLocationKeyView()
  refreshLocationCacheView()
})

onUnload(() => {
  if (timer) {
    clearInterval(timer)
    timer = null
  }
})
</script>

<style scoped>
.page {
  padding: 32rpx;
}

.title {
  display: block;
  font-size: 46rpx;
  font-weight: 700;
  margin-bottom: 20rpx;
}

.card {
  background-color: #f6f7f9;
  border-radius: 16rpx;
  padding: 24rpx;
  margin-bottom: 20rpx;
}

.row {
  display: block;
  font-size: 28rpx;
  line-height: 40rpx;
  margin-bottom: 8rpx;
  word-break: break-all;
}

.section-title {
  display: block;
  font-size: 30rpx;
  line-height: 40rpx;
  font-weight: 600;
  margin-bottom: 14rpx;
}

.base-url-input {
  width: 100%;
  min-height: 88rpx;
  box-sizing: border-box;
  padding: 0 24rpx;
  border-radius: 14rpx;
  background: #ffffff;
  border: 1rpx solid #dbe3f0;
  font-size: 28rpx;
  color: #111827;
}

.location-key-input {
  margin: 12rpx 0 14rpx;
}

.actions {
  margin-top: 16rpx;
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.action-btn {
  margin: 0;
}

.primary {
  color: #ffffff;
  background: #1d4ed8;
}

.query-item {
  font-size: 26rpx;
  margin-bottom: 8rpx;
  word-break: break-all;
}

.back-btn {
  margin-top: 8rpx;
}
</style>
