/**
 * 资源库列表页
 * 对应 uni 版 pages/tab/resources/index.vue（原版 1068 行）
 *
 * 与 人脉页 保持同一套写法：
 *   - 分页 / 骨架屏 / 空状态 / 错误重试 交给 behaviors/paginated-list
 *   - 卡片的展示字段在 setData 之前由 utils/resource-card 一次性算好
 *   - 顶部筛选头复用 top-search-filter-header
 *
 * 尚未迁移的下游页面（资源详情 / 发布 / 管理）用 toast 占位，
 * 跳转链接与参数已按原版写好，接入时只改页面路径即可。
 */

import { getResourceFeed, reportResourceImpressions } from '../../services/post'
import { mapResourcePostItem } from '../../utils/resource-card'
import { withFallback } from '../../utils/fallback'
import { mockResourceFeed } from '../../utils/mock'
import { INDUSTRY_OPTIONS } from '../../utils/industry-options'
import paginatedList from '../../behaviors/paginated-list'

const UI_TEXT = {
  searchPlaceholder: '搜索资源、需求或合作项目',
  loading: '加载中...',
  retry: '重新加载',
  empty: '暂无匹配内容',
  emptyDesc: '换个关键词或筛选条件试试',
  loadMore: '上拉加载更多',
  demand: '需求',
  industry: '行业',
  sortLatest: '最新',
  sortPopular: '热门',
  manage: '管理',
  allIndustry: '全部行业',
  loadError: '资源列表加载失败，请稍后重试',
  loginFirst: '请先登录',
  missingPostCode: '资源编号缺失',
  pendingDetail: '资源详情页将在下一批次接入',
  pendingManage: '资源管理页将在下一批次接入',
  pendingPublish: '资源发布页将在下一批次接入'
}

const app = getApp()

Page({
  behaviors: [paginatedList],

  data: {
    UI_TEXT,
    keyword: '',
    activeMode: 'cooperate',
    sortKey: 'latest',
    selectedIndustry: '',

    // 自定义导航避让
    topPaddingPx: 0,
    capsuleRowHeightPx: 32,
    capsuleAvoidRightInsetPx: 0,

    topTabs: [{ key: 'cooperate', label: UI_TEXT.demand }],
    rightControls: [],
    activeRightKeys: [],
    industryOptions: []
  },

  onLoad() {
    this._initNavMetrics()
    this._initFilterOptions()
    this.initList()
  },

  onUnload() {
    if (this._searchTimer) {
      clearTimeout(this._searchTimer)
      this._searchTimer = null
    }
  },

  /* ---------------- 自定义导航 ---------------- */

  _initNavMetrics() {
    const navBar = (app && app.globalData && app.globalData.navBar) || {}
    const menuWidth = Number(navBar.menuWidth || 87)
    const menuHeight = Number(navBar.menuHeight || 32)
    const menuRight = Number(navBar.menuRight || 10)
    const statusBarHeight = Number(navBar.statusBarHeight || 0)

    this.setData({
      topPaddingPx: statusBarHeight + 6,
      capsuleRowHeightPx: menuHeight || 32,
      capsuleAvoidRightInsetPx: Math.max(menuRight + menuWidth - 8, 0)
    })
  },

  /* ---------------- 筛选控件 ---------------- */

  _initFilterOptions() {
    // 后端返回的行业列表是英文，本地维护中文列表（与原版一致）
    this.setData({ industryOptions: INDUSTRY_OPTIONS }, () => this._syncControls())
  },

  /** 重算顶部右侧控件，替代 computed */
  _syncControls() {
    const hasIndustry = Boolean(String(this.data.selectedIndustry || '').trim())
    const notLatest = this.data.sortKey !== 'latest'

    const activeRightKeys = []
    if (hasIndustry) activeRightKeys.push('industry')
    if (notLatest) activeRightKeys.push('sort')

    this.setData({
      rightControls: [
        {
          key: 'industry',
          label: String(this.data.selectedIndustry || '').trim() || UI_TEXT.industry,
          dot: hasIndustry
        },
        {
          key: 'sort',
          label: this.data.sortKey === 'latest' ? UI_TEXT.sortLatest : UI_TEXT.sortPopular
        },
        {
          key: 'manage',
          label: UI_TEXT.manage,
          showArrow: false
        }
      ],
      activeRightKeys
    })
  },

  onTapRightControl(event) {
    const key = (event && event.detail && event.detail.key) || ''
    if (key === 'industry') {
      this.showIndustryPicker()
      return
    }
    if (key === 'sort') {
      const nextSort = this.data.sortKey === 'latest' ? 'popular' : 'latest'
      this.setData({ sortKey: nextSort }, () => {
        this._syncControls()
        this.loadList(true, { forceRefresh: true })
      })
      return
    }
    if (key === 'manage') {
      if (!ensureLoggedIn()) return
      wx.showToast({ title: UI_TEXT.pendingManage, icon: 'none' })
    }
  },

  showIndustryPicker() {
    const items = [UI_TEXT.allIndustry].concat(this.data.industryOptions || [])
    wx.showActionSheet({
      itemList: items.slice(0, 12),
      success: (res) => {
        const picked = items[res.tapIndex]
        this.setData({
          selectedIndustry: picked === UI_TEXT.allIndustry ? '' : picked
        }, () => {
          this._syncControls()
          this.loadList(true, { forceRefresh: true })
        })
      },
      fail: () => {}
    })
  },

  onChangeFilter(event) {
    const key = (event && event.detail && event.detail.key) || 'cooperate'
    this.setData({ activeMode: key === 'resource' ? 'resource' : 'cooperate' }, () => {
      this.loadList(true, { forceRefresh: true })
    })
  },

  onKeywordInput(event) {
    const value = (event && event.detail && event.detail.value) || ''
    this.setData({ keyword: value })
    this.scheduleReload()
  },

  /* ---------------- 取数 ---------------- */

  async fetchList(params) {
    const merged = Object.assign({}, params, {
      mode: this.data.activeMode,
      sort: this.data.sortKey,
      keyword: String(this.data.keyword || '').trim(),
      industry_label: String(this.data.selectedIndustry || '').trim()
    })

    const payload = await withFallback(
      () => getResourceFeed(merged),
      () => mockResourceFeed(merged),
      { silent: true }
    )

    this._reportImpressions(payload)
    return payload
  },

  mapListItem(item) {
    return mapResourcePostItem(item)
  },

  /** 曝光上报，失败不影响浏览 */
  _reportImpressions(payload = {}) {
    try {
      const requestId = String(payload.request_id || '').trim()
      const items = Array.isArray(payload.items) ? payload.items : []
      if (!requestId || !items.length) return

      const postCodes = items
        .map((item) => String(item.post_code || '').trim())
        .filter(Boolean)

      if (!postCodes.length) return

      reportResourceImpressions({
        request_id: requestId,
        tab: this.data.activeMode,
        post_codes: postCodes
      })
    } catch (err) {
      // 曝光失败静默处理
    }
  },

  /* ---------------- 交互 ---------------- */

  onTapDetail(event) {
    const item = (event && event.detail && event.detail.item) || {}
    const postCode = String(item.postCode || '').trim()
    if (!postCode) {
      wx.showToast({ title: UI_TEXT.missingPostCode, icon: 'none' })
      return
    }

    // 资源详情页尚未迁移，先把目标页和参数定下来
    // （后续批次接 pages/resource-detail/index，参数 ?postCode=xxx）
    const isVenue = String(item.type || '').trim().toLowerCase() === 'venue'
    const targetPage = isVenue
      ? '/pages/resource-venue-detail/index'
      : '/pages/resource-detail/index'

    wx.showToast({ title: UI_TEXT.pendingDetail, icon: 'none' })
    console.log('[resources] 待迁移页面:', targetPage, 'postCode=', postCode)
  },

  onTapPublish() {
    if (!ensureLoggedIn()) return
    wx.showToast({ title: UI_TEXT.pendingPublish, icon: 'none' })
  },

  onListUnauthorized() {
    wx.removeStorageSync('token')
    wx.removeStorageSync('isLoggedIn')
    wx.removeStorageSync('userInfo')
  },

  onRefresherRefresh() {
    this.refreshList()
  },

  onRefresherRestore() {
    this.setData({ listRefreshing: false })
  }
})

function ensureLoggedIn() {
  if (Boolean(String(wx.getStorageSync('token') || '').trim())) return true
  wx.showToast({ title: UI_TEXT.loginFirst, icon: 'none' })
  return false
}
