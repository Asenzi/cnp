/**
 * 个人名片详情页
 * 对应 uni 版 pages/me/card/index.vue（原版 1291 行 + 7 个组件）
 *
 * P1 垂直切片最后一环。还原英雄区 / 统计 / 个人介绍 / 圈子 / 底部操作，
 * 动态流与联系方式解锁留到后续批次。
 */

import { getUserProfileById } from '../../services/user'
import { toggleUserFollow } from '../../services/network'
import { resolveProfileHomeData } from '../../utils/profile-detail'
import { withFallback } from '../../utils/fallback'
import { mockProfile, mockFollowResult } from '../../utils/mock'
import { isLoggedIn } from '../../utils/store'

const PENDING_FOLLOW_STORAGE_KEY = 'pendingFollowUserId'

Page({
  data: {
    userId: '',
    loading: true,
    loadError: '',
    profile: null,
    followPending: false,
    isSelf: false
  },

  onLoad(options) {
    const userId = String((options && options.userId) || '').trim()
    if (!userId) {
      this.setData({ loading: false, loadError: '缺少用户标识' })
      return
    }
    this.setData({ userId })
    this.loadProfile(userId)
  },

  async loadProfile(userId) {
    this.setData({ loading: true, loadError: '' })

    try {
      const raw = await withFallback(
        () => getUserProfileById(userId),
        () => mockProfile(userId),
        { silent: true }
      )

      const profile = resolveProfileHomeData(raw || {}, {})
      const mine = this._resolveSelfId()
      const isSelf = Boolean(mine) && mine === String(profile.userId || '').trim()

      this.setData({ profile, isSelf, loading: false })

      // 未登录时点过关注，登录后回来自动补上
      const pending = String(wx.getStorageSync(PENDING_FOLLOW_STORAGE_KEY) || '').trim()
      if (pending && pending === userId && isLoggedIn()) {
        wx.removeStorageSync(PENDING_FOLLOW_STORAGE_KEY)
        this.toggleFollow(true)
      }
    } catch (err) {
      this.setData({
        loading: false,
        loadError: String((err && err.message) || '加载失败，请稍后重试')
      })
    }
  },

  _resolveSelfId() {
    try {
      const raw = wx.getStorageSync('userInfo')
      const info = typeof raw === 'string' ? JSON.parse(raw) : raw
      if (!info || typeof info !== 'object') return ''
      return String(info.user_id || info.userId || info.id || '').trim()
    } catch (err) {
      return ''
    }
  },

  onRetry() {
    if (this.data.userId) {
      this.loadProfile(this.data.userId)
    }
  },

  async onToggleFollow() {
    if (this.data.followPending) return

    const target = String(this.data.userId || '').trim()
    if (!target) return

    if (!isLoggedIn()) {
      wx.setStorageSync(PENDING_FOLLOW_STORAGE_KEY, target)
      wx.showToast({ title: '请先登录', icon: 'none' })
      setTimeout(() => {
        wx.navigateTo({ url: '/pages/auth/login/index' })
      }, 600)
      return
    }

    const willFollow = !this.data.profile.followed
    this.setData({ followPending: true })

    try {
      const result = await withFallback(
        () => toggleUserFollow(target, willFollow),
        () => mockFollowResult(willFollow),
        { silent: true }
      )
      const nextFollowed = result && typeof result.is_followed === 'boolean'
        ? result.is_followed
        : willFollow

      this.setData({ 'profile.followed': nextFollowed })
      wx.showToast({ title: nextFollowed ? '关注成功' : '已取消关注', icon: 'none' })
    } catch (err) {
      wx.showToast({ title: '操作失败，请稍后重试', icon: 'none' })
    } finally {
      this.setData({ followPending: false })
    }
  },

  onSendMessage() {
    wx.showToast({ title: '消息会话将在后续批次接入', icon: 'none' })
  }
})
