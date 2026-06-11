import { getApiBaseUrl } from '@/utils/request.js'

const LOCATION_FILTER_CACHE_KEY = 'discover_location_filter_v1'
const CURRENT_CITY_CACHE_KEYS = ['currentCity', 'locationCity']

// 使用后端代理API进行逆地理编码
async function reverseGeocodeByBackend(latitude, longitude) {
  const baseURL = getApiBaseUrl()
  const token = uni.getStorageSync('token')

  const res = await requestPromise({
    url: `${baseURL}/api/v1/map/reverse-geocode`,
    method: 'GET',
    header: {
      'Authorization': token ? `Bearer ${token}` : ''
    },
    data: {
      latitude,
      longitude
    }
  })

  const payload = res?.data || {}
  // 后端返回格式: { code: 0, message: "success", data: { city: "深圳", ... } }
  if (res?.statusCode !== 200 || payload?.code !== 0) {
    const error = new Error(payload?.message || 'reverse geocode failed')
    error.code = 'REVERSE_GEOCODE_FAILED'
    throw error
  }

  const city = String(payload?.data?.city || '').trim()
  if (!city) {
    throw new Error('city not found')
  }

  return city
}

function requestPromise(options) {
  return new Promise((resolve, reject) => {
    uni.request({
      ...options,
      success: (res) => resolve(res),
      fail: (err) => reject(err)
    })
  })
}

function getLocationPromise() {
  return new Promise((resolve, reject) => {
    uni.getLocation({
      type: 'gcj02',
      isHighAccuracy: true,
      highAccuracyExpireTime: 3000,
      success: (res) => resolve(res),
      fail: (err) => reject(err)
    })
  })
}

export async function resolveCurrentCityByGps() {
  const location = await getLocationPromise()
  const latitude = Number(location?.latitude)
  const longitude = Number(location?.longitude)
  if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) {
    throw new Error('invalid coordinates')
  }

  // 使用后端代理API
  return reverseGeocodeByBackend(latitude, longitude)
}

export function getQqMapKeyInfo() {
  // 现在通过后端代理,不再需要前端Key
  return {
    key: '(使用后端代理)',
    source: 'backend',
    sourceKey: 'backend_proxy'
  }
}

export function getLocationErrorMessage(error) {
  const message = String(error?.message || error?.errMsg || '').toLowerCase()

  if (message.includes('auth deny') || message.includes('permission')) {
    return '定位权限未开启,请在设置中允许定位'
  }
  if (message.includes('fail') || message.includes('timeout')) {
    return '定位失败,请稍后重试'
  }
  return '定位失败,已使用默认城市'
}

export function saveCurrentCity(city) {
  const normalized = String(city || '').trim()
  if (!normalized) {
    return
  }
  for (const key of CURRENT_CITY_CACHE_KEYS) {
    uni.setStorageSync(key, normalized)
  }
}

export function saveLocationFilterCache(payload = {}) {
  const mode = String(payload?.mode || '').trim() === 'national' ? 'national' : 'city'
  const currentCity = String(payload?.currentCity || '').trim()
  const selectedCity = String(payload?.selectedCity || '').trim()
  uni.setStorageSync(LOCATION_FILTER_CACHE_KEY, {
    mode,
    currentCity,
    selectedCity
  })
}

export function loadLocationFilterCache() {
  try {
    const raw = uni.getStorageSync(LOCATION_FILTER_CACHE_KEY)
    if (!raw) {
      return {
        mode: 'city',
        currentCity: '',
        selectedCity: ''
      }
    }
    const parsed = typeof raw === 'string' ? JSON.parse(raw) : raw
    if (!parsed || typeof parsed !== 'object') {
      return {
        mode: 'city',
        currentCity: '',
        selectedCity: ''
      }
    }
    return {
      mode: String(parsed.mode || '').trim() === 'national' ? 'national' : 'city',
      currentCity: String(parsed.currentCity || '').trim(),
      selectedCity: String(parsed.selectedCity || '').trim()
    }
  } catch {
    return {
      mode: 'city',
      currentCity: '',
      selectedCity: ''
    }
  }
}

export function clearLocationSessionCache() {
  for (const key of CURRENT_CITY_CACHE_KEYS) {
    uni.removeStorageSync(key)
  }
  uni.removeStorageSync(LOCATION_FILTER_CACHE_KEY)
}
