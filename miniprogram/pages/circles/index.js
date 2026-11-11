/**
 * 圈子发现列表页
 * 对应 uni 版 pages/tab/circles/index.vue（原版 1190 行）
 *
 * 与 人脉 / 资源 保持同一套写法：
 *   - 分页 / 骨架屏 / 空状态 / 错误重试 交给 behaviors/paginated-list
 *   - 卡片展示字段由 utils/circle-card 在 setData 之前算好
 *   - 顶部筛选头复用 top-search-filter-header
 *
 * 原版列表里的"收藏"按钮是被注释掉的，这里同样不做收藏操作，
 * 但保留兴趣变更订阅：详情页收藏后回到本页能就地同步状态。
 *
 * 尚未迁移的圈子详情页用 toast 占位，跳转路径与参数已按原版写好。
 */

import { getDiscoverCircles } from '../../services/circle'
import { applyInterestToCard, mapCircleCard } from '../../utils/circle-card'
import { withFallback } from '../../utils/fallback'
import { mockDiscoverCircles } from '../../utils/mock'
import { INDUSTRY_OPTIONS } from '../../utils/industry-options'
import {
  consumeLatestCircleInterestChange,
  subscribeCircleInterestChange,
  unsubscribeCircleInterestChange
} from '../../utils/circle-interest'
import paginatedList from '../../behaviors/paginated-list'

const UI_TEXT = {
  searchPlaceholder: '搜索圈子名称或关键词',
  recommend: '推荐',
  industry: '行业',
  allIndustry: '全部行业',
  empty: '暂无可推荐圈子',
  emptyDesc: '试试调整筛选条件或搜索关键词',
  retry: '重新加载',
  loading: '加载中...',
  loadMore: '上拉加载更多',
  noMore: '没有更多圈子了',
  loadError: '圈子推荐加载失败，请稍后重试',
  missingCode: '圈子编号缺失'
}

const app = getApp()

Page({
  behaviors: [paginatedList],

  data: {
    UI_TEXT,
    keyword: '',
    activeTab: 'recommend',
    selectedIndustry: '',

    // 自定义导航避让
    topPaddingPx: 0,
    capsuleRowHeightPx: 32,
    capsuleAvoidRightInsetPx: 0,

    topTabs: [{ key: 'recommend', label: UI_TEXT.recommend }],
    rightControls: [],
    activeRightKeys: [],
    industryOptions: []
  },

  onLoad() {
    this._initNavMetrics()
    this._initFilterOptions()

    // 详情页收藏后回到列表时同步：eventBus + storage 双通道
    this._interestHandler = (payload) => this.onInterestChange(payload)
    subscribeCircleInterestChange(this._interestHandler)

    this.initList()
  },

  onShow() {
    this.onInterestChange(consumeLatestCircleInterestChange())
  },

  onUnload() {
    if (this._searchTimer) {
      clearTimeout(this._searchTimer)
      this._searchTimer = null
    }
    if (this._interestHandler) {
      unsubscribeCircleInterestChange(this._interestHandler)
      this._interestHandler = null
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
    this.setData({ industryOptions: INDUSTRY_OPTIONS }, () => this._syncControls())
  },

  /** 重算顶部右侧控件，替代 computed */
  _syncControls() {
    const hasIndustry = Boolean(String(this.data.selectedIndustry || '').trim())

    this.setData({
      rightControls: [
        {
          key: 'industry',
          label: String(this.data.selectedIndustry || '').trim() || UI_TEXT.industry,
          dot: hasIndustry
        }
      ],
      activeRightKeys: hasIndustry ? ['industry'] : []
    })
  },

  onTapRightControl(event) {
    const key = (event && event.detail && event.detail.key) || ''
    if (key === 'industry') {
      this.showIndustryPicker()
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

  onChangeTab(event) {
    const key = (event && event.detail && event.detail.key) || 'recommend'
    if (key === this.data.activeTab) {
      return
    }
    this.setData({ activeTab: key }, () => {
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
      tab: this.data.activeTab,
      keyword: String(this.data.keyword || '').trim(),
      industry_label: String(this.data.selectedIndustry || '').trim()
    })

    return withFallback(
      () => getDiscoverCircles(merged),
      () => mockDiscoverCircles(merged),
      { silent: true }
    )
  },

  mapListItem(item, index) {
    return mapCircleCard(item, index)
  },

  /* ---------------- 收藏状态同步 ---------------- */

  onInterestChange(payload) {
    const circleCode = String((payload && payload.circleCode) || '').trim()
    if (!circleCode) {
      return
    }

    const items = this.data.listItems || []
    let changed = false
    const nextItems = items.map((item) => {
      if (String(item.circleCode || '').trim() !== circleCode) {
        return item
      }
      if (Boolean(item.interested) === Boolean(payload.interested)) {
        return item
      }
      changed = true
      return applyInterestToCard(item, payload.interested)
    })

    if (changed) {
      this.setData({ listItems: nextItems })
    }
  },

  /* ---------------- 交互 ---------------- */

  onTapDetail(event) {
    const item = (event && event.detail && event.detail.item) || {}
    const circleCode = String(item.circleCode || '').trim()
    if (!circleCode) {
      wx.showToast({ title: UI_TEXT.missingCode, icon: 'none' })
      return
    }

    wx.navigateTo({
      url: `/pages/circle-detail/index?code=${encodeURIComponent(circleCode)}`
    })
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
