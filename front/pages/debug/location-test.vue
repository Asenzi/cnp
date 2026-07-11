<template>
  <view class="page">
    <view class="header">
      <text class="title">位置同步测试</text>
    </view>

    <view class="section">
      <text class="section-title">当前状态</text>
      <view class="info-row">
        <text class="label">登录状态:</text>
        <text class="value">{{ isLoggedIn ? '已登录' : '未登录' }}</text>
      </view>
      <view class="info-row">
        <text class="label">缓存位置:</text>
        <text class="value">{{ cachedLocationText }}</text>
      </view>
      <view class="info-row">
        <text class="label">缓存时间:</text>
        <text class="value">{{ cachedTimeText }}</text>
      </view>
    </view>

    <view class="section">
      <text class="section-title">最新位置</text>
      <view class="info-row">
        <text class="label">纬度:</text>
        <text class="value">{{ currentLatitude || '未获取' }}</text>
      </view>
      <view class="info-row">
        <text class="label">经度:</text>
        <text class="value">{{ currentLongitude || '未获取' }}</text>
      </view>
    </view>

    <view class="section">
      <text class="section-title">操作</text>
      <button class="test-btn" :disabled="loading" @tap="testGetLocation">
        {{ loading ? '获取中...' : '1. 测试获取位置' }}
      </button>
      <button class="test-btn" :disabled="loading || !isLoggedIn" @tap="testUploadLocation">
        {{ loading ? '上传中...' : '2. 测试上传位置' }}
      </button>
      <button class="test-btn" :disabled="loading || !isLoggedIn" @tap="testSmartSync">
        {{ loading ? '同步中...' : '3. 测试智能同步' }}
      </button>
      <button class="test-btn" @tap="clearCache">清除缓存</button>
    </view>

    <view class="section">
      <text class="section-title">日志</text>
      <scroll-view class="log-area" scroll-y>
        <text v-for="(log, index) in logs" :key="index" class="log-item">{{ log }}</text>
      </scroll-view>
    </view>
  </view>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getCurrentLocation, uploadUserLocation, smartSyncLocation, shouldUpdateLocation } from '../../utils/location-sync'

const isLoggedIn = ref(false)
const cachedLocation = ref(null)
const currentLatitude = ref('')
const currentLongitude = ref('')
const loading = ref(false)
const logs = ref([])

const addLog = (message) => {
  const time = new Date().toLocaleTimeString()
  logs.value.unshift(`[${time}] ${message}`)
  console.log(message)
}

const cachedLocationText = computed(() => {
  if (!cachedLocation.value) return '无'
  return `${cachedLocation.value.latitude.toFixed(6)}, ${cachedLocation.value.longitude.toFixed(6)}`
})

const cachedTimeText = computed(() => {
  if (!cachedLocation.value || !cachedLocation.value.updatedAt) return '无'
  const date = new Date(cachedLocation.value.updatedAt)
  const now = Date.now()
  const diff = Math.floor((now - cachedLocation.value.updatedAt) / 60000)
  return `${date.toLocaleString()} (${diff}分钟前)`
})

const loadStatus = () => {
  isLoggedIn.value = Boolean(uni.getStorageSync('token'))
  cachedLocation.value = uni.getStorageSync('userLocation') || null
  addLog(`登录状态: ${isLoggedIn.value ? '已登录' : '未登录'}`)
  if (cachedLocation.value) {
    addLog(`缓存位置: ${cachedLocationText.value}`)
  }
}

const testGetLocation = async () => {
  loading.value = true
  addLog('开始测试获取位置...')
  try {
    const location = await getCurrentLocation()
    currentLatitude.value = location.latitude.toFixed(7)
    currentLongitude.value = location.longitude.toFixed(7)
    addLog(`✅ 获取位置成功: ${currentLatitude.value}, ${currentLongitude.value}`)
  } catch (err) {
    addLog(`❌ 获取位置失败: ${err.errMsg || err.message || '未知错误'}`)
  } finally {
    loading.value = false
  }
}

const testUploadLocation = async () => {
  if (!currentLatitude.value || !currentLongitude.value) {
    addLog('❌ 请先获取位置')
    return
  }

  loading.value = true
  addLog('开始测试上传位置...')
  try {
    const success = await uploadUserLocation(
      parseFloat(currentLatitude.value),
      parseFloat(currentLongitude.value)
    )
    if (success) {
      addLog('✅ 上传位置成功')
    } else {
      addLog('❌ 上传位置失败')
    }
  } catch (err) {
    addLog(`❌ 上传位置失败: ${err.message || '未知错误'}`)
  } finally {
    loading.value = false
  }
}

const testSmartSync = async () => {
  loading.value = true
  addLog('开始测试智能同步...')
  addLog(`缓存检查: 需要更新=${shouldUpdateLocation()}`)
  try {
    const result = await smartSyncLocation(false)
    if (result) {
      addLog(`✅ 智能同步完成: ${result.latitude.toFixed(6)}, ${result.longitude.toFixed(6)}`)
      loadStatus()
    } else {
      addLog('ℹ️ 缓存仍有效，跳过同步')
    }
  } catch (err) {
    addLog(`❌ 智能同步失败: ${err.message || '未知错误'}`)
  } finally {
    loading.value = false
  }
}

const clearCache = () => {
  uni.removeStorageSync('userLocation')
  cachedLocation.value = null
  addLog('✅ 缓存已清除')
}

onMounted(() => {
  loadStatus()
})
</script>

<style scoped>
.page {
  min-height: 100vh;
  background: #f6f6f8;
  padding: 24rpx;
}

.header {
  padding: 32rpx 0;
  text-align: center;
}

.title {
  font-size: 40rpx;
  font-weight: 600;
  color: #1e293b;
}

.section {
  background: #ffffff;
  border-radius: 16rpx;
  padding: 32rpx;
  margin-bottom: 24rpx;
}

.section-title {
  display: block;
  font-size: 28rpx;
  font-weight: 600;
  color: #334155;
  margin-bottom: 24rpx;
}

.info-row {
  display: flex;
  justify-content: space-between;
  padding: 16rpx 0;
  border-bottom: 1rpx solid #f1f5f9;
}

.info-row:last-child {
  border-bottom: none;
}

.label {
  font-size: 26rpx;
  color: #64748b;
}

.value {
  font-size: 26rpx;
  color: #1e293b;
  font-weight: 500;
}

.test-btn {
  width: 100%;
  height: 88rpx;
  background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%);
  border-radius: 12rpx;
  border: none;
  color: #ffffff;
  font-size: 28rpx;
  font-weight: 600;
  margin-bottom: 16rpx;
}

.test-btn:last-child {
  background: linear-gradient(135deg, #64748b 0%, #475569 100%);
  margin-bottom: 0;
}

.test-btn[disabled] {
  opacity: 0.6;
}

.test-btn::after {
  border: none;
}

.log-area {
  height: 500rpx;
  background: #0f172a;
  border-radius: 12rpx;
  padding: 20rpx;
}

.log-item {
  display: block;
  font-size: 22rpx;
  line-height: 36rpx;
  color: #94a3b8;
  font-family: 'Courier New', monospace;
  margin-bottom: 8rpx;
}
</style>
