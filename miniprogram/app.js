const NAV_BAR_HEIGHT_FALLBACK = 44
const STATUS_BAR_HEIGHT_FALLBACK = 20

function readWindowInfo() {
  if (typeof wx.getWindowInfo === 'function') {
    try {
      return wx.getWindowInfo() || {}
    } catch (error) {
      return {}
    }
  }
  try {
    return wx.getSystemInfoSync() || {}
  } catch (error) {
    return {}
  }
}

function readMenuButtonRect() {
  if (typeof wx.getMenuButtonBoundingClientRect !== 'function') {
    return null
  }
  try {
    return wx.getMenuButtonBoundingClientRect() || null
  } catch (error) {
    return null
  }
}

App({
  globalData: {
    token: '',
    userInfo: null,
    isLoggedIn: false,
    unreadCount: 0,
    currentCity: '',
    // 置为 true 时所有请求直接走本地兜底数据，不走网络（演示 / 联调用）
    mockEnabled: false,
    usingMockData: false,
    navBar: {
      statusBarHeight: STATUS_BAR_HEIGHT_FALLBACK,
      navBarHeight: NAV_BAR_HEIGHT_FALLBACK,
      totalHeight: STATUS_BAR_HEIGHT_FALLBACK + NAV_BAR_HEIGHT_FALLBACK,
      menuRight: 10,
      menuWidth: 87,
      menuHeight: 32
    },
    windowInfo: {}
  },

  onLaunch() {
    this.initWindowMetrics()
    this.restoreLoginState()
    // TODO(P1): connectRealtimeSocket()
    // TODO(P2): syncUserLocation()
  },

  onShow() {
    // TODO(P1): connectRealtimeSocket()
  },

  onHide() {
    // TODO(P1): disconnectRealtimeSocket()
  },

  initWindowMetrics() {
    const windowInfo = readWindowInfo()
    const menuRect = readMenuButtonRect()
    const statusBarHeight = Number(windowInfo.statusBarHeight) || STATUS_BAR_HEIGHT_FALLBACK

    let navBarHeight = NAV_BAR_HEIGHT_FALLBACK
    let menuRight = 10
    let menuWidth = 87
    let menuHeight = 32

    if (menuRect && menuRect.height) {
      navBarHeight = (menuRect.top - statusBarHeight) * 2 + menuRect.height
      menuRight = windowInfo.windowWidth ? windowInfo.windowWidth - menuRect.right : 10
      menuWidth = menuRect.width
      menuHeight = menuRect.height
    }

    this.globalData.windowInfo = windowInfo
    this.globalData.navBar = {
      statusBarHeight,
      navBarHeight,
      totalHeight: statusBarHeight + navBarHeight,
      menuRight,
      menuWidth,
      menuHeight
    }
  },

  restoreLoginState() {
    let token = ''
    let userInfo = null

    try {
      token = wx.getStorageSync('token') || ''
      userInfo = wx.getStorageSync('userInfo') || null
    } catch (error) {
      token = ''
      userInfo = null
    }

    this.setLoginState(token, userInfo)
  },

  setLoginState(token, userInfo) {
    this.globalData.token = token || ''
    this.globalData.userInfo = userInfo || null
    this.globalData.isLoggedIn = Boolean(this.globalData.token)
    return this.globalData.isLoggedIn
  },

  clearLoginState() {
    this.globalData.token = ''
    this.globalData.userInfo = null
    this.globalData.isLoggedIn = false
    this.globalData.unreadCount = 0

    try {
      wx.removeStorageSync('token')
      wx.removeStorageSync('userInfo')
      wx.removeStorageSync('isLoggedIn')
    } catch (error) {
      // 忽略清理失败
    }
  }
})
