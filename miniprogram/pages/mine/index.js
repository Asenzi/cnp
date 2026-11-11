import { MANAGEMENT_ITEMS } from './modules/menu'
import { getCurrentUserProfile } from '../../services/user'
import { getUnreadNotificationCount } from '../../services/notification'
import { getIncomeOverview } from '../../services/settlement'
import { connectRealtimeSocket, disconnectRealtimeSocket, subscribeRealtime } from '../../utils/realtime'
import { isLoggedIn, clearUser, setUser } from '../../utils/store'

const DEFAULT_AVATAR = 'https://cos.cnptec.site/static/logo.png'
const SERVICE_ITEMS = []
const SETTING_ITEMS = MANAGEMENT_ITEMS

function truthy(value) {
  if (typeof value === 'boolean') return value
  if (typeof value === 'number') return value === 1
  return ['1', 'true', 'yes', 'active'].includes(String(value || '').trim().toLowerCase())
}

function parseUser(raw) {
  if (typeof raw !== 'string') return raw && typeof raw === 'object' ? raw : {}
  try { return JSON.parse(raw) || {} } catch (error) { return {} }
}

function memberOpened(info = {}) {
  if ([info.is_member, info.member_opened, info.is_vip, info.vip_opened].some(truthy)) return true
  if (['active', 'opened', 'member', 'vip', 'paid'].includes(String(info.member_status || info.vip_status || '').trim().toLowerCase())) return true
  const expiry = info.member_expire_at || info.vip_expire_at
  const time = expiry ? new Date(String(expiry).replace(' ', 'T')).getTime() : 0
  return Number.isFinite(time) && time > Date.now()
}

function collectionCount(info = {}) {
  const parts = [info.network_interest_count, info.resource_interest_count, info.circle_interest_count]
  if (parts.every((value) => value !== undefined && value !== null && value !== '' && Number.isFinite(Number(value)))) {
    return String(parts.reduce((sum, value) => sum + Number(value), 0))
  }
  const value = Number(info.interest_count ?? info.interested_count ?? info.follow_favorite_count ?? info.favorite_count ?? info.collect_count)
  return Number.isFinite(value) && value >= 0 ? String(value) : '0'
}

Page({
  data: {
    statusBarHeight: 0, isLoggedIn: false, currentUser: {}, unreadMessageCount: 0,
    walletBalance: null, visibleServiceList: SERVICE_ITEMS, visibleSettingList: SETTING_ITEMS,
    displayAvatar: DEFAULT_AVATAR, displayName: '圈脉用户', displayUserId: '--',
    displayIntro: '一句话介绍你的行业、资源与合作方向，让更多合适的人脉主动找到你',
    isIntroEmpty: true, displayCircleCount: '--', displayCollectionCount: '0',
    displayWalletBalance: '--', unreadMessageCountText: '--', identityBadges: [],
    isMemberOpened: false, isCircleOwner: false
  },

  onLoad() {
    let statusBarHeight = 0
    try { statusBarHeight = Number(wx.getWindowInfo().statusBarHeight) || 0 } catch (error) {}
    this.setData({ statusBarHeight })
    this._realtimeHandler = (payload) => this.handleRealtimeEvent(payload)
    this._unsubscribeRealtime = subscribeRealtime(this._realtimeHandler)
  },

  onShow() {
    this.syncLoginState()
    if (this.data.isLoggedIn) {
      connectRealtimeSocket()
      this.refreshUserProfileFromServer()
      this.loadWalletBalance()
    } else {
      this.setData({ walletBalance: null, unreadMessageCount: 0 })
      this.syncDisplayFields()
    }
  },

  onUnload() {
    if (this._unsubscribeRealtime) this._unsubscribeRealtime()
  },

  syncLoginState() {
    const user = parseUser(wx.getStorageSync('userInfo'))
    const logged = isLoggedIn() || [true, 'true', 1, '1'].includes(wx.getStorageSync('isLoggedIn')) || Object.keys(user).length > 0
    this.setData({ isLoggedIn: logged, currentUser: logged ? user : {} }, () => this.syncDisplayFields())
  },

  syncDisplayFields() {
    const user = this.data.currentUser || {}
    const verified = truthy(user.is_verified) || truthy(user.real_name_verified) || Boolean(String(user.verified_real_name || '').trim())
    const member = memberOpened(user)
    const owner = truthy(user.is_circle_owner)
    const id = user.userId || user.user_id
    const badges = []
    if (verified) badges.push({ key: 'verified', icon: 'https://cos.cnptec.site/static/icon/certification.png' })
    if (member) badges.push({ key: 'member', icon: 'https://cos.cnptec.site/static/icon/mennber1.png' })
    if (owner) badges.push({ key: 'circle-owner', icon: 'https://cos.cnptec.site/static/icon/leader.png?v=20260623' })
    const services = SERVICE_ITEMS.filter((item) => item.key !== 'auth' || !verified)
    this.setData({
      displayAvatar: String(user.avatar_url || '').trim() || DEFAULT_AVATAR,
      displayName: String(user.nickname || '').trim() || '圈脉用户',
      displayUserId: id ? String(id) : '--',
      displayIntro: String(user.intro || '').trim() || '一句话介绍你的行业、资源与合作方向，让更多合适的人脉主动找到你',
      isIntroEmpty: !String(user.intro || '').trim(),
      displayCircleCount: typeof user.circle_count === 'number' ? String(user.circle_count) : '--',
      displayCollectionCount: collectionCount(user),
      displayWalletBalance: this.data.walletBalance === null ? '--' : `¥${Number(this.data.walletBalance).toFixed(2)}`,
      unreadMessageCountText: String(this.data.unreadMessageCount),
      identityBadges: badges, isMemberOpened: member, isCircleOwner: owner, visibleServiceList: services, memberExpiry: String(user.member_expire_at || user.vip_expire_at || '').slice(0, 10) || '未开通'
    })
  },

  copyUserId() { wx.setClipboardData({ data: this.data.displayUserId }) },
  onShareAppMessage() { return { title: this.data.displayName, path: '/pages/card/index?userId=' + this.data.displayUserId } },
  goPublish() { wx.switchTab({ url: '/pages/resources/index' }) },
  goEditInfo() { wx.showToast({ title: '资料编辑页面正在迁移', icon: 'none' }) },
  onIntroTap() { if (this.data.isIntroEmpty) this.goEditInfo() },
  goLogin() { wx.navigateTo({ url: '/pages/auth/login/index' }) },
  goMyCircles() { wx.showToast({ title: '我的圈子页面正在迁移', icon: 'none' }) },
  goMyFollowing() { wx.showToast({ title: '收藏列表页面正在迁移', icon: 'none' }) },
  goWallet() { wx.showToast({ title: '钱包页面正在迁移', icon: 'none' }) },
  goMessages() { wx.showToast({ title: '消息页面正在迁移', icon: 'none' }) },
  onOpenMember() { wx.showToast({ title: '会员中心页面正在迁移', icon: 'none' }) },

  onCircleOwnerAction() {
    if (!this.data.isLoggedIn) return this.onNeedLogin()
    if (this.data.isCircleOwner) wx.switchTab({ url: '/pages/circles/index' })
    else wx.showToast({ title: '圈主申请页面正在迁移', icon: 'none' })
  },

  onNeedLogin() { wx.showToast({ title: '请先登录', icon: 'none' }) },

  onServiceTap(event) {
    if (!this.data.isLoggedIn) return this.onNeedLogin()
    const key = event.currentTarget.dataset.key
    if (key === 'auth') {
      if (this.data.identityBadges.some((badge) => badge.key === 'verified')) {
        wx.showModal({ title: '实名认证', content: '您已经实名认证。', showCancel: false })
      } else wx.showToast({ title: '实名认证页面正在迁移', icon: 'none' })
    }
  },

  onLogout() {
    wx.showModal({
      title: '退出登录', content: '确定退出当前账号吗？', confirmText: '退出登录', cancelText: '取消', confirmColor: '#ef4444',
      success: (res) => {
        if (!res.confirm) return
        disconnectRealtimeSocket()
        clearUser()
        this.setData({ unreadMessageCount: 0, walletBalance: null }, () => this.syncLoginState())
        wx.showToast({ title: '已退出登录', icon: 'none' })
      }
    })
  },

  onSettingTap(event) {
    if (!this.data.isLoggedIn) return this.onNeedLogin()
    const key = event.currentTarget.dataset.key
    if (key === 'logout') return this.onLogout()
    if (key === 'circles') return this.goMyCircles()
    if (key === 'resources') return wx.switchTab({ url: '/pages/resources/index' })
    if (key === 'distribution') return this.goWallet()
    if (key === 'profile-card') {
      const id = this.data.displayUserId
      if (id !== '--') wx.navigateTo({ url: `/pages/card/index?userId=${encodeURIComponent(id)}` })
      else wx.showToast({ title: '暂时无法获取名片编号', icon: 'none' })
      return
    }
    const labels = { 'account-security': '账号管理', help: '帮助与反馈', about: '关于我们' }
    wx.showToast({ title: labels[key] || '设置', icon: 'none' })
  },

  async refreshUserProfileFromServer() {
    if (!wx.getStorageSync('token')) return
    try {
      const user = await getCurrentUserProfile()
      setUser(wx.getStorageSync('token'), user || {})
      this.setData({ currentUser: user || {}, isLoggedIn: true }, () => this.syncDisplayFields())
      this.loadUnreadMessageCount()
    } catch (err) {
      if (Number(err && err.statusCode) === 401) {
        disconnectRealtimeSocket()
        clearUser()
        this.setData({ isLoggedIn: false, currentUser: {}, walletBalance: null }, () => this.syncDisplayFields())
      }
    }
  },

  async loadUnreadMessageCount() {
    try {
      const data = await getUnreadNotificationCount()
      const count = Math.max(Number(data && (data.unread_count || data.count)) || 0, 0)
      this.setData({ unreadMessageCount: count }, () => this.syncDisplayFields())
    } catch (err) { this.setData({ unreadMessageCount: 0 }, () => this.syncDisplayFields()) }
  },

  async loadWalletBalance() {
    try {
      const data = await getIncomeOverview({ limit: 1 })
      const balance = Number(data && data.account && data.account.available_balance)
      this.setData({ walletBalance: Number.isFinite(balance) ? balance : null }, () => this.syncDisplayFields())
    } catch (err) { this.setData({ walletBalance: null }, () => this.syncDisplayFields()) }
  },

  handleRealtimeEvent(payload) {
    if (!payload || payload.event !== 'notification.changed') return
    const count = Number(payload.data && payload.data.unread_count)
    if (Number.isFinite(count) && count >= 0) this.setData({ unreadMessageCount: count }, () => this.syncDisplayFields())
    else this.loadUnreadMessageCount()
  }
})

