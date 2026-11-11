/**
 * 人脉库列表页
 * 对应 uni 版 pages/tab/discover/index.vue（原版 1812 行）
 *
 * P1 垂直切片的中间环节：登录 -> 本页 -> 名片详情
 * 分页状态机统一交给 behaviors/paginated-list，本页只负责
 * 取数、字段映射与筛选条件。
 *
 * 筛选按原页面交互迁移：行业面板和独立城市选择页。
 */

import { getNetworkRecommendations, getNetworkFilterOptions } from '../../services/network'
import { mapMemberCard } from '../../utils/profile'
import { withFallback } from '../../utils/fallback'
import { mockRecommendations } from '../../utils/mock'
import { loadLocationFilterCache, saveLocationFilterCache, saveCurrentCity } from '../../utils/location'
import { resolveCurrentCityByGps, getLocationErrorMessage } from '../../utils/location'
import { INDUSTRY_OPTIONS } from '../../utils/industry-options'
import paginatedList from '../../behaviors/paginated-list'

const UI_TEXT = {
  searchPlaceholder: '搜索人脉、公司或职位',
  loading: '加载中...',
  retry: '重新加载',
  empty: '暂无推荐人脉',
  loadMore: '上拉加载更多',
  recommend: '推荐',
  industry: '行业',
  locating: '定位中...',
  loginFirst: '请先登录',
  unnamedUser: '未命名用户',
  verifyLv1: 'LV1 已认证',
  defaultRole: '暂未填写行业',
  activeFallback: '最近活跃',
  defaultCity: '全部',
  nationwideCity: '全国',
  missingTarget: '目标用户信息缺失'
}

const LOGIN_DISCOVER_REFRESH_STORAGE_KEY = 'discover_login_refresh_v1'
const LOCATION_HISTORY_STORAGE_KEY = 'network_location_history_v1'
const LOCATION_PAGE_RESULT_STORAGE_KEY = 'discover_location_page_result_v1'
const LOCATION_HISTORY_LIMIT = 8
const app = getApp()

Page({
  behaviors: [paginatedList],

  data: {
    UI_TEXT,
    keyword: '',
    activeTab: 'recommend',
    topTabs: [{ key: 'recommend', label: UI_TEXT.recommend }],

    // 自定义导航避让
    topPaddingPx: 0,
    capsuleRowHeightPx: 32,
    capsuleAvoidRightInsetPx: 0,

    // 筛选
    currentCity: UI_TEXT.defaultCity,
    
    isNationalScope: false,
    filters: {
      city_name: '',
      industry_label: ''
    },
    rightControls: [],
    activeRightKeys: [],
    filterVisible: false,
    filterOptions: { cities: [], industries: INDUSTRY_OPTIONS },
    locationHistoryCities: []
  },

  onLoad() {
    this._initNavMetrics()
    this._initLocationState()
    this._loadFilterOptions()
    this.initList()
  },

  onShow() {
    const shouldRefresh = Boolean(wx.getStorageSync(LOGIN_DISCOVER_REFRESH_STORAGE_KEY))
    if (shouldRefresh) {
      wx.removeStorageSync(LOGIN_DISCOVER_REFRESH_STORAGE_KEY)
      if (this.data.listItems.length > 0) {
        this.refreshList()
      }
    }

    const pendingLocation = wx.getStorageSync(LOCATION_PAGE_RESULT_STORAGE_KEY)
    if (pendingLocation && typeof pendingLocation === 'object') {
      wx.removeStorageSync(LOCATION_PAGE_RESULT_STORAGE_KEY)
      if (pendingLocation.type === 'select') this.applySelectedCity(pendingLocation.city)
      if (pendingLocation.type === 'relocate') this.applyRelocatedCity(pendingLocation.city)
    }
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
    const statusBarHeight = Number(navBar.statusBarHeight || 0)
    const menuRight = Number(navBar.menuRight || 10)
    const menuWidth = Number(navBar.menuWidth || 87)
    const menuHeight = Number(navBar.menuHeight || 32)

    this.setData({
      topPaddingPx: statusBarHeight + 6,
      capsuleRowHeightPx: menuHeight,
      // 胶囊左边界 = 屏宽 - 右边距 - 胶囊宽，搜索框右侧需让出这段 + 8px 间隙
      capsuleAvoidRightInsetPx: Math.max(menuRight + menuWidth - 8, 0)
    })
  },

  /* ---------------- 定位与筛选 ---------------- */

  _initLocationState() {
    const cache = loadLocationFilterCache() || {}
    let locationHistoryCities = []
    try {
      const storedHistory = wx.getStorageSync(LOCATION_HISTORY_STORAGE_KEY)
      locationHistoryCities = Array.isArray(storedHistory)
        ? storedHistory.map((item) => String(item || '').trim()).filter(Boolean)
        : []
    } catch (err) {}
    const cachedCity = String(
      cache.currentCity || wx.getStorageSync('currentCity') || wx.getStorageSync('locationCity') || ''
    ).trim()

    this.setData({
      currentCity: cachedCity || UI_TEXT.defaultCity,
      isNationalScope: cache.mode === 'national',
      'filters.city_name': String(cache.selectedCity || '').trim(),
      locationHistoryCities
    }, () => {
      this._syncControls()
    })

    const hasCache = Boolean(cache.currentCity || cache.selectedCity || cache.mode === 'national')
    if (!hasCache) {
      this.refreshLocation({ silent: true })
    }
  },

  _loadFilterOptions() {
    this.fetchFilterOptions()
  },

  /** 重算顶部右侧控件（城市 / 行业）——替代 computed */
  _syncControls() {
    const filters = this.data.filters || {}
    const displayCityName = this.data.isNationalScope
      ? UI_TEXT.nationwideCity
      : (String(filters.city_name || '').trim() || this.data.currentCity || UI_TEXT.defaultCity)

    const hasCityOverride = !this.data.isNationalScope
      && Boolean(String(filters.city_name || '').trim())
      && String(filters.city_name || '').trim() !== this.data.currentCity
    const hasIndustryFilter = Boolean(String(filters.industry_label || '').trim())

    const activeRightKeys = []
    if (hasCityOverride) activeRightKeys.push('locate')
    if (hasIndustryFilter) activeRightKeys.push('industry')

    this.setData({
      rightControls: [
        {
          key: 'locate',
          label: this.data.listLocating ? UI_TEXT.locating : displayCityName,
          dot: hasCityOverride
        },
        {
          key: 'industry',
          label: String(filters.industry_label || '').trim() || UI_TEXT.industry,
          dot: hasIndustryFilter
        }
      ],
      activeRightKeys
    })
  },

  async refreshLocation({ silent = false } = {}) {
    if (this.data.listLocating) return

    this.setData({ listLocating: true }, () => this._syncControls())

    try {
      const city = await resolveCurrentCityByGps()
      const normalized = String(city || '').trim()
      if (!normalized) return

      saveCurrentCity(normalized)
      saveLocationFilterCache({
        mode: 'city',
        currentCity: normalized,
        selectedCity: ''
      })

      this.setData({
        currentCity: normalized,
        isNationalScope: false,
        'filters.city_name': ''
      }, () => this._syncControls())

      if (!silent) {
        wx.showToast({ title: `已定位到：${normalized}`, icon: 'none' })
      }
      this.loadList(true, { forceRefresh: true })
    } catch (err) {
      if (!silent) {
        wx.showToast({ title: getLocationErrorMessage(err), icon: 'none' })
      }
    } finally {
      this.setData({ listLocating: false }, () => this._syncControls())
    }
  },

  onTapRightControl(event) {
    const key = event && event.detail && event.detail.key
    if (key === 'locate') {
      this.onOpenLocation()
      return
    }
    if (key === 'industry') {
      this.onOpenFilter()
    }
  },

  async fetchFilterOptions() {
    if (this._filterOptionsLoaded) return
    if (this._filterOptionsPromise) return this._filterOptionsPromise
    this._filterOptionsPromise = (async () => {
      try {
        const result = await getNetworkFilterOptions()
        const cities = Array.isArray(result && result.cities)
          ? result.cities.map((item) => String(item || '').trim()).filter(Boolean)
          : []
        this.setData({ 'filterOptions.cities': cities })
        this._filterOptionsLoaded = true
      } catch (err) {
        // 行业默认项仍可用，城市页会显示原项目的热门城市。
      } finally {
        this._filterOptionsPromise = null
      }
    })()
    return this._filterOptionsPromise
  },

  async onOpenFilter() {
    await this.fetchFilterOptions()
    this.setData({ filterVisible: true })
  },

  onCloseFilter() {
    this.setData({ filterVisible: false })
  },

  onResetFilter() {
    this.setData({ 'filters.industry_label': '', filterVisible: false }, () => {
      this._syncControls()
      this.loadList(true, { forceRefresh: true })
    })
  },

  onApplyFilter(event) {
    const industry = String(event && event.detail && event.detail.industry_label || '').trim()
    this.setData({ 'filters.industry_label': industry, filterVisible: false }, () => {
      this._syncControls()
      this.loadList(true, { forceRefresh: true })
    })
  },

  async onOpenLocation() {
    await this.fetchFilterOptions()
    const displayCityName = this.data.isNationalScope
      ? UI_TEXT.nationwideCity
      : String(this.data.filters.city_name || '').trim() || this.data.currentCity || UI_TEXT.defaultCity
    wx.navigateTo({
      url: `/pages/discover/city/index?currentCity=${encodeURIComponent(this.data.currentCity)}&selectedCity=${encodeURIComponent(displayCityName)}`,
      success: (res) => {
        const eventChannel = res.eventChannel
        eventChannel.emit('locationPage:init', {
          currentCity: this.data.currentCity,
          selectedCity: displayCityName,
          historyCities: this.data.locationHistoryCities || [],
          hotCities: this.data.filterOptions.cities || []
        })
        eventChannel.on('locationPage:select', ({ city }) => this.applySelectedCity(city))
        eventChannel.on('locationPage:relocate', ({ city }) => this.applyRelocatedCity(city))
      }
    })
  },

  applySelectedCity(city) {
    const normalized = String(city || '').trim()
    const nationwide = normalized === UI_TEXT.nationwideCity
    const selectedCity = nationwide || normalized === UI_TEXT.defaultCity || normalized === this.data.currentCity
      ? ''
      : normalized
    const nextHistory = !normalized || normalized === UI_TEXT.nationwideCity
      ? this.data.locationHistoryCities
      : [normalized].concat(this.data.locationHistoryCities || [])
        .filter((item, index, list) => item && list.indexOf(item) === index)
        .slice(0, LOCATION_HISTORY_LIMIT)
    this.setData({
      isNationalScope: nationwide,
      'filters.city_name': selectedCity,
      locationHistoryCities: nextHistory
    }, () => {
      wx.removeStorageSync(LOCATION_PAGE_RESULT_STORAGE_KEY)
      wx.setStorageSync(LOCATION_HISTORY_STORAGE_KEY, nextHistory)
      saveLocationFilterCache({
        mode: nationwide ? 'national' : 'city',
        currentCity: this.data.currentCity,
        selectedCity
      })
      this._syncControls()
      this.loadList(true, { forceRefresh: true })
    })
  },

  applyRelocatedCity(city) {
    const normalized = String(city || '').trim()
    if (!normalized) return
    saveCurrentCity(normalized)
    saveLocationFilterCache({ mode: 'city', currentCity: normalized, selectedCity: '' })
    const nextHistory = [normalized].concat(this.data.locationHistoryCities || [])
      .filter((item, index, list) => item && list.indexOf(item) === index)
      .slice(0, LOCATION_HISTORY_LIMIT)
    this.setData({
      currentCity: normalized,
      isNationalScope: false,
      'filters.city_name': '',
      locationHistoryCities: nextHistory
    }, () => {
      wx.removeStorageSync(LOCATION_PAGE_RESULT_STORAGE_KEY)
      wx.setStorageSync(LOCATION_HISTORY_STORAGE_KEY, nextHistory)
      this._syncControls()
      this.loadList(true, { forceRefresh: true })
    })
  },

  onChangeTab(event) {
    const key = (event && event.detail && event.detail.key) || 'recommend'
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
      city_name: this.data.isNationalScope ? '' : String(this.data.filters.city_name || '').trim(),
      industry_label: String(this.data.filters.industry_label || '').trim()
    })

    return withFallback(
      () => getNetworkRecommendations(merged),
      () => mockRecommendations(merged),
      { silent: true }
    )
  },

  mapListItem(item) {
    return mapMemberCard(item, UI_TEXT)
  },

  /* ---------------- 交互 ---------------- */

  onViewProfile(event) {
    const member = (event && event.detail && event.detail.member) || {}
    const targetUserId = String(member.businessUserId || '').trim()
    if (!targetUserId) {
      wx.showToast({ title: UI_TEXT.missingTarget, icon: 'none' })
      return
    }
    wx.navigateTo({
      url: `/pages/card/index?userId=${encodeURIComponent(targetUserId)}`
    })
  },

  onGoVerify() {
    wx.showToast({ title: '认证流程将在后续批次接入', icon: 'none' })
  },

  onRefresherRefresh() {
    this.refreshList()
  },

  onRefresherRestore() {
    this.setData({ listRefreshing: false })
  }
})
