/**
 * 分页列表 Behavior
 *
 * 原生没有 computed，列表页最容易出 bug 的地方就是「加载中 / 加载更多 /
 * 空状态 / 骨架屏 / 错误重试」这五六个状态互相打架。
 * 这里统一维护状态机，页面只需实现 fetchList(params)。
 *
 * 页面需要实现：
 *   fetchList(params) -> Promise<{ items, next_cursor, has_more }>
 *   mapListItem(item)  -> 视图模型（可选，默认原样返回）
 *
 * 页面 data 中需要提供：
 *   listItems: []
 */

const DEFAULT_DEBOUNCE_MS = 280

module.exports = Behavior({
  data: {
    listItems: [],
    listLoading: false,
    listLoadingMore: false,
    listLoaded: false,
    listBootstrapping: true,
    listError: '',
    listHasMore: true,
    listCursor: '',
    listRequestId: '',
    listRefreshing: false,
    // 定位中也会撑起骨架屏，由页面在定位开始/结束时写入
    listLocating: false,
    // 以下为派生字段，由 _syncListFlags 统一重算，页面不要直接 setData
    listHasAny: false,
    listSkeleton: true,
    listEmpty: false
  },

  lifetimes: {
    detached() {
      if (this._listDebounceTimer) {
        clearTimeout(this._listDebounceTimer)
        this._listDebounceTimer = null
      }
      this._listSeq = (this._listSeq || 0) + 1000 // 让已在飞的请求失效
    }
  },

  methods: {
    /** 首次进入调用 */
    async initList() {
      this.setData({ listBootstrapping: true })
      try {
        await this.loadList(true)
      } finally {
        this.setData({ listBootstrapping: false }, () => {
          this._syncListFlags()
        })
      }
    },

    /**
     * @param {Boolean} reset true=重新加载，false=加载下一页
     * @param {Object}  options { forceRefresh, extraParams }
     */
    async loadList(reset = false, options = {}) {
      if (this.data.listLoading || this.data.listLoadingMore) {
        if (reset) this._listPendingReset = true
        return
      }

      if (!reset && !options.forceRefresh) {
        if (!this.data.listHasMore || !this.data.listCursor) return
      }

      if (!this._listSeq) this._listSeq = 0
      const seq = ++this._listSeq

      const patch = reset
        ? { listLoading: true, listError: '' }
        : { listLoadingMore: true }

      this.setData(patch, () => this._syncListFlags())

      try {
        const params = Object.assign({
          limit: this.data.listPageSize || 20,
          cursor: reset ? '' : this.data.listCursor,
          request_id: reset ? '' : this.data.listRequestId
        }, options.extraParams || {})

        const payload = await this.fetchList(params)
        if (seq !== this._listSeq) return // 已有更新的请求发出，丢弃本次结果

        const rawItems = Array.isArray(payload && payload.items) ? payload.items : []
        const mapper = this.mapListItem || ((item) => item)
        const mapped = rawItems.map(mapper)

        const nextItems = reset
          ? mapped
          : this._dedupeAppend(this.data.listItems, mapped)

        this.setData({
          listItems: nextItems,
          listRequestId: String((payload && payload.request_id) || '').trim(),
          listCursor: String((payload && payload.next_cursor) || '').trim(),
          listHasMore: Boolean(payload && payload.has_more)
            && Boolean(String((payload && payload.next_cursor) || '').trim()),
          listLoaded: true,
          listError: ''
        })
      } catch (err) {
        if (seq !== this._listSeq) return
        if (Number(err && err.statusCode || 0) === 401) {
          if (this.onListUnauthorized) this.onListUnauthorized(err)
          this.setData({ listError: '' })
          return
        }
        const message = String((err && err.message) || '加载失败，请稍后重试')
        if (reset || !this.data.listItems.length) {
          this.setData({ listError: message })
        }
      } finally {
        this.setData({
          listLoading: false,
          listLoadingMore: false,
          listRefreshing: false
        }, () => {
          this._syncListFlags()
          if (this._listPendingReset) {
            this._listPendingReset = false
            this.loadList(true, { forceRefresh: true })
          }
        })
      }
    },

    /** 下拉刷新 / 手动刷新 */
    async refreshList() {
      if (this.data.listRefreshing) return
      this.setData({ listRefreshing: true })
      await this.loadList(true, { forceRefresh: true })
      if (typeof wx.stopPullDownRefresh === 'function') {
        wx.stopPullDownRefresh()
      }
    },

    /** 条件变化（搜索词、筛选）时防抖重载 */
    scheduleReload(delay = DEFAULT_DEBOUNCE_MS) {
      if (this._listDebounceTimer) clearTimeout(this._listDebounceTimer)
      this._listDebounceTimer = setTimeout(() => {
        this._listDebounceTimer = null
        this.loadList(true)
      }, delay)
    },

    onListScrollToLower() {
      this.loadList(false)
    },

    onListRetry() {
      this.loadList(true, { forceRefresh: true })
    },

    /** 就地更新某一项（关注状态、点赞数等），避免整页重刷 */
    updateListItem(id, patch) {
      const targetId = String(id || '').trim()
      if (!targetId) return
      const nextItems = (this.data.listItems || []).map((item) => {
        if (String(item.id || '').trim() !== targetId) return item
        return Object.assign({}, item, patch)
      })
      this.setData({ listItems: nextItems }, () => this._syncListFlags())
    },

    _dedupeAppend(current = [], incoming = []) {
      const exists = new Set()
      current.forEach((item) => exists.add(String((item && item.id) || '')))
      return current.concat(incoming.filter((item) => !exists.has(String((item && item.id) || ''))))
    },

    /** 重算派生状态：必须在每次影响列表的 setData 之后调用 */
    _syncListFlags() {
      const hasAny = (this.data.listItems || []).length > 0
      // 骨架屏只用于「首次加载且还没有任何结果」。一旦 listLoaded 为真，
      // 无论结果是空还是有数据，都必须退出骨架屏，否则空状态永远显示不出来。
      this.setData({
        listHasAny: hasAny,
        listSkeleton: !hasAny && !this.data.listLoaded && (
          this.data.listBootstrapping || this.data.listLoading || this.data.listLocating === true
        ),
        listEmpty: this.data.listLoaded && !this.data.listLoading && !hasAny && !this.data.listError
      })
    }
  }
})
