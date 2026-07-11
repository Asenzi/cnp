<template>
  <view class="followers-page">
    <view class="page-header" :style="{ paddingTop: statusBarHeight + 'px' }">
      <view class="header-bar">
        <view class="back-btn" hover-class="back-btn-active" @tap="onBack">
          <text class="back-icon">‹</text>
        </view>
        <text class="header-title">我的粉丝</text>
        <view class="header-spacer"></view>
      </view>
      <view class="search-bar">
        <view class="search-input-wrap">
          <input class="search-input" type="text" placeholder="搜索姓名、公司或职位" :value="searchKeyword" @input="onSearchInput"
            confirm-type="search" @confirm="onSearchConfirm" />
          <view v-if="searchKeyword" class="search-clear" @tap="onClearSearch">
            <text class="clear-icon">×</text>
          </view>
        </view>
      </view>
    </view>

    <scroll-view class="content-scroll" scroll-y :show-scrollbar="false" :refresher-enabled="true"
      :refresher-triggered="refreshing" :lower-threshold="120" refresher-background="#f8f9fa"
      @refresherrefresh="onRefresh" @refresherrestore="onRefreshRestore" @scrolltolower="onLoadMore">
      <view class="followers-list">
        <!-- Loading skeleton -->
        <view v-if="loading && !hasAny" class="skeleton-list">
          <view v-for="i in 3" :key="`skeleton-${i}`" class="skeleton-card">
            <view class="skeleton-avatar"></view>
            <view class="skeleton-info">
              <view class="skeleton-line skeleton-name"></view>
              <view class="skeleton-line skeleton-detail"></view>
              <view class="skeleton-line skeleton-bio"></view>
            </view>
          </view>
        </view>

        <!-- Error state -->
        <view v-else-if="loadError && !hasAny" class="status-wrap">
          <image class="status-icon" src="https://cos.cnptec.site/static/icon/data-block.png" mode="aspectFit" />
          <text class="status-text">{{ loadError }}</text>
          <view class="retry-btn" hover-class="retry-btn-active" @tap="onRetry">
            <text class="retry-btn-text">重新加载</text>
          </view>
        </view>

        <!-- Empty state -->
        <view v-else-if="loaded && !hasAny" class="empty-wrap">
          <image class="empty-icon-image" src="https://cos.cnptec.site/static/icon/data-block.png" mode="aspectFit" />
          <text class="empty-title">还没有粉丝</text>
          <text class="empty-subtitle">完善个人信息，发布优质内容，吸引更多关注</text>
        </view>

        <!-- Followers list -->
        <template v-else>
          <view v-for="item in followersList" :key="item.id" class="follower-card" hover-class="follower-card-active"
            @tap="onViewProfile(item)">
            <view class="card-main">
              <image class="user-avatar" mode="aspectFill" :src="item.avatar" />
              <view class="user-info">
                <view class="name-row">
                  <text class="user-name">{{ item.name }}</text>
                  <image v-if="item.isVerified" class="verified-badge"
                    src="https://cos.cnptec.site/static/icon/certification.png" mode="aspectFit" />
                </view>
                <text v-if="item.detail" class="user-detail">{{ item.detail }}</text>
                <text v-if="item.bio" class="user-bio">{{ item.bio }}</text>
              </view>
            </view>
            <view v-if="item.isFollowedBack" class="follow-status follow-status-mutual" @tap.stop>
              <text class="follow-status-icon">✓</text>
              <text class="follow-status-text">互相关注</text>
            </view>
            <view v-else class="follow-btn" :class="{ 'follow-btn-pending': isFollowPending(item.id) }"
              hover-class="follow-btn-hover" @tap.stop="onFollowBack(item)">
              <text class="follow-btn-text">关注</text>
            </view>
          </view>

          <!-- Load more -->
          <view v-if="loadingMore" class="load-more-wrap">
            <text class="load-more-text">加载中...</text>
          </view>
          <view v-else-if="hasMore && hasAny" class="load-more-wrap">
            <text class="load-more-text">上拉加载更多</text>
          </view>
          <view v-else-if="!hasMore && hasAny" class="load-more-wrap">
            <text class="load-more-text load-more-end">没有更多了</text>
          </view>
        </template>
      </view>
    </scroll-view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'
import { getMyFollowersList } from '../../../api/user'
import { toggleUserFollow } from '../../../api/network'

const { statusBarHeight = 0 } = uni.getSystemInfoSync()

const PAGE_SIZE = 20

const searchKeyword = ref('')
const allFollowersList = ref([])
const loading = ref(false)
const loaded = ref(false)
const loadError = ref('')
const refreshing = ref(false)
const loadingMore = ref(false)
const hasMore = ref(true)
const followersList = ref([])
const followPendingMap = ref({})

const hasAny = computed(() => followersList.value.length > 0)

// 搜索相关
const filterFollowersList = () => {
  const keyword = searchKeyword.value.trim().toLowerCase()
  if (!keyword) {
    followersList.value = [...allFollowersList.value]
    return
  }

  followersList.value = allFollowersList.value.filter(item => {
    const name = String(item.name || '').toLowerCase()
    const detail = String(item.detail || '').toLowerCase()
    const bio = String(item.bio || '').toLowerCase()
    return name.includes(keyword) || detail.includes(keyword) || bio.includes(keyword)
  })
}

const onSearchInput = (e) => {
  searchKeyword.value = e.detail.value
  filterFollowersList()
}

const onSearchConfirm = () => {
  filterFollowersList()
}

const onClearSearch = () => {
  searchKeyword.value = ''
  filterFollowersList()
}

const isFollowPending = (userId) => {
  return Boolean(followPendingMap.value[userId])
}

const showToast = (title) => {
  uni.showToast({ title, icon: 'none' })
}

const mapFollowerItem = (item) => {
  const userId = String(item?.user_id || item?.userId || '').trim()
  const name = String(item?.nickname || '').trim() || '未命名用户'
  const avatar = String(item?.avatar_url || '').trim() || 'https://cos.cnptec.site/static/logo.png'
  const industryLabel = String(item?.industry_label || '').trim()
  const companyName = String(item?.company_name || '').trim()
  const jobTitle = String(item?.job_title || '').trim()
  const cityName = String(item?.city_name || '').trim()

  const detailParts = [jobTitle, companyName].filter(Boolean)
  const detail = detailParts.length > 0 ? detailParts.join(' · ') : (industryLabel || cityName || '')

  return {
    id: userId,
    userId,
    name,
    avatar,
    detail,
    bio: String(item?.intro || '').trim(),
    isVerified: Boolean(item?.is_verified),
    isFollowedBack: Boolean(item?.is_followed_back || item?.followed || item?.is_followed)
  }
}

const onBack = () => {
  uni.navigateBack()
}

const loadFollowersList = async (reset = false) => {
  if (loading.value || loadingMore.value) {
    return
  }
  if (!reset && !hasMore.value) {
    return
  }

  if (reset) {
    loading.value = true
    loadError.value = ''
  } else {
    loadingMore.value = true
  }

  try {
    const response = await getMyFollowersList({
      offset: reset ? 0 : followersList.value.length,
      limit: PAGE_SIZE
    })

    const items = Array.isArray(response?.items)
      ? response.items.map(mapFollowerItem)
      : []

    if (reset) {
      allFollowersList.value = items
      followersList.value = items
    } else {
      const existed = new Set(allFollowersList.value.map(item => item.id))
      const newItems = items.filter(item => !existed.has(item.id))
      allFollowersList.value = [...allFollowersList.value, ...newItems]
      followersList.value = [...allFollowersList.value]
    }

    filterFollowersList()

    hasMore.value = Boolean(response?.has_more)
    loaded.value = true
  } catch (error) {
    console.error('Load followers list failed:', error)
    const statusCode = error?.statusCode || 0
    if (statusCode === 401) {
      loadError.value = '请先登录'
    } else if (reset && !hasAny.value) {
      loadError.value = error?.message || '加载失败，请稍后重试'
    } else {
      showToast('加载失败')
    }
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

const onRefresh = async () => {
  refreshing.value = true
  await loadFollowersList(true)
  setTimeout(() => {
    refreshing.value = false
  }, 300)
}

const onRefreshRestore = () => {
  refreshing.value = false
}

const onLoadMore = () => {
  if (!loadingMore.value && hasMore.value && hasAny.value) {
    loadFollowersList(false)
  }
}

const onRetry = () => {
  loadFollowersList(true)
}

const onViewProfile = (item) => {
  const userId = String(item?.userId || item?.id || '').trim()
  if (!userId) {
    return
  }
  uni.navigateTo({
    url: `/pages/me/card/index?userId=${encodeURIComponent(userId)}`
  })
}

const onFollowBack = async (item) => {
  if (!item || isFollowPending(item.id)) {
    return
  }

  const userId = item.id
  followPendingMap.value[userId] = true

  try {
    await toggleUserFollow(userId, true)

    // Update status to mutual
    followersList.value = followersList.value.map(follower => {
      if (follower.id === userId) {
        return { ...follower, isFollowedBack: true }
      }
      return follower
    })

    showToast('关注成功')
  } catch (error) {
    console.error('Follow back failed:', error)
    showToast('操作失败，请稍后重试')
  } finally {
    delete followPendingMap.value[userId]
  }
}

onLoad(() => {
  loadFollowersList(true)
})

onShow(() => {
  // Optionally refresh on show
})
</script>

<style scoped>
.followers-page {
  min-height: 100vh;
  background: #f8f9fa;
}

.page-header {
  position: sticky;
  top: 0;
  z-index: 10;
  background: #ffffff;
  border-bottom: 1rpx solid rgba(15, 23, 42, 0.06);
}

.header-bar {
  height: 88rpx;
  display: flex;
  align-items: center;
  padding: 0 16rpx;
}

.search-bar {
  padding: 16rpx 24rpx;
}

.search-input-wrap {
  position: relative;
  display: flex;
  align-items: center;
  height: 72rpx;
  background: #f8f9fa;
  border-radius: 36rpx;
  padding: 0 24rpx;
}

.search-input {
  flex: 1;
  font-size: 28rpx;
  color: #0f172a;
  line-height: 40rpx;
}

.search-input::placeholder {
  color: #94a3b8;
}

.search-clear {
  width: 40rpx;
  height: 40rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 20rpx;
  background: rgba(15, 23, 42, 0.06);
}

.clear-icon {
  font-size: 32rpx;
  line-height: 1;
  color: #64748b;
}

.back-btn {
  width: 56rpx;
  height: 56rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12rpx;
}

.back-btn-active {
  background: rgba(15, 23, 42, 0.04);
}

.back-icon {
  font-size: 48rpx;
  line-height: 1;
  color: #0f172a;
  font-weight: 300;
}

.header-title {
  flex: 1;
  text-align: center;
  font-size: 32rpx;
  font-weight: 600;
  color: #0f172a;
}

.header-spacer {
  width: 56rpx;
}

.content-scroll {
  height: calc(100vh - 88rpx - 104rpx);
}

.followers-list {
  padding: 24rpx;
}

.skeleton-list {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.skeleton-card {
  background: #ffffff;
  border-radius: 16rpx;
  padding: 28rpx;
  display: flex;
  gap: 20rpx;
}

.skeleton-avatar {
  width: 96rpx;
  height: 96rpx;
  border-radius: 48rpx;
  background: linear-gradient(90deg, #f1f5f9 0%, #e2e8f0 50%, #f1f5f9 100%);
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s ease-in-out infinite;
}

.skeleton-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12rpx;
  padding-top: 8rpx;
}

.skeleton-line {
  height: 24rpx;
  border-radius: 12rpx;
  background: linear-gradient(90deg, #f1f5f9 0%, #e2e8f0 50%, #f1f5f9 100%);
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s ease-in-out infinite;
}

.skeleton-name {
  width: 40%;
  height: 28rpx;
}

.skeleton-detail {
  width: 60%;
}

.skeleton-bio {
  width: 80%;
}

@keyframes skeleton-loading {
  0% {
    background-position: 200% 0;
  }

  100% {
    background-position: -200% 0;
  }
}

.status-wrap {
  padding: 120rpx 60rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.status-icon {
  width: 200rpx;
  height: 200rpx;
  margin-bottom: 24rpx;
}

.status-text {
  font-size: 28rpx;
  color: #64748b;
  text-align: center;
  margin-bottom: 32rpx;
}

.retry-btn {
  height: 68rpx;
  padding: 0 48rpx;
  background: #1a57db;
  border-radius: 34rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.retry-btn-active {
  opacity: 0.8;
}

.retry-btn-text {
  font-size: 28rpx;
  font-weight: 500;
  color: #ffffff;
}

.empty-wrap {
  padding: 120rpx 60rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.empty-icon-image {
  width: 200rpx;
  height: 200rpx;
  margin-bottom: 12rpx;
}

.empty-icon-wrap {
  width: 160rpx;
  height: 160rpx;
  background: linear-gradient(135deg, #eef2ff 0%, #e0e7ff 100%);
  border-radius: 80rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 32rpx;
}

.empty-icon {
  font-size: 80rpx;
  line-height: 1;
}

.empty-title {
  font-size: 32rpx;
  font-weight: 600;
  color: #0f172a;
  margin-bottom: 12rpx;
}

.empty-subtitle {
  font-size: 26rpx;
  color: #64748b;
  text-align: center;
  line-height: 40rpx;
  margin-bottom: 40rpx;
  max-width: 480rpx;
}

.follower-card {
  position: relative;
  background: #ffffff;
  border-radius: 16rpx;
  border: 1rpx solid rgba(15, 23, 42, 0.06);
  padding: 28rpx;
  margin-bottom: 16rpx;
  display: flex;
  align-items: flex-start;
  gap: 20rpx;
  transition: all 0.2s;
}

.follower-card-active {
  background: #fafbfc;
}

.card-main {
  flex: 1;
  display: flex;
  gap: 20rpx;
  min-width: 0;
}

.user-avatar {
  width: 96rpx;
  height: 96rpx;
  border-radius: 48rpx;
  background: linear-gradient(135deg, #e2e8f0 0%, #cbd5e1 100%);
  flex-shrink: 0;
  box-shadow: 0 0 0 3rpx #ffffff, 0 2rpx 8rpx rgba(15, 23, 42, 0.08);
}

.user-info {
  flex: 1;
  min-width: 0;
  padding-top: 4rpx;
}

.name-row {
  display: flex;
  align-items: center;
  gap: 8rpx;
  margin-bottom: 6rpx;
}

.user-name {
  font-size: 32rpx;
  font-weight: 600;
  color: #0f172a;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.verified-badge {
  width: 32rpx;
  height: 32rpx;
  flex-shrink: 0;
}

.user-detail {
  font-size: 26rpx;
  color: #64748b;
  margin-bottom: 8rpx;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-bio {
  font-size: 26rpx;
  color: #94a3b8;
  line-height: 38rpx;
  overflow: hidden;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.follow-status {
  position: absolute;
  top: 28rpx;
  right: 28rpx;
  flex-shrink: 0;
  height: 40rpx;
  padding: 0 20rpx;
  background: rgba(26, 87, 219, 0.08);
  border: 1rpx solid rgba(26, 87, 219, 0.2);
  border-radius: 20rpx;
  display: flex;
  align-items: center;
  gap: 6rpx;
  transition: all 0.2s;
}

.follow-status-mutual {
  background: rgba(34, 197, 94, 0.08);
  border-color: rgba(34, 197, 94, 0.2);
}

.follow-status-icon {
  font-size: 24rpx;
  line-height: 1;
  color: #1a57db;
  font-weight: 600;
}

.follow-status-mutual .follow-status-icon {
  color: #22c55e;
}

.follow-status-text {
  font-size: 24rpx;
  font-weight: 500;
  color: #1a57db;
}

.follow-status-mutual .follow-status-text {
  color: #22c55e;
}

.follow-btn {
  position: absolute;
  top: 28rpx;
  right: 28rpx;
  flex-shrink: 0;
  height: 56rpx;
  padding: 0 28rpx;
  background: #1a57db;
  border-radius: 20rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.follow-btn-hover {
  background: #1443a8;
}

.follow-btn-pending {
  opacity: 0.5;
}

.follow-btn-text {
  font-size: 26rpx;
  font-weight: 500;
  color: #ffffff;
}

.load-more-wrap {
  padding: 32rpx 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.load-more-text {
  font-size: 26rpx;
  color: #94a3b8;
}

.load-more-end {
  color: #cbd5e1;
}

@media (prefers-color-scheme: dark) {
  .followers-page {
    background: #0f172a;
  }

  .page-header {
    background: #1e293b;
    border-bottom-color: rgba(241, 245, 249, 0.06);
  }

  .follower-card {
    background: #1e293b;
    border-color: rgba(241, 245, 249, 0.06);
  }

  .follower-card-active {
    background: #334155;
  }
}
</style>
