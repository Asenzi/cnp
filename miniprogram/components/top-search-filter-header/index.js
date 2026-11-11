/**
 * 顶部搜索 + 筛选头
 * 对应 uni 版 pages/tab/components/TopSearchFilterHeader.vue
 * 承载自定义导航栏（避开胶囊按钮）与左 tab / 右筛选控件
 */

Component({
  options: {
    addGlobalClass: false
  },

  properties: {
    keyword: {
      type: String,
      value: ''
    },
    searchPlaceholder: {
      type: String,
      value: '搜索'
    },
    topPaddingPx: {
      type: Number,
      value: 0
    },
    rightInsetPx: {
      type: Number,
      value: 0
    },
    searchBarHeightPx: {
      type: Number,
      value: 44
    },
    leftItems: {
      type: Array,
      value: []
    },
    activeLeftKey: {
      type: String,
      value: ''
    },
    rightItems: {
      type: Array,
      value: []
    },
    activeRightKeys: {
      type: Array,
      value: []
    }
  },

  data: {
    rightItemsView: [],
    searchBarHeight: 44,
    paddingRight: 16
  },

  observers: {
    'rightItems, activeRightKeys': function (rightItems, activeRightKeys) {
      const keys = activeRightKeys || []
      const view = (rightItems || []).map((item) => {
        return Object.assign({}, item, {
          _active: keys.indexOf(item.key) >= 0
        })
      })
      this.setData({ rightItemsView: view })
    },
    'searchBarHeightPx': function (value) {
      this.setData({ searchBarHeight: Math.max(Number(value || 0), 34) })
    },
    'rightInsetPx': function (value) {
      this.setData({ paddingRight: 16 + Math.max(Number(value || 0), 0) })
    }
  },

  methods: {
    onInput(event) {
      this.triggerEvent('update', { value: (event && event.detail && event.detail.value) || '' })
    },

    onTapLeft(event) {
      const key = event.currentTarget.dataset.key
      this.triggerEvent('changeleft', { key })
    },

    onTapRight(event) {
      const key = event.currentTarget.dataset.key
      this.triggerEvent('tapright', { key })
    }
  }
})
