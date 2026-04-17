const QQ_MAP_KEY_STORAGE_KEYS = ['__QQ_MAP_KEY__', 'QQ_MAP_KEY', 'qqMapKey', 'qq_map_key']
const QQ_MAP_KEY_ENV_KEYS = ['VUE_APP_QQ_MAP_KEY', 'UNI_APP_QQ_MAP_KEY', 'QQ_MAP_KEY']
const QQ_GEOCODER_URL = 'https://apis.map.qq.com/ws/geocoder/v1/'
const LOCATION_FILTER_CACHE_KEY = 'discover_location_filter_v1'
const CURRENT_CITY_CACHE_KEYS = ['currentCity', 'locationCity']

function getProcessEnv() {
  if (typeof process !== 'undefined' && process && process.env) {
    return process.env
  }
  return {}
}

function resolveQqMapKeyInfo() {
  for (const storageName of QQ_MAP_KEY_STORAGE_KEYS) {
    const storageKey = String(uni.getStorageSync(storageName) || '').trim()
    if (storageKey) {
      return {
        key: storageKey,
        source: 'storage',
        sourceKey: storageName
      }
    }
  }

  const env = getProcessEnv()
  const envEntries = [
    ['VUE_APP_QQ_MAP_KEY', env.VUE_APP_QQ_MAP_KEY],
    ['UNI_APP_QQ_MAP_KEY', env.UNI_APP_QQ_MAP_KEY],
    ['QQ_MAP_KEY', env.QQ_MAP_KEY]
  ]
  for (const [key, rawValue] of envEntries) {
    const value = String(rawValue || '').trim()
    if (value) {
      return {
        key: value,
        source: 'env',
        sourceKey: key
      }
    }
  }

  return {
    key: '',
    source: 'none',
    sourceKey: ''
  }
}

function resolveQqMapKey() {
  return resolveQqMapKeyInfo().key
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

async function reverseGeocodeByQqMap(latitude, longitude, key) {
  const res = await requestPromise({
    url: QQ_GEOCODER_URL,
    method: 'GET',
    data: {
      key,
      location: `${latitude},${longitude}`,
      get_poi: 0
    }
  })

  const payload = res?.data || {}
  if (res?.statusCode !== 200 || Number(payload?.status) !== 0) {
    const status = Number(payload?.status)
    const error = new Error(payload?.message || 'reverse geocode failed')
    error.code = status === 190 ? 'QQ_MAP_KEY_INVALID' : 'QQ_MAP_GEOCODER_FAILED'
    error.tencentStatus = Number.isFinite(status) ? status : 0
    error.tencentMessage = String(payload?.message || '').trim()
    error.requestId = String(payload?.request_id || '').trim()
    throw error
  }

  const city = String(payload?.result?.address_component?.city || '').trim()
  if (!city) {
    throw new Error('city not found')
  }

  return city.replace(/\u5e02$/, '')
}

export async function resolveCurrentCityByGps() {
  const location = await getLocationPromise()
  const latitude = Number(location?.latitude)
  const longitude = Number(location?.longitude)
  if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) {
    throw new Error('invalid coordinates')
  }

  const qqMapKey = resolveQqMapKey()
  if (!qqMapKey) {
    const keyError = new Error('QQ_MAP_KEY_MISSING')
    keyError.code = 'QQ_MAP_KEY_MISSING'
    throw keyError
  }

  return reverseGeocodeByQqMap(latitude, longitude, qqMapKey)
}

export function getQqMapKeyInfo() {
  const info = resolveQqMapKeyInfo()
  return {
    key: info.key,
    source: info.source,
    sourceKey: info.sourceKey
  }
}

export function getLocationErrorMessage(error) {
  const message = String(error?.message || error?.errMsg || '').toLowerCase()
  const tencentMessage = String(error?.tencentMessage || '').toLowerCase()

  if (error?.code === 'QQ_MAP_KEY_MISSING') {
    return '\u672a\u914d\u7f6e\u5730\u56fe Key\uff0c\u5df2\u4f7f\u7528\u9ed8\u8ba4\u57ce\u5e02'
  }
  if (error?.code === 'QQ_MAP_KEY_INVALID' || error?.tencentStatus === 190 || tencentMessage.includes('\u65e0\u6548\u7684key')) {
    return '\u817e\u8baf\u5730\u56fe Key \u65e0\u6548\uff0c\u8bf7\u66f4\u65b0\u4e3a\u6709\u6548\u7684 WebService API Key'
  }
  if (error?.tencentStatus === 199 || tencentMessage.includes('webserviceapi') || tencentMessage.includes('\u672a\u5f00\u901a')) {
    return '\u817e\u8baf\u5730\u56fe Key \u672a\u5f00\u901a WebService API\uff0c\u8bf7\u5728\u63a7\u5236\u53f0\u542f\u7528\u5bf9\u5e94\u80fd\u529b'
  }
  if (message.includes('auth deny') || message.includes('permission')) {
    return '\u5b9a\u4f4d\u6743\u9650\u672a\u5f00\u542f\uff0c\u8bf7\u5728\u8bbe\u7f6e\u4e2d\u5141\u8bb8\u5b9a\u4f4d'
  }
  if (message.includes('fail') || message.includes('timeout')) {
    return '\u5b9a\u4f4d\u5931\u8d25\uff0c\u8bf7\u7a0d\u540e\u91cd\u8bd5'
  }
  return '\u5b9a\u4f4d\u5931\u8d25\uff0c\u5df2\u4f7f\u7528\u9ed8\u8ba4\u57ce\u5e02'
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
