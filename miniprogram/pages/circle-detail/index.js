/**
 * 圈子详情页
 * 对应 uni 版 pages/circles/detail/index.vue（原版 719 行 + 6 个组件）
 *
 * 与原版的差异：
 *   - 付费入圈的微信虚拟支付（requestVirtualPayment）依赖类目资质，
 *     本批次不迁移：免费圈走真实提交，付费圈提示待接入。
 *   - 成员点击跳已迁移的 /pages/card/index；活动点击跳资源详情，
 *     该页尚未迁移，用 toast 占位。
 */

import {
  getCircleDetail,
  getCircleMembers,
  getCirclePosts,
  submitCircleJoinRequest,
  toggleCircleCollection
} from '../../services/circle'
import {
  buildCircleDetail,
  emptyCircleDetail,
  mapCircleMember,
  mapJoinAction
} from '../../utils/circle-detail'
import { mapResourcePostItem } from '../../utils/resource-card'
import { withFallback } from '../../utils/fallback'
import { mockCircleDetail, mockCircleMembers, mockCirclePosts } from '../../utils/mock'
import { publishCircleInterestChange } from '../../utils/circle-interest'

const UI_TEXT = {
  loading: '加载中...',
  loadFailed: '圈子详情加载失败',
  membersFailed: '成员列表加载失败',
  postsFailed: '圈子动态加载失败',
  loginFirst: '请先登录',
  missingCode: '圈子编号缺失',
  missingUser: '用户信息缺失',
  missingPost: '活动编号缺失',
  collected: '已收藏',
  uncollected: '已取消收藏',
  operationFailed: '操作失败，请稍后重试',
  applySubmitting: '提交中...',
  applySuccess: '申请已提交',
  applyFailed: '申请加入失败',
  paidPending: '付费入圈将在虚拟支付资质就绪后接入',
  pendingPostDetail: '资源详情页将在下一批次接入',
  noMembers: '暂无圈子成员',
  noEvents: '暂无圈子活动'
}

const PENDING_COLLECT_KEY = 'pendingCircleCollectCode'

Page({
  data: {
    UI_TEXT,
    circleCode: '',
    detail: emptyCircleDetail(),
    tabs: [
      { key: 'member', label: '成员' },
      { key: 'event', label: '活动' }
    ],
    activeTabKey: 'member',
    members: [],
    posts: [],
    isOwner: false,
    isLoggedIn: false,
    joinAction: { text: '申请加入', disabled: false },
    descExpanded: false,
    descExpandable: false,
    loading: true
  },

  onLoad(options = {}) {
    const code = String((options && options.code) || '').trim()
    if (!code) {
      wx.showToast({ title: UI_TEXT.missingCode, icon: 'none' })
      this.setData({ loading: false })
      return
    }

    this.setData({ circleCode: code })
    this._syncLoginState()
    this.loadAll()
  },

  onShow() {
    this._syncLoginState()
    this._consumePendingCollect()
  },

  /* ---------------- 取数 ---------------- */

  async loadAll() {
    const code = this.data.circleCode
    if (!code) {
      return
    }

    this.setData({ loading: true })
    try {
      await Promise.all([
        this.loadDetail(),
        this.loadMembers(),
        this.loadPosts()
      ])
    } finally {
      this.setData({ loading: false })
    }
  },

  async loadDetail() {
    const code = this.data.circleCode
    try {
      const serverDetail = await withFallback(
        () => getCircleDetail(code),
        () => mockCircleDetail(code),
        { silent: true }
      )
      const detail = buildCircleDetail(serverDetail, this.data.detail)
      this.setData({ detail }, () => this._syncDerived())
    } catch (err) {
      wx.showToast({ title: (err && err.message) || UI_TEXT.loadFailed, icon: 'none' })
    }
  },

  async loadMembers() {
    const code = this.data.circleCode
    try {
      const payload = await withFallback(
        () => getCircleMembers(code, { offset: 0, limit: 50 }),
        () => mockCircleMembers({ limit: 20 }),
        { silent: true }
      )
      const items = Array.isArray(payload && payload.items) ? payload.items : []
      this.setData({ members: items.map((item, index) => mapCircleMember(item, index)) })
    } catch (err) {
      this.setData({ members: [] })
      wx.showToast({ title: (err && err.message) || UI_TEXT.membersFailed, icon: 'none' })
    }
  },

  async loadPosts() {
    const code = this.data.circleCode
    try {
      const payload = await withFallback(
        () => getCirclePosts(code, { limit: 50 }),
        () => mockCirclePosts({ limit: 12 }),
        { silent: true }
      )
      const items = Array.isArray(payload && payload.items) ? payload.items : []
      this.setData({ posts: items.map((item) => mapResourcePostItem(item)) })
    } catch (err) {
      this.setData({ posts: [] })
      wx.showToast({ title: (err && err.message) || UI_TEXT.postsFailed, icon: 'none' })
    }
  },

  /* ---------------- 派生字段（原生没有 computed，统一在这里重算） ---------------- */

  _syncDerived() {
    const detail = this.data.detail || {}
    const currentUserId = this._resolveCurrentUserId()
    const isOwner = Boolean(currentUserId)
      && String(detail.owner && detail.owner.userId || '').trim() === currentUserId

    this.setData({
      isOwner,
      joinAction: mapJoinAction(detail.joinRequestStatus, detail.joinPaymentStatus, false),
      descExpandable: String(detail.description || '').length > 60
    })
  },

  _syncLoginState() {
    this.setData({ isLoggedIn: Boolean(String(wx.getStorageSync('token') || '').trim()) })
  },

  _resolveCurrentUserId() {
    const userInfo = wx.getStorageSync('userInfo')
    if (!userInfo || typeof userInfo !== 'object') {
      return ''
    }
    return String(userInfo.user_id || userInfo.userId || '').trim()
  },

  /* ---------------- 交互 ---------------- */

  onTabChange(event) {
    const key = (event && event.currentTarget && event.currentTarget.dataset.key) || 'member'
    if (key === this.data.activeTabKey) {
      return
    }
    this.setData({ activeTabKey: key })
  },

  onToggleDescription() {
    if (!this.data.descExpandable) {
      return
    }
    this.setData({ descExpanded: !this.data.descExpanded })
  },

  onMemberDetail(event) {
    const member = (event && event.detail && event.detail.member) || {}
    const userId = String(member.userId || '').trim()
    if (!userId) {
      wx.showToast({ title: UI_TEXT.missingUser, icon: 'none' })
      return
    }
    wx.navigateTo({ url: `/pages/card/index?userId=${encodeURIComponent(userId)}` })
  },

  onPostDetail(event) {
    const item = (event && event.detail && event.detail.item) || {}
    const postCode = String(item.postCode || '').trim()
    if (!postCode) {
      wx.showToast({ title: UI_TEXT.missingPost, icon: 'none' })
      return
    }
    wx.showToast({ title: UI_TEXT.pendingPostDetail, icon: 'none' })
  },

  onToggleInterest() {
    if (!this._ensureLoggedIn()) {
      return
    }
    this._submitInterest(!this.data.detail.isInterested)
  },

  onInterestBeforeLogin() {
    const code = String(this.data.circleCode || '').trim()
    if (!code) {
      wx.showToast({ title: UI_TEXT.missingCode, icon: 'none' })
      return
    }
    wx.setStorageSync(PENDING_COLLECT_KEY, code)
    wx.navigateTo({ url: '/pages/auth/login/index' })
  },

  /** 登录后回到本页时，补上进入登录页前发起的收藏 */
  _consumePendingCollect() {
    if (!this.data.isLoggedIn) {
      return
    }
    const pendingCode = String(wx.getStorageSync(PENDING_COLLECT_KEY) || '').trim()
    if (!pendingCode || pendingCode !== String(this.data.circleCode || '').trim()) {
      return
    }
    wx.removeStorageSync(PENDING_COLLECT_KEY)
    this._submitInterest(true)
  },

  async _submitInterest(desired) {
    const code = String(this.data.circleCode || '').trim()
    if (!code) {
      wx.showToast({ title: UI_TEXT.missingCode, icon: 'none' })
      return
    }

    try {
      const result = await toggleCircleCollection(code, desired)
      const nextInterested = Boolean(
        result && (result.is_collected ?? result.collected ?? result.is_interested ?? result.interested)
      )
      const collectCount = Number(
        (result && (result.collect_count ?? result.favorite_count)) ?? this.data.detail.collectCount ?? 0
      )

      const detail = Object.assign({}, this.data.detail, {
        isInterested: nextInterested,
        collectCount
      })
      this.setData({ detail })

      publishCircleInterestChange(code, nextInterested)
      wx.showToast({ title: nextInterested ? UI_TEXT.collected : UI_TEXT.uncollected, icon: 'none' })
    } catch (err) {
      wx.showToast({ title: (err && err.message) || UI_TEXT.operationFailed, icon: 'none' })
    }
  },

  async onApplyJoin() {
    if (!this._ensureLoggedIn()) {
      return
    }

    const amount = Number(this.data.detail.priceNumber || 0)
    if (amount > 0) {
      wx.showToast({ title: UI_TEXT.paidPending, icon: 'none' })
      return
    }

    const confirmed = await new Promise((resolve) => {
      wx.showModal({
        title: '申请加入圈子',
        content: '提交后圈主可审核，1个工作日未处理将自动加入。',
        confirmText: '提交申请',
        cancelText: '取消',
        success: (res) => resolve(Boolean(res && res.confirm)),
        fail: () => resolve(false)
      })
    })
    if (!confirmed) {
      return
    }

    this.setData({ joinAction: { text: UI_TEXT.applySubmitting, disabled: true } })
    wx.showLoading({ title: UI_TEXT.applySubmitting })

    try {
      await submitCircleJoinRequest(this.data.circleCode, {})
      await this.loadDetail()
      wx.showToast({ title: UI_TEXT.applySuccess, icon: 'success' })
    } catch (err) {
      wx.showToast({ title: (err && err.message) || UI_TEXT.applyFailed, icon: 'none' })
    } finally {
      wx.hideLoading()
      this._syncDerived()
    }
  },

  onShareAppMessage() {
    const detail = this.data.detail || {}
    const title = String(detail.title || '圈子详情').trim()
    return {
      title: `邀请你加入【${title}】· ${detail.membersText || ''}`,
      path: `/pages/circle-detail/index?code=${encodeURIComponent(this.data.circleCode)}`
    }
  },

  onShareTimeline() {
    const detail = this.data.detail || {}
    const title = String(detail.title || '圈子详情').trim()
    return {
      title: `邀请你加入【${title}】`,
      query: `code=${encodeURIComponent(this.data.circleCode)}`
    }
  },

  _ensureLoggedIn() {
    if (this.data.isLoggedIn) {
      return true
    }
    wx.showToast({ title: UI_TEXT.loginFirst, icon: 'none' })
    return false
  }
})
