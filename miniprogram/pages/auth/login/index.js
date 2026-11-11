/**
 * 登录页
 * 对应 uni 版 pages/auth/login/index.vue
 *
 * 策略：真接口优先 + 本地兜底
 *   - 已获得手机号授权 -> 走真实 loginByWechatMiniapp，网络不可达时回落本地数据
 *   - 未获得手机号授权（个人主体小程序拿不到 getPhoneNumber）-> 直接走本地通道，
 *     保证 P1 链路在开发者工具里始终可跑通
 */

import { loginByWechatMiniapp } from '../../../services/auth'
import { connectRealtimeSocket } from '../../../utils/realtime'
import { getMiniappLoginCode, getWechatDeviceId } from '../../../utils/wechat-auth'
import {
  loadLocationFilterCache,
  resolveCurrentCityByGps,
  saveCurrentCity,
  saveLocationFilterCache
} from '../../../utils/location'
import { syncUserLocation } from '../../../utils/location-sync'
import { setUser } from '../../../utils/store'
import { withFallback } from '../../../utils/fallback'
import { mockLoginResult } from '../../../utils/mock'

const INVITE_CODE_STORAGE_KEY = '__INVITE_CODE__'
const LOGIN_DISCOVER_REFRESH_STORAGE_KEY = 'discover_login_refresh_v1'
const LOGIN_PROFILE_REQUIRED_STORAGE_KEY = 'login_profile_required_v1'
const DEFAULT_CITY_NAME = '深圳'

const app = getApp()

Page({
  data: {
    statusBarHeight: 0,
    agreed: false,
    isLoading: false
  },

  onLoad(options) {
    const navBar = (app && app.globalData && app.globalData.navBar) || {}
    const queryInviteCode = String((options && (options.inviteCode || options.invite_code)) || '').trim()
    const cachedInviteCode = String(wx.getStorageSync(INVITE_CODE_STORAGE_KEY) || '').trim()
    const finalInviteCode = queryInviteCode || cachedInviteCode

    if (finalInviteCode) {
      wx.setStorageSync(INVITE_CODE_STORAGE_KEY, finalInviteCode)
    }

    this.inviteCode = finalInviteCode
    this.setData({ statusBarHeight: Number(navBar.statusBarHeight || 0) })
  },

  toggleAgreement() {
    this.setData({ agreed: !this.data.agreed })
  },

  openAgreement(event) {
    const type = event.currentTarget.dataset.type
    const url = type === 'user'
      ? '/pages/legal/user-agreement/index'
      : '/pages/legal/privacy-policy/index'

    wx.navigateTo({
      url,
      fail: () => {
        wx.showToast({ title: '协议页面将在后续批次提供', icon: 'none' })
      }
    })
  },

  handleSkipLogin() {
    if (this.data.isLoading) return
    const pages = getCurrentPages()
    if (pages.length > 1) {
      wx.navigateBack()
      return
    }
    wx.switchTab({ url: '/pages/discover/index' })
  },

  /** 依次尝试：缓存城市 -> GPS 反查（5 秒超时）-> 默认城市 */
  async resolveLoginCity() {
    const cache = loadLocationFilterCache() || {}
    const cachedCity = String(
      cache.currentCity || wx.getStorageSync('currentCity') || wx.getStorageSync('locationCity') || ''
    ).trim()

    try {
      const city = await Promise.race([
        resolveCurrentCityByGps(),
        new Promise((resolve) => setTimeout(() => resolve(''), 5000))
      ])
      const normalizedCity = String(city || '').trim()
      if (normalizedCity) {
        saveCurrentCity(normalizedCity)
        saveLocationFilterCache({
          mode: 'city',
          currentCity: normalizedCity,
          selectedCity: normalizedCity
        })
        return normalizedCity
      }
    } catch (err) {
      console.warn('登录前定位城市失败:', err)
    }

    return cachedCity || DEFAULT_CITY_NAME
  },

  async loginWithRealApi(phoneCode, cityName) {
    const code = await getMiniappLoginCode()
    return loginByWechatMiniapp({
      code,
      phone_code: phoneCode || undefined,
      device_id: getWechatDeviceId(),
      invite_code: this.inviteCode || undefined,
      city_name: cityName || undefined
    })
  },

  async handleWechatLogin(event) {
    if (this.data.isLoading) return

    if (!this.data.agreed) {
      wx.showToast({ title: '请先同意用户协议与隐私政策', icon: 'none', duration: 2000 })
      return
    }

    const detail = (event && event.detail) || {}
    const phoneCode = String(detail.code || '').trim()
    const phoneAuthorized = /getPhoneNumber:ok/.test(String(detail.errMsg || ''))

    this.setData({ isLoading: true })

    try {
      const cityName = await this.resolveLoginCity()
      let result = null

      if (phoneAuthorized && phoneCode) {
        result = await withFallback(
          () => this.loginWithRealApi(phoneCode, cityName),
          () => mockLoginResult({ city_name: cityName })
        )
      } else {
        wx.showToast({
          title: '未获取到手机号授权，已使用本地演示数据',
          icon: 'none',
          duration: 2000
        })
        result = mockLoginResult({ city_name: cityName })
      }

      const token = String((result && result.access_token) || '').trim()
      const userInfo = (result && result.user_info) || {}

      setUser(token, userInfo)
      wx.removeStorageSync(INVITE_CODE_STORAGE_KEY)

      try {
        connectRealtimeSocket()
      } catch (err) {
        console.warn('实时连接建立失败:', err)
      }

      if (result && result.is_new_user) {
        wx.setStorageSync(LOGIN_PROFILE_REQUIRED_STORAGE_KEY, true)
        wx.showToast({ title: '请先在「我的」完善个人资料', icon: 'none', duration: 2400 })
        setTimeout(() => {
          wx.switchTab({ url: '/pages/mine/index' })
        }, 600)
        return
      }

      syncUserLocation(true).catch((err) => {
        console.warn('登录后位置同步失败:', err)
      })

      wx.showToast({ title: '登录成功', icon: 'none', duration: 1200 })
      setTimeout(() => {
        wx.setStorageSync(LOGIN_DISCOVER_REFRESH_STORAGE_KEY, Date.now())
        wx.switchTab({ url: '/pages/discover/index' })
      }, 300)
    } catch (err) {
      const code = Number((err && err.code) || 0)
      if ([4267, 4272, 4273].indexOf(code) >= 0) {
        wx.showModal({
          title: '资料审核未通过',
          content: (err && err.message) || '头像或昵称不符合平台规范，请修改后重新提交',
          showCancel: false,
          confirmText: '去修改'
        })
      } else {
        wx.showToast({
          title: (err && err.message) || '登录失败，请稍后重试',
          icon: 'none',
          duration: 2000
        })
      }
    } finally {
      this.setData({ isLoading: false })
    }
  }
})
