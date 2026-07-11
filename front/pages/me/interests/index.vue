<template>
  <view class="interests-page">
    <view class="filter-header">
      <view class="search-bar">
        <view class="search-input-wrap">
          <input
            class="search-input"
            type="text"
            :value="searchKeyword"
            placeholder="搜索已收藏的人脉、资源或圈子"
            placeholder-class="search-placeholder"
            confirm-type="search"
            @input="onSearchInput"
            @confirm="onSearchConfirm"
          />
          <view v-if="searchKeyword" class="search-clear" hover-class="search-clear-active" @tap="onClearSearch">
            <text class="search-clear-text">清除</text>
          </view>
        </view>
      </view>

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
            <text class="empty-title">{{ emptyTitle }}</text>
            <text class="empty-desc">{{ emptyDescription }}</text>
          </view>

          <template v-if="activeTab === 'contacts'">
            <view
              v-for="(contact, index) in filteredItems"
              :key="contact.id"
              class="contact-card item-enter"
              :style="{ animationDelay: `${index * 50}ms` }"
              hover-class="contact-card-active"
              @tap="onViewContact(contact)"
            >
              <image class="contact-avatar" :src="contact.avatar" mode="aspectFill" />
              <view class="contact-info">
                <view class="contact-name-row">
                  <text class="contact-name">{{ contact.name }}</text>
                  <image
                    v-if="contact.isVerified"
                    class="verified-badge"
                    src="https://cos.cnptec.site/static/icon/certification.png"
                    mode="aspectFit"
                  />
                </view>
                <text v-if="contact.detail" class="contact-detail">{{ contact.detail }}</text>
                <text v-if="contact.bio" class="contact-bio">{{ contact.bio }}</text>
              </view>
              <view
                class="collect-action"
                :class="{ 'collect-action-pending': pendingContactIds[contact.id] }"
                hover-class="collect-action-active"
                @tap.stop="onToggleContactInterest(contact)"
              >
                <text class="collect-action-text">已收藏</text>
              </view>
            </view>
          </template>

          <template v-else-if="activeTab === 'resources'">
            <ProfilePostCard
              v-for="(post, index) in filteredItems"
              :key="post.id"
              :item="post"
              :show-interest="true"
              :style="{ animationDelay: `${index * 50}ms` }"
              class="item-enter"
              @detail="onTapPostDetail"
              @interest="onTogglePostInterest"
            />
          </template>

          <template v-else>
            <DiscoverListCard
              v-for="(circle, index) in filteredItems"
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
          <view v-else-if="loaded && hasAny && !searchKeyword" class="load-more-wrap">
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
import { getInterestedUsers, toggleUserInterest } from '../../../api/network'
import { getInterestedResources, toggleResourceInterest } from '../../../api/post'
import { getCollectedCircles, toggleCircleCollection } from '../../../api/circle'

const PAGE_SIZE = 20

const tabs = [
  { key: 'contacts', label: '人脉' },
  { key: 'resources', label: '资源' },
  { key: 'circles', label: '圈子' }
]

const activeTab = ref('contacts')
const searchKeyword = ref('')
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
const pendingContactIds = ref({})

const activeTabLabel = computed(() => tabs.find((tab) => tab.key === activeTab.value)?.label || '')
const hasAny = computed(() => items.value.length > 0)

const getSearchText = (item) => {
  if (activeTab.value === 'contacts') {
    return [item.name, item.detail, item.bio].join(' ')
  }

  if (activeTab.value === 'resources') {
    return [
      item.title,
      item.description,
      item.content,
      item.authorName,
      item.rawPost?.title,
      item.rawPost?.content,
      item.rawPost?.description
    ].join(' ')
  }

  return [
    item.name,
    item.title,
    item.description,
    item.intro,
    item.ownerName,
    item.industryLabel
  ].join(' ')
}

const filteredItems = computed(() => {
  const keyword = searchKeyword.value.trim().toLowerCase()
  if (!keyword) {
    return items.value
  }

  return items.value.filter((item) => getSearchText(item).toLowerCase().includes(keyword))
})

const showEmpty = computed(() => loaded.value && !loading.value && filteredItems.value.length === 0 && !loadError.value)
const emptyTitle = computed(() => (
  searchKeyword.value.trim()
    ? `未找到相关${activeTabLabel.value}`
    : `暂无收藏的${activeTabLabel.value}`
))
const emptyDescription = computed(() => (
  searchKeyword.value.trim()
    ? '换个关键词试试吧'
    : '去发现页面看看更多优质内容'
))

const showToast = (title) => {
  uni.showToast({
    title,
    icon: 'none'
  })
}

const mapContactItem = (item) => {
  const userId = String(item?.user_id || item?.userId || item?.id || '').trim()
  const detail = String(item?.detail_line || item?.detailLine || '').trim()
    || [item?.job_title, item?.company_name].map((value) => String(value || '').trim()).filter(Boolean).join(' · ')
    || String(item?.industry_label || item?.city_name || '').trim()

  return {
    id: userId,
    userId,
    name: String(item?.nickname || item?.name || '').trim() || '未命名用户',
    avatar: String(item?.avatar_url || item?.avatar || '').trim() || 'https://cos.cnptec.site/static/logo.png',
    detail,
    bio: String(item?.intro || '').trim(),
    isVerified: Boolean(item?.is_verified)
  }
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
    let data
    if (activeTab.value === 'contacts') {
      data = await getInterestedUsers({
        cursor: reset ? '' : nextCursor.value,
        limit: PAGE_SIZE
      })
    } else if (activeTab.value === 'resources') {
      data = await getInterestedResources({
        cursor: reset ? '' : nextCursor.value,
        limit: PAGE_SIZE
      })
    } else {
      data = await getCollectedCircles({
        cursor: reset ? '' : nextCursor.value,
        limit: PAGE_SIZE
      })
    }

    if (!isPageAlive.value || thisRequestId !== currentRequestId.value) {
      return
    }

    const incoming = Array.isArray(data?.items) ? data.items : []
    const mappedIncoming = activeTab.value === 'contacts'
      ? incoming.map(mapContactItem)
      : activeTab.value === 'resources'
        ? incoming.map(mapProfilePostItem)
        : incoming

    if (reset) {
      items.value = mappedIncoming
    } else {
      const existingIds = new Set(items.value.map((item) => item.id))
      items.value = [...items.value, ...mappedIncoming.filter((item) => !existingIds.has(item.id))]
    }

    nextCursor.value = String(data?.next_cursor || data?.cursor || '').trim()
    hasMore.value = Boolean(data?.has_more)
    loaded.value = true
    loadError.value = ''
  } catch (error) {
    if (!isPageAlive.value || thisRequestId !== currentRequestId.value) {
      return
    }

    const message = error?.message || '加载失败，请稍后重试'
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

const onSearchInput = (event) => {
  searchKeyword.value = event?.detail?.value || ''
}

const onSearchConfirm = () => {
  searchKeyword.value = searchKeyword.value.trim()
}

const onClearSearch = () => {
  searchKeyword.value = ''
}

const onChangeTab = (key) => {
  if (activeTab.value === key) {
    return
  }

  currentRequestId.value++
  activeTab.value = key
  searchKeyword.value = ''
  items.value = []
  nextCursor.value = ''
  hasMore.value = true
  loaded.value = false
  loadError.value = ''
  loading.value = false
  loadingMore.value = false
  fetchData(true)
}

const onViewContact = (contact) => {
  const userId = String(contact?.userId || contact?.id || '').trim()
  if (!userId) {
    showToast('用户编号缺失')
    return
  }

  uni.navigateTo({
    url: `/pages/me/card/index?userId=${encodeURIComponent(userId)}`
  })
}

const onToggleContactInterest = async (contact) => {
  const userId = String(contact?.userId || contact?.id || '').trim()
  if (!userId || pendingContactIds.value[userId]) {
    return
  }

  const targetIndex = items.value.findIndex((item) => item.id === userId)
  if (targetIndex < 0) {
    return
  }

  const removedItem = items.value[targetIndex]
  pendingContactIds.value[userId] = true
  items.value.splice(targetIndex, 1)

  try {
    await toggleUserInterest(userId, false)
    showToast('已取消收藏')
  } catch (error) {
    items.value.splice(targetIndex, 0, removedItem)
    showToast(error?.message || '操作失败，请稍后重试')
  } finally {
    delete pendingContactIds.value[userId]
  }
}

const onTapPostDetail = (post) => {
  const postCode = String(post?.postCode || post?.rawPost?.post_code || post?.post_code || '').trim()
  if (!postCode) {
    showToast('资源编号缺失')
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

  const targetIndex = items.value.findIndex((item) =>
    (item.postCode || item.rawPost?.post_code || item.post_code) === postCode
  )

  if (targetIndex >= 0) {
    const removedItem = items.value[targetIndex]
    items.value.splice(targetIndex, 1)

    try {
      await toggleResourceInterest(postCode, false)
      showToast('已取消收藏')
    } catch (error) {
      items.value.splice(targetIndex, 0, removedItem)
      showToast(error?.message || '操作失败，请稍后重试')
    }
  }
}

const onToggleCircleInterest = async (circle) => {
  const circleCode = String(circle?.circleCode || circle?.circle_code || '').trim()
  if (!circleCode) {
    return
  }

  const targetIndex = items.value.findIndex((item) =>
    String(item?.circleCode || item?.circle_code || '').trim() === circleCode
  )

  if (targetIndex >= 0) {
    const removedItem = items.value[targetIndex]
    items.value.splice(targetIndex, 1)

    try {
      await toggleCircleCollection(circleCode, false)
      showToast('已取消收藏')
    } catch (error) {
      items.value.splice(targetIndex, 0, removedItem)
      showToast(error?.message || '操作失败，请稍后重试')
    }
  }
}

const onRetry = () => {
  fetchData(true)
}

const onScrollToLower = () => {
  fetchData(false)
}

const runRefreshData = async () => {
  if (refreshing.value) {
    return
  }

  refreshing.value = true
  try {
    await fetchData(true)
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

.filter-header {
  position: sticky;
  top: 0;
  z-index: 10;
  background: #f6f6f8;
  border-bottom: 1rpx solid rgba(15, 23, 42, 0.06);
}

.search-bar {
  padding: 20rpx 32rpx 12rpx;
}

.search-input-wrap {
  height: 72rpx;
  padding: 0 24rpx;
  display: flex;
  align-items: center;
  gap: 16rpx;
  background: #ffffff;
  border: 1rpx solid rgba(15, 23, 42, 0.06);
  border-radius: 36rpx;
  box-shadow: 0 4rpx 14rpx rgba(15, 23, 42, 0.04);
}

.search-input {
  flex: 1;
  min-width: 0;
  height: 72rpx;
  color: #0f172a;
  font-size: 28rpx;
  line-height: 72rpx;
}

.search-placeholder {
  color: #94a3b8;
}

.search-clear {
  flex-shrink: 0;
  padding: 10rpx 4rpx 10rpx 16rpx;
}

.search-clear-active {
  opacity: 0.6;
}

.search-clear-text {
  color: #64748b;
  font-size: 24rpx;
}

.tabs-wrap {
  height: 88rpx;
  padding: 0 32rpx;
  display: flex;
  align-items: center;
  gap: 48rpx;
}

.tab-item {
  position: relative;
  height: 88rpx;
  display: flex;
  align-items: center;
  justify-content: center;
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
  width: 48rpx;
  height: 4rpx;
  border-radius: 2rpx;
  background: #1a57db;
  transform: translateX(-50%);
}

.content-scroll {
  height: calc(100vh - 192rpx);
}

.content-wrap {
  padding: 24rpx 32rpx calc(48rpx + env(safe-area-inset-bottom));
  display: flex;
  flex-direction: column;
  gap: 24rpx;
}

.contact-card {
  position: relative;
  padding: 28rpx;
  display: flex;
  align-items: flex-start;
  gap: 20rpx;
  background: #fafbfc;
  border: 1rpx solid rgba(15, 23, 42, 0.06);
  border-radius: 20rpx;
  box-shadow: 0 4rpx 16rpx rgba(15, 23, 42, 0.04);
}

.contact-card-active {
  background: #f1f5f9;
}

.contact-avatar {
  width: 96rpx;
  height: 96rpx;
  flex-shrink: 0;
  border-radius: 48rpx;
  background: #e2e8f0;
}

.contact-info {
  flex: 1;
  min-width: 0;
  padding-right: 112rpx;
}

.contact-name-row {
  display: flex;
  align-items: center;
  gap: 8rpx;
  margin-bottom: 6rpx;
}

.contact-name {
  max-width: 280rpx;
  overflow: hidden;
  color: #0f172a;
  font-size: 32rpx;
  line-height: 44rpx;
  font-weight: 600;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.verified-badge {
  width: 30rpx;
  height: 30rpx;
  flex-shrink: 0;
}

.contact-detail,
.contact-bio {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
}

.contact-detail {
  color: #64748b;
  font-size: 25rpx;
  line-height: 36rpx;
  white-space: nowrap;
}

.contact-bio {
  margin-top: 6rpx;
  color: #94a3b8;
  font-size: 24rpx;
  line-height: 34rpx;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.collect-action {
  position: absolute;
  top: 28rpx;
  right: 28rpx;
  height: 48rpx;
  padding: 0 16rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(26, 87, 219, 0.08);
  border-radius: 12rpx;
}

.collect-action-active {
  background: rgba(239, 68, 68, 0.08);
}

.collect-action-pending {
  opacity: 0.5;
  pointer-events: none;
}

.collect-action-text {
  color: #1a57db;
  font-size: 24rpx;
  font-weight: 500;
}

.collect-action-active .collect-action-text {
  color: #ef4444;
}

.item-enter {
  opacity: 0;
  animation: fadeInUp 0.4s ease-out forwards;
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
  min-height: 320rpx;
  padding: 48rpx 32rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 20rpx;
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
  border-radius: 24rpx;
  box-shadow: 0 4rpx 16rpx rgba(15, 23, 42, 0.04);
}

.empty-state {
  padding: 120rpx 32rpx 80rpx;
  background: transparent;
  box-shadow: none;
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
  text-align: center;
}

.empty-title {
  margin-top: 8rpx;
  color: #1e293b;
  font-size: 32rpx;
  line-height: 44rpx;
  font-weight: 600;
}

.retry-btn {
  height: 72rpx;
  margin-top: 8rpx;
  padding: 0 40rpx;
  color: #ffffff;
  font-size: 28rpx;
  line-height: 72rpx;
  background: #1a57db;
  border: 0;
  border-radius: 36rpx;
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
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16rpx;
  text-align: center;
}

.load-more-text {
  color: #94a3b8;
  font-size: 24rpx;
  line-height: 32rpx;
}

@media (prefers-color-scheme: dark) {
  .interests-page,
  .filter-header {
    background: #0f172a;
  }

  .filter-header {
    border-bottom-color: #334155;
  }

  .search-input-wrap,
  .contact-card {
    background: #1e293b;
    border-color: rgba(241, 245, 249, 0.06);
  }

  .search-input,
  .contact-name,
  .empty-title {
    color: #f1f5f9;
  }

  .search-placeholder,
  .search-clear-text,
  .tab-text,
  .contact-detail,
  .status-text,
  .empty-desc {
    color: #94a3b8;
  }

  .tab-item-active .tab-text,
  .collect-action-text {
    color: #60a5fa;
  }

  .tab-item-active::after {
    background: #60a5fa;
  }

  .contact-card-active {
    background: #334155;
  }

  .contact-bio {
    color: #64748b;
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
}
</style>
