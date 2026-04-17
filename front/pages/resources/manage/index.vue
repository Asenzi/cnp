<template>
  <view class="manage-page">
    <view class="status-tabs">
      <button
        v-for="item in statusTabs"
        :key="item.key"
        class="status-tab"
        :class="activeStatus === item.key ? 'status-tab-active' : ''"
        hover-class="status-tab-hover"
        @tap="onChangeStatus(item.key)"
      >
        {{ item.label }}
      </button>
    </view>

    <scroll-view
      class="manage-scroll"
      scroll-y
      :show-scrollbar="false"
      :lower-threshold="120"
      @scrolltolower="onScrollToLower"
    >
      <view class="list-wrap">
        <view v-if="loading && !hasAny" class="status-wrap">
          <text class="status-text">加载中...</text>
        </view>

        <view v-else-if="loadError && !hasAny" class="status-wrap">
          <text class="status-text">{{ loadError }}</text>
          <button class="retry-btn" hover-class="retry-btn-active" @tap="onRetry">重新加载</button>
        </view>

        <template v-else>
          <view v-for="item in posts" :key="item.post_code" class="post-card">
            <view class="post-head" @tap="onTapDetail(item)">
              <text class="post-title">{{ item.title || '未命名资源' }}</text>
              <view class="badge-row">
                <text v-if="item.is_pinned" class="badge badge-pin">置顶</text>
                <text class="badge" :class="item.status === 'active' ? 'badge-online' : 'badge-offline'">
                  {{ item.status === 'active' ? '已上架' : '已下架' }}
                </text>
              </view>
            </view>
            <text class="post-desc">{{ item.description || '' }}</text>
            <view class="meta-row">
              <text class="meta-text">{{ item.time_text || '刚刚' }}</text>
              <text class="meta-text">浏览 {{ item.view_count || 0 }}</text>
              <text class="meta-text">点赞 {{ item.like_count || 0 }}</text>
            </view>
            <view class="action-row">
              <button class="action-btn" hover-class="action-btn-active" @tap="onEdit(item)">编辑</button>
              <button class="action-btn" hover-class="action-btn-active" @tap="onToggleStatus(item)">
                {{ item.status === 'active' ? '下架' : '上架' }}
              </button>
              <button class="action-btn" hover-class="action-btn-active" @tap="onTogglePin(item)">
                {{ item.is_pinned ? '取消置顶' : '置顶' }}
              </button>
              <button class="action-btn action-btn-danger" hover-class="action-btn-active" @tap="onDelete(item)">删除</button>
            </view>
          </view>

          <view v-if="showEmpty" class="status-wrap">
            <text class="status-text">暂无发布内容</text>
          </view>

          <view v-if="loadingMore" class="load-more-wrap">
            <text class="load-more-text">加载中...</text>
          </view>
          <view v-else-if="hasMore && hasAny" class="load-more-wrap">
            <text class="load-more-text">上拉加载更多</text>
          </view>
        </template>
      </view>
    </scroll-view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onPullDownRefresh, onShow } from '@dcloudio/uni-app'
import {
  deleteResourcePost,
  getMyResourceFeed,
  setResourcePostPin,
  setResourcePostStatus
} from '../../../api/post'

const PAGE_SIZE = 20
const statusTabs = [
  { key: 'all', label: '全部' },
  { key: 'active', label: '已上架' },
  { key: 'offline', label: '已下架' }
]

const activeStatus = ref('all')
const posts = ref([])
const loading = ref(false)
const loadingMore = ref(false)
const loaded = ref(false)
const loadError = ref('')
const hasMore = ref(true)
const nextCursor = ref('')
const refreshingByShow = ref(false)

const hasAny = computed(() => posts.value.length > 0)
const showEmpty = computed(() => loaded.value && !loading.value && !hasAny.value && !loadError.value)

const showToast = (title) => {
  uni.showToast({
    title,
    icon: 'none'
  })
}

const fetchMine = async (reset = false) => {
  if (loading.value || loadingMore.value) {
    return
  }
  if (!reset && (!hasMore.value || !nextCursor.value)) {
    return
  }

  if (reset) {
    loading.value = true
    loadError.value = ''
  } else {
    loadingMore.value = true
  }

  try {
    const data = await getMyResourceFeed({
      status: activeStatus.value === 'all' ? '' : activeStatus.value,
      cursor: reset ? '' : nextCursor.value,
      limit: PAGE_SIZE
    })

    const incoming = Array.isArray(data?.items) ? data.items : []
    if (reset) {
      posts.value = incoming
    } else {
      const exists = new Set(posts.value.map((item) => item.post_code))
      const appended = incoming.filter((item) => !exists.has(item.post_code))
      posts.value = [...posts.value, ...appended]
    }
    nextCursor.value = String(data?.next_cursor || '').trim()
    hasMore.value = Boolean(data?.has_more) && Boolean(nextCursor.value)
    loaded.value = true
    loadError.value = ''
  } catch (err) {
    const message = err?.message || '我的发布加载失败'
    if (reset && !hasAny.value) {
      loadError.value = message
    }
    showToast(message)
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

const onChangeStatus = (status) => {
  activeStatus.value = status || 'all'
  fetchMine(true)
}

const onTapDetail = (item) => () => {
  const postCode = encodeURIComponent(String(item?.post_code || '').trim())
  if (!postCode) {
    showToast('资源编号缺失')
    return
  }
  uni.navigateTo({
    url: `/pages/resources/detail/index?postCode=${postCode}`
  })
}

const onEdit = (item) => {
  const postCode = String(item?.post_code || '').trim()
  if (!postCode) {
    showToast('资源编号缺失')
    return
  }
  uni.navigateTo({
    url: `/pages/resources/publish/index?postCode=${encodeURIComponent(postCode)}`,
    events: {
      updated: () => fetchMine(true)
    }
  })
}

const onToggleStatus = async (item) => {
  const postCode = String(item?.post_code || '').trim()
  if (!postCode) {
    return
  }
  const nextStatus = item.status === 'active' ? 'offline' : 'active'
  try {
    const data = await setResourcePostStatus(postCode, nextStatus)
    const index = posts.value.findIndex((post) => post.post_code === postCode)
    if (index >= 0) {
      posts.value[index] = { ...posts.value[index], ...data }
      posts.value = [...posts.value]
    }
    showToast(nextStatus === 'active' ? '已上架' : '已下架')
    if (activeStatus.value !== 'all' && activeStatus.value !== nextStatus) {
      posts.value = posts.value.filter((post) => post.post_code !== postCode)
    }
  } catch (err) {
    showToast(err?.message || '状态更新失败')
  }
}

const onTogglePin = async (item) => {
  const postCode = String(item?.post_code || '').trim()
  if (!postCode) {
    return
  }
  try {
    const data = await setResourcePostPin(postCode, !item.is_pinned)
    const index = posts.value.findIndex((post) => post.post_code === postCode)
    if (index >= 0) {
      posts.value[index] = { ...posts.value[index], ...data }
      posts.value = [...posts.value]
    }
    showToast(data?.is_pinned ? '已置顶' : '已取消置顶')
    posts.value = [...posts.value].sort((a, b) => {
      const ap = a.is_pinned ? 1 : 0
      const bp = b.is_pinned ? 1 : 0
      if (ap !== bp) return bp - ap
      return String(b.created_at || '').localeCompare(String(a.created_at || ''))
    })
  } catch (err) {
    showToast(err?.message || '置顶操作失败')
  }
}

const onDelete = (item) => {
  const postCode = String(item?.post_code || '').trim()
  if (!postCode) {
    return
  }
  uni.showModal({
    title: '删除确认',
    content: '删除后不可恢复，是否继续？',
    confirmColor: '#ef4444',
    success: async (res) => {
      if (!res?.confirm) {
        return
      }
      try {
        await deleteResourcePost(postCode)
        posts.value = posts.value.filter((post) => post.post_code !== postCode)
        showToast('删除成功')
      } catch (err) {
        showToast(err?.message || '删除失败')
      }
    }
  })
}

const onRetry = () => {
  fetchMine(true)
}

const onScrollToLower = () => {
  fetchMine(false)
}

onShow(() => {
  if (!refreshingByShow.value) {
    refreshingByShow.value = true
    fetchMine(true).finally(() => {
      refreshingByShow.value = false
    })
  } else {
    fetchMine(true)
  }
})

onPullDownRefresh(async () => {
  await fetchMine(true)
  uni.stopPullDownRefresh()
})
</script>

<style scoped>
.manage-page {
  height: 100vh;
  overflow: hidden;
  background: #f6f6f8;
}

.status-tabs {
  padding: 16rpx 20rpx;
  display: flex;
  gap: 12rpx;
  background: #ffffff;
  border-bottom: 1rpx solid #e5e7eb;
}

.status-tab {
  flex: 1;
  height: 64rpx;
  border-radius: 12rpx;
  border: 1rpx solid #dbe3ef;
  background: #f8fafc;
  color: #475569;
  font-size: 24rpx;
  line-height: 64rpx;
  font-weight: 600;
}

.status-tab::after {
  border: 0;
}

.status-tab-active {
  color: #1a57db;
  background: rgba(26, 87, 219, 0.12);
  border-color: #1a57db;
}

.status-tab-hover {
  opacity: 0.86;
}

.manage-scroll {
  height: calc(100vh - 96rpx);
}

.list-wrap {
  padding: 16rpx 20rpx calc(28rpx + env(safe-area-inset-bottom));
  display: flex;
  flex-direction: column;
  gap: 14rpx;
}

.post-card {
  background: #ffffff;
  border: 1rpx solid #eef2f7;
  border-radius: 14rpx;
  padding: 18rpx;
}

.post-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10rpx;
}

.post-title {
  flex: 1;
  color: #111827;
  font-size: 30rpx;
  line-height: 40rpx;
  font-weight: 700;
}

.badge-row {
  display: inline-flex;
  align-items: center;
  gap: 8rpx;
}

.badge {
  border-radius: 999rpx;
  padding: 4rpx 12rpx;
  font-size: 20rpx;
  line-height: 24rpx;
}

.badge-pin {
  color: #1a57db;
  background: rgba(26, 87, 219, 0.12);
}

.badge-online {
  color: #15803d;
  background: rgba(74, 222, 128, 0.2);
}

.badge-offline {
  color: #64748b;
  background: #e2e8f0;
}

.post-desc {
  margin-top: 10rpx;
  color: #475569;
  font-size: 25rpx;
  line-height: 34rpx;
}

.meta-row {
  margin-top: 10rpx;
  display: flex;
  gap: 14rpx;
}

.meta-text {
  color: #94a3b8;
  font-size: 22rpx;
  line-height: 30rpx;
}

.action-row {
  margin-top: 14rpx;
  display: flex;
  gap: 10rpx;
}

.action-btn {
  flex: 1;
  height: 58rpx;
  border-radius: 10rpx;
  border: 1rpx solid #dbe3ef;
  background: #f8fafc;
  color: #334155;
  font-size: 22rpx;
  line-height: 58rpx;
}

.action-btn::after {
  border: 0;
}

.action-btn-danger {
  color: #ef4444;
  border-color: rgba(239, 68, 68, 0.3);
  background: rgba(239, 68, 68, 0.08);
}

.action-btn-active {
  opacity: 0.84;
}

.status-wrap {
  border-radius: 16rpx;
  border: 1rpx dashed #cbd5e1;
  background: #ffffff;
  min-height: 220rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16rpx;
}

.status-text {
  color: #64748b;
  font-size: 24rpx;
  line-height: 32rpx;
}

.retry-btn {
  height: 58rpx;
  border-radius: 999rpx;
  border: 0;
  padding: 0 28rpx;
  font-size: 24rpx;
  line-height: 58rpx;
  color: #ffffff;
  background: #1a57db;
}

.retry-btn::after {
  border: 0;
}

.retry-btn-active {
  opacity: 0.9;
}

.load-more-wrap {
  padding: 16rpx 0 8rpx;
  text-align: center;
}

.load-more-text {
  color: #94a3b8;
  font-size: 22rpx;
  line-height: 30rpx;
}
</style>
