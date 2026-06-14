<template>
  <view class="interests-page">
    <view class="tabs-wrap">
      <view
        v-for="tab in tabs"
        :key="tab.key"
        class="tab-item"
        :class="{ 'tab-item-active': activeTab === tab.key }"
        @tap="onChangeTab(tab.key)"
      >
        <text class="tab-text">{{ tab.label }}</text>
      </view>
    </view>

    <scroll-view
      class="content-scroll"
      scroll-y
      :show-scrollbar="false"
      :lower-threshold="120"
      :refresher-enabled="true"
      :refresher-triggered="refreshing"
      refresher-background="#f6f6f8"
      @scrolltolower="onScrollToLower"
      @refresherrefresh="onRefresherRefresh"
      @refresherrestore="onRefresherRestore"
      @refresherabort="onRefresherRestore"
    >
      <view class="content-wrap">
        <view v-if="loading && !hasAny" class="status-wrap">
          <view class="loading-spinner"></view>
          <text class="status-text">加载中...</text>
        </view>

        <view v-else-if="loadError && !hasAny" class="status-wrap">
          <text class="status-text">{{ loadError }}</text>
          <button class="retry-btn" hover-class="retry-btn-active" @tap="onRetry">重新加载</button>
        </view>

        <template v-else>
          <view v-if="showEmpty" class="empty-state">
            <image class="empty-icon-image" src="https://cos.cnptec.site/static/icon/data-block.png" mode="aspectFit" />
            <text class="empty-title">暂无感兴趣的{{ activeTabLabel }}</text>
            <text class="empty-desc">去发现页面找找感兴趣的内容吧</text>
          </view>

          <template v-if="activeTab === 'resources'">
            <ProfilePostCard
              v-for="(post, index) in items"
              :key="post.id"
              :item="post"
              :show-interest="true"
              :style="{ animationDelay: `${index * 50}ms` }"
              class="item-enter"
              @detail="onTapPostDetail"
              @interest="onTogglePostInterest"
            />
          </template>

          <template v-else-if="activeTab === 'circles'">
            <DiscoverListCard
              v-for="(circle, index) in items"
              :key="circle.id"
              :circle="circle"
              :style="{ animationDelay: `${index * 50}ms` }"
              class="item-enter"
              @interest="onToggleCircleInterest"
            />
          </template>

          <view v-if="loadingMore" class="load-more-wrap">
            <view class="loading-spinner loading-spinner-small"></view>
            <text class="load-more-text">加载中...</text>
          </view>
          <view v-else-if="hasMore && hasAny" class="load-more-wrap">
            <text class="load-more-text">上拉加载更多</text>
          </view>
          <view v-else-if="loaded && hasAny" class="load-more-wrap">
            <text class="load-more-text">没有更多了</text>
          </view>
        </template>
      </view>
    </scroll-view>
  </view>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { onPullDownRefresh } from '@dcloudio/uni-app'
import ProfilePostCard from '../card/components/ProfilePostCard.vue'
import DiscoverListCard from '../../tab/circles/components/DiscoverListCard.vue'
import { mapProfilePostItem } from '../card/modules/profile-home-view-model'
import { getInterestedResources, toggleResourceInterest } from '../../../api/post'
import { getInterestedCircles, toggleCircleInterest } from '../../../api/circle'

const PAGE_SIZE = 20

const tabs = [
  { key: 'resources', label: '资源' },
  { key: 'circles', label: '圈子' }
]

const activeTab = ref('resources')
const items = ref([])
const loading = ref(false)
const loadingMore = ref(false)
const loaded = ref(false)
const loadError = ref('')
const hasMore = ref(true)
const nextCursor = ref('')
const refreshing = ref(false)
const isPageAlive = ref(true)
const currentRequestId = ref(0)

const hasAny = computed(() => items.value.length > 0)
const showEmpty = computed(() => loaded.value && !loading.value && !hasAny.value && !loadError.value)
const activeTabLabel = computed(() => tabs.find((t) => t.key === activeTab.value)?.label || '')

const showToast = (title) => {
  uni.showToast({
    title,
    icon: 'none'
  })
}

const fetchData = async (reset = false) => {
  if (loading.value || loadingMore.value) {
    return
  }
  if (!reset && (!hasMore.value || !nextCursor.value)) {
    return
  }

  const thisRequestId = ++currentRequestId.value

  if (reset) {
    loading.value = true
    loadError.value = ''
  } else {
    loadingMore.value = true
  }

  try {
    // 璋冪敤瀹為檯API
    let data
    try {
      if (activeTab.value === 'resources') {
        data = await getInterestedResources({
          cursor: reset ? '' : nextCursor.value,
          limit: PAGE_SIZE
        })
      } else if (activeTab.value === 'circles') {
        data = await getInterestedCircles({
          cursor: reset ? '' : nextCursor.value,
          limit: PAGE_SIZE
        })
      }
    } catch (apiErr) {
      // 如果是404，说明后端接口未实现，返回空数据
      if (apiErr?.statusCode === 404) {
        console.log('API not implemented yet, returning empty data')
        data = {
          items: [],
          next_cursor: '',
          has_more: false
        }
      } else {
        throw apiErr
      }
    }

    if (!isPageAlive.value || thisRequestId !== currentRequestId.value) {
      return
    }

    const incoming = Array.isArray(data?.items) ? data.items : []

    if (reset) {
      if (activeTab.value === 'resources') {
        items.value = incoming.map(mapProfilePostItem)
      } else {
        items.value = incoming
      }
    } else {
      const existsMap = new Map(items.value.map((item) => [item.id, true]))
      const appended = incoming.filter((item) => !existsMap.has(item.id))
      if (activeTab.value === 'resources') {
        items.value = [...items.value, ...appended.map(mapProfilePostItem)]
      } else {
        items.value = [...items.value, ...appended]
      }
    }

    nextCursor.value = String(data?.next_cursor || data?.cursor || '').trim()
    hasMore.value = Boolean(data?.has_more)
    loaded.value = true
    loadError.value = ''
  } catch (err) {
    if (!isPageAlive.value || thisRequestId !== currentRequestId.value) {
      return
    }

    const message = err?.message || '加载失败，请稍后重试'
    if (reset && !hasAny.value) {
      loadError.value = message
    }
    showToast(message)
  } finally {
    if (thisRequestId === currentRequestId.value) {
      loading.value = false
      loadingMore.value = false
    }
  }
}

const onChangeTab = (key) => {
  if (activeTab.value === key) {
    return
  }
  activeTab.value = key
  fetchData(true)
}

const onTapPostDetail = (post) => {
  const postCode = String(post?.postCode || post?.rawPost?.post_code || post?.post_code || '').trim()
  if (!postCode) {
    showToast('璧勬簮缂栧彿缂哄け')
    return
  }
  uni.navigateTo({
    url: `/pages/resources/detail/index?postCode=${encodeURIComponent(postCode)}`
  })
}

const onTogglePostInterest = async (post) => {
  const postCode = String(post?.postCode || post?.rawPost?.post_code || post?.post_code || '').trim()
  if (!postCode) {
    return
  }

  // 乐观更新：从列表移除
  const targetIndex = items.value.findIndex((item) =>
    (item.postCode || item.rawPost?.post_code || item.post_code) === postCode
  )

  if (targetIndex >= 0) {
    const removedItem = items.value[targetIndex]
    items.value.splice(targetIndex, 1)

    try {
      await toggleResourceInterest(postCode, false)
      showToast('已取消感兴趣')
    } catch (err) {
      // 失败时恢复
      items.value.splice(targetIndex, 0, removedItem)
      const message = err?.message || '操作失败，请稍后重试'
      showToast(message)
    }
  }
}

const onToggleCircleInterest = async (circle) => {
  const circleCode = String(circle?.circleCode || '').trim()
  if (!circleCode) {
    return
  }

  // 乐观更新：从列表移除
  const targetIndex = items.value.findIndex((item) => item.circleCode === circleCode)

  if (targetIndex >= 0) {
    const removedItem = items.value[targetIndex]
    items.value.splice(targetIndex, 1)

    try {
      await toggleCircleInterest(circleCode, false)
      showToast('已取消感兴趣')
    } catch (err) {
      // 失败时恢复
      items.value.splice(targetIndex, 0, removedItem)
      const message = err?.message || '操作失败，请稍后重试'
      showToast(message)
    }
  }
}

const onRetry = () => {
  fetchData(true)
}

const onScrollToLower = () => {
  fetchData(false)
}

const refreshData = async () => {
  await fetchData(true)
}

const runRefreshData = async () => {
  if (refreshing.value) {
    return
  }

  refreshing.value = true
  try {
    await refreshData()
  } finally {
    refreshing.value = false
    uni.stopPullDownRefresh()
  }
}

const onRefresherRefresh = async () => {
  await runRefreshData()
}

const onRefresherRestore = () => {
  refreshing.value = false
}

onMounted(async () => {
  isPageAlive.value = true
  await fetchData(true)
})

onPullDownRefresh(async () => {
  await runRefreshData()
})

onUnmounted(() => {
  isPageAlive.value = false
  currentRequestId.value++
})
</script>

<style scoped>
.interests-page {
  min-height: 100vh;
  background: #f6f6f8;
}

.tabs-wrap {
  position: sticky;
  top: 0;
  z-index: 10;
  display: flex;
  align-items: center;
  background: #f6f6f8;
  border-bottom: 1rpx solid #f1f5f9;
  padding: 0 32rpx;
  gap: 30px;
}

.tab-item {
  height: 88rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.tab-text {
  color: #64748b;
  font-size: 28rpx;
  line-height: 40rpx;
  font-weight: 600;
  transition: all 0.2s ease;
}

.tab-item-active .tab-text {
  color: #1a57db;
  font-weight: 700;
}

.tab-item-active::after {
  content: '';
  position: absolute;
  left: 50%;
  bottom: 0;
  transform: translateX(-50%);
  width: 48rpx;
  height: 4rpx;
  border-radius: 2rpx;
}

.content-scroll {
  height: calc(100vh - 88rpx);
}

.content-wrap {
  padding: 24rpx 32rpx calc(48rpx + env(safe-area-inset-bottom));
  display: flex;
  flex-direction: column;
  gap: 24rpx;
}

.item-enter {
  animation: fadeInUp 0.4s ease-out forwards;
  opacity: 0;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20rpx);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.status-wrap,
.empty-state {
  border-radius: 24rpx;
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
  min-height: 320rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 20rpx;
  padding: 48rpx 32rpx;
  box-shadow: 0 4rpx 16rpx rgba(15, 23, 42, 0.04);
}

.empty-state {
  background: transparent;
  box-shadow: none;
  padding: 120rpx 32rpx 80rpx;
}

.empty-icon-image {
  width: 200rpx;
  height: 200rpx;
  margin-bottom: 12rpx;
}

.loading-spinner {
  width: 48rpx;
  height: 48rpx;
  border: 4rpx solid #e2e8f0;
  border-top-color: #1a57db;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.loading-spinner-small {
  width: 32rpx;
  height: 32rpx;
  border-width: 3rpx;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.status-text,
.empty-desc {
  color: #64748b;
  font-size: 26rpx;
  line-height: 36rpx;
}

.empty-icon-wrap {
  width: 120rpx;
  height: 120rpx;
  border-radius: 60rpx;
  background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 8rpx;
}

.empty-icon {
  font-size: 64rpx;
  line-height: 64rpx;
}

.empty-title {
  color: #1e293b;
  font-size: 32rpx;
  line-height: 44rpx;
  font-weight: 600;
  margin-top: 8rpx;
}

.retry-btn {
  height: 72rpx;
  border-radius: 36rpx;
  border: 0;
  padding: 0 40rpx;
  font-size: 28rpx;
  line-height: 72rpx;
  color: #ffffff;
  background: linear-gradient(135deg, #1a57db 0%, #1e40af 100%);
  box-shadow: 0 8rpx 16rpx rgba(26, 87, 219, 0.2);
  margin-top: 8rpx;
}

.retry-btn::after {
  border: 0;
}

.retry-btn-active {
  opacity: 0.85;
  transform: scale(0.98);
}

.load-more-wrap {
  padding: 20rpx 0 12rpx;
  text-align: center;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16rpx;
}

.load-more-text {
  color: #94a3b8;
  font-size: 24rpx;
  line-height: 32rpx;
}

@media (prefers-color-scheme: dark) {
  .interests-page {
    background: #0f172a;
  }

  .tabs-wrap {
    background: #1e293b;
    border-bottom-color: #334155;
  }

  .tab-text {
    color: #94a3b8;
  }

  .tab-item-active .tab-text {
    color: #60a5fa;
  }

  .tab-item-active::after {
    background: #60a5fa;
  }

  .status-wrap,
  .empty-state {
    background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
    box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.3);
  }

  .empty-state {
    background: transparent;
    box-shadow: none;
  }

  .loading-spinner {
    border-color: #334155;
    border-top-color: #3b82f6;
  }

  .empty-icon-wrap {
    background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
  }

  .status-text,
  .empty-desc {
    color: #94a3b8;
  }

  .empty-title {
    color: #f1f5f9;
  }

  .retry-btn {
    background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%);
    box-shadow: 0 8rpx 16rpx rgba(37, 99, 235, 0.3);
  }
}
</style>
