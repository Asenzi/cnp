/**
 * 位置同步工具 - 自动获取并上传用户经纬度
 */

import { updateCurrentUserProfile } from '../api/user'
import { getApiBaseUrl } from './request'

const DEFAULT_CITY_NAME = '深圳'

const reverseGeocodeCity = (latitude, longitude) => {
  return new Promise((resolve) => {
    uni.request({
      url: `${getApiBaseUrl()}/api/v1/map/reverse-geocode`,
      method: 'GET',
      data: {
        latitude,
        longitude
      },
      success: (res) => {
        const payload = res?.data || {}
        const city = String(payload?.data?.city || '').trim()
        resolve(city)
      },
      fail: () => resolve('')
    })
  })
}

/**
 * 获取用户当前位置
 */
export const getCurrentLocation = () => {
  return new Promise((resolve, reject) => {
    console.log('[位置同步] 开始获取用户位置...')
    uni.getLocation({
      type: 'gcj02',
      success: (res) => {
        console.log('[位置同步] 位置获取成功:', { latitude: res.latitude, longitude: res.longitude })
        resolve({
          latitude: res.latitude,
          longitude: res.longitude
        })
      },
      fail: (err) => {
        console.error('[位置同步] 获取位置失败:', err)
        reject(err)
      }
    })
  })
}

/**
 * 上传用户位置到服务器
 */
export const uploadUserLocation = async (latitude, longitude, cityName = '') => {
  try {
    const normalizedCityName = String(cityName || '').trim()
    console.log('[位置同步] 开始上传位置到服务器:', { latitude, longitude, cityName: normalizedCityName })
    const payload = {
      latitude,
      longitude
    }
    if (normalizedCityName) {
      payload.city_name = normalizedCityName
    }
    const result = await updateCurrentUserProfile(payload)
    const cachedUserInfo = uni.getStorageSync('userInfo') || {}
    uni.setStorageSync('userInfo', {
      ...cachedUserInfo,
      ...(result || {}),
      latitude,
      longitude,
      ...(normalizedCityName ? { city_name: normalizedCityName } : {})
    })
    console.log('[位置同步] 位置上传成功:', result)
    return true
  } catch (err) {
    console.error('[位置同步] 位置上传失败:', err)
    return false
  }
}

/**
 * 获取并同步用户位置
 * @param {boolean} silent - 是否静默执行（不显示错误提示）
 */
export const syncUserLocation = async (silent = true) => {
  console.log('[位置同步] 开始同步用户位置，静默模式:', silent)

  try {
    const location = await getCurrentLocation()
    const cityName = await reverseGeocodeCity(location.latitude, location.longitude) || DEFAULT_CITY_NAME
    if (cityName) {
      uni.setStorageSync('currentCity', cityName)
      uni.setStorageSync('locationCity', cityName)
    }
    const uploadSuccess = await uploadUserLocation(location.latitude, location.longitude, cityName)

    if (!uploadSuccess) {
      throw new Error('位置上传失败')
    }

    // 缓存位置信息到本地
    uni.setStorageSync('userLocation', {
      latitude: location.latitude,
      longitude: location.longitude,
      cityName,
      updatedAt: Date.now()
    })

    console.log('[位置同步] 位置同步完成并已缓存')
    return location
  } catch (err) {
    console.error('[位置同步] 同步失败:', err)
    if (!silent) {
      uni.showToast({
        title: '位置获取失败',
        icon: 'none'
      })
    }
    throw err
  }
}

/**
 * 检查位置是否需要更新
 * 移除缓存机制 - 每次都需要更新
 */
export const shouldUpdateLocation = () => {
  console.log('[位置同步] 检查更新策略: 每次都需要更新位置')
  return true // 总是返回 true，每次都更新
}

/**
 * 智能同步位置 - 每次都强制更新
 */
export const smartSyncLocation = async (silent = true) => {
  console.log('[位置同步] 开始同步位置（每次都更新）')
  return await syncUserLocation(silent)
}
