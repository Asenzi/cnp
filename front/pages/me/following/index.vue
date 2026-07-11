<template>
  <view class="following-page">
    <view class="page-header" :style="{ paddingTop: statusBarHeight + 'px' }">
      <view class="header-bar">
        <view class="back-btn" hover-class="back-btn-active" @tap="onBack">
          <text class="back-icon">‹</text>
        </view>
        <text class="header-title">我的收藏</text>
        <view class="header-spacer"></view>
      </view>
      <view class="search-bar">
        <view class="search-input-wrap">
          <input class="search-input" type="text" placeholder="搜索已收藏的人脉、资源或圈子" :value="searchKeyword" @input="onSearchInput"
            confirm-type="search" @confirm="onSearchConfirm" />
          <view v-if="searchKeyword" class="search-clear" @tap="onClearSearch">
            <text class="clear-icon">×</text>
          </view>
        </view>
      </view>
      <view class="tabs-bar">
        <view v-for="tab in tabs" :key="tab.key" class="tab-item" :class="{ 'tab-item-active': activeTab === tab.key }"
          @tap="onSwitchTab(tab.key)">
          <text class="tab-label">{{ tab.label }}</text>
        </view>
      </view>
    </view>

    <scroll-view class="content-scroll" scroll-y :show-scrollbar="false" :refresher-enabled="true"
      :refresher-triggered="refreshing" :lower-threshold="120" refresher-background="#f8f9fa"
      @refresherrefresh="onRefresh" @refresherrestore="onRefreshRestore" @scrolltolower="onLoadMore">
      <view class="following-list">
        <template v-if="activeTab === 'contacts'">
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
            <text class="empty-title">{{ searchKeyword ? '未找到相关人脉' : '暂无收藏的人脉' }}</text>
            <text class="empty-subtitle">{{ searchKeyword ? '换个关键词试试吧' : '去人脉库发现更多优质人脉' }}</text>
            <view class="empty-action" hover-class="empty-action-active" @tap="onExplore">
              <text class="empty-action-text">去发现</text>
            </view>
          </view>

          <!-- Following list -->
          <template v-else>
            <view v-for="item in followingList" :key="item.id" class="following-card"
              hover-class="following-card-active" @tap="onViewProfile(item)">
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
              <view class="follow-status" :class="{ 'follow-status-pending': isUnfollowPending(item.id) }"
                hover-class="follow-status-hover" @tap.stop="onUnfollow(item)">
                <text class="follow-status-icon">✓</text>
                <text class="follow-status-text">已收藏</text>
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
        </template>

        <!-- 资源标签页 -->
        <template v-else-if="activeTab === 'resources'">
          <view v-if="resourcesLoading && !currentHasAny" class="skeleton-list">
            <view v-for="i in 3" :key="`skeleton-${i}`" class="skeleton-card">
              <view class="skeleton-avatar"></view>
              <view class="skeleton-info">
                <view class="skeleton-line skeleton-name"></view>
                <view class="skeleton-line skeleton-detail"></view>
                <view class="skeleton-line skeleton-bio"></view>
              </view>
            </view>
          </view>

          <view v-else-if="resourcesLoadError && !currentHasAny" class="status-wrap">
            <image class="status-icon" src="https://cos.cnptec.site/static/icon/data-block.png" mode="aspectFit" />
            <text class="status-text">{{ resourcesLoadError }}</text>
            <view class="retry-btn" hover-class="retry-btn-active" @tap="() => loadResources(true)">
              <text class="retry-btn-text">重新加载</text>
            </view>
          </view>

          <view v-else-if="resourcesLoaded && !currentHasAny" class="empty-wrap">
            <image class="empty-icon-image" src="https://cos.cnptec.site/static/icon/data-block.png" mode="aspectFit" />
            <text class="empty-title">{{ searchKeyword ? '未找到相关资源' : '暂无收藏的资源' }}</text>
            <text class="empty-subtitle">{{ searchKeyword ? '换个关键词试试吧' : '去资源页面发现更多优质内容' }}</text>
          </view>

          <template v-else>
            <ProfilePostCard v-for="item in filteredResourcesItems" :key="item.id" :item="item" :show-interest="true"
              @detail="onTapPostDetail" @interest="onTogglePostInterest" />

            <view v-if="resourcesLoadingMore" class="load-more-wrap">
              <text class="load-more-text">加载中...</text>
            </view>
            <view v-else-if="resourcesHasMore && currentHasAny" class="load-more-wrap">
              <text class="load-more-text">上拉加载更多</text>
            </view>
            <view v-else-if="!resourcesHasMore && currentHasAny" class="load-more-wrap">
              <text class="load-more-text load-more-end">没有更多了</text>
            </view>
          </template>
        </template>

        <!-- 圈子标签页 -->
        <template v-else>
          <view v-if="circlesLoading && !currentHasAny" class="skeleton-list">
            <view v-for="i in 3" :key="`skeleton-${i}`" class="skeleton-card">
              <view class="skeleton-avatar"></view>
              <view class="skeleton-info">
                <view class="skeleton-line skeleton-name"></view>
                <view class="skeleton-line skeleton-detail"></view>
                <view class="skeleton-line skeleton-bio"></view>
              </view>
            </view>
          </view>

          <view v-else-if="circlesLoadError && !currentHasAny" class="status-wrap">
            <image class="status-icon" src="https://cos.cnptec.site/static/icon/data-block.png" mode="aspectFit" />
            <text class="status-text">{{ circlesLoadError }}</text>
            <view class="retry-btn" hover-class="retry-btn-active" @tap="() => loadCircles(true)">
              <text class="retry-btn-text">重新加载</text>
            </view>
          </view>

          <view v-else-if="circlesLoaded && !currentHasAny" class="empty-wrap">
            <image class="empty-icon-image" src="https://cos.cnptec.site/static/icon/data-block.png" mode="aspectFit" />
            <text class="empty-title">{{ searchKeyword ? '未找到相关圈子' : '暂无收藏的圈子' }}</text>
            <text class="empty-subtitle">{{ searchKeyword ? '换个关键词试试吧' : '去圈子页面发现更多优质圈子' }}</text>
          </view>

          <template v-else>
            <DiscoverListCard v-for="item in filteredCirclesItems" :key="item.id" :circle="item"
              @interest="onToggleCircleInterest" />

            <view v-if="circlesLoadingMore" class="load-more-wrap">
              <text class="load-more-text">加载中...</text>
            </view>
            <view v-else-if="circlesHasMore && currentHasAny" class="load-more-wrap">
              <text class="load-more-text">上拉加载更多</text>
            </view>
            <view v-else-if="!circlesHasMore && currentHasAny" class="load-more-wrap">
              <text class="load-more-text load-more-end">没有更多了</text>
            </view>
          </template>
        </template>
      </view>
    </scroll-view>

    <!-- Unfollow confirmation -->
    <view v-if="showUnfollowSheet" class="sheet-mask" @tap="onCancelUnfollow">
      <view class="unfollow-sheet" @tap.stop>
        <view class="sheet-content">
          <image class="sheet-avatar" mode="aspectFill" :src="unfollowTarget?.avatar" />
          <text class="sheet-title">取消收藏 {{ unfollowTarget?.name }}？</text>
          <text class="sheet-desc">取消后将从收藏人脉中移除</text>
        </view>
        <view class="sheet-actions">
          <view class="sheet-btn sheet-btn-cancel" hover-class="sheet-btn-hover" @tap="onCancelUnfollow">
            <text class="sheet-btn-text">取消</text>
          </view>
          <view class="sheet-btn sheet-btn-confirm" hover-class="sheet-btn-hover" @tap="onConfirmUnfollow">
            <text class="sheet-btn-text sheet-btn-text-confirm">取消收藏</text>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'
import { getInterestedUsers, toggleUserInterest } from '../../../api/network'
import { getInterestedResources, toggleResourceInterest } from '../../../api/post'
import { getCollectedCircles, toggleCircleCollection } from '../../../api/circle'
import ProfilePostCard from '../card/components/ProfilePostCard.vue'
import DiscoverListCard from '../../tab/circles/components/DiscoverListCard.vue'
import { mapProfilePostItem } from '../card/modules/profile-home-view-model'

const { statusBarHeight = 0 } = uni.getSystemInfoSync()

const PAGE_SIZE = 20

const tabs = [
  { key: 'contacts', label: '人脉' },
  { key: 'resources', label: '资源' },
  { key: 'circles', label: '圈子' }
]

const activeTab = ref('contacts')
const searchKeyword = ref('')

// 人脉库数据
const allFollowingList = ref([])
const loading = ref(false)
const loaded = ref(false)
const loadError = ref('')
const refreshing = ref(false)
const loadingMore = ref(false)
const hasMore = ref(true)
const followingCursor = ref('')
const followingList = ref([])
const unfollowPendingMap = ref({})
const showUnfollowSheet = ref(false)
const unfollowTarget = ref(null)

// 资源和圈子数据
const resourcesItems = ref([])
const resourcesLoading = ref(false)
const resourcesLoaded = ref(false)
const resourcesLoadError = ref('')
const resourcesLoadingMore = ref(false)
const resourcesHasMore = ref(true)
const resourcesCursor = ref('')

const circlesItems = ref([])
const circlesLoading = ref(false)
const circlesLoaded = ref(false)
const circlesLoadError = ref('')
const circlesLoadingMore = ref(false)
const circlesHasMore = ref(true)
const circlesCursor = ref('')

const hasAny = computed(() => followingList.value.length > 0)

const normalizedSearchKeyword = computed(() => searchKeyword.value.trim().toLowerCase())

const includesKeyword = (values) => {
  const keyword = normalizedSearchKeyword.value
  if (!keyword) return true
  return values.map((value) => String(value || '').toLowerCase()).join(' ').includes(keyword)
}

const filteredResourcesItems = computed(() => resourcesItems.value.filter((item) => includesKeyword([
  item.title,
  item.description,
  item.content,
  item.authorName,
  item.rawPost?.title,
  item.rawPost?.description,
  item.rawPost?.content
])))

const filteredCirclesItems = computed(() => circlesItems.value.filter((item) => includesKeyword([
  item.name,
  item.title,
  item.description,
  item.intro,
  item.ownerName,
  item.industryLabel
])))

const currentItems = computed(() => {
  if (activeTab.value === 'resources') return filteredResourcesItems.value
  if (activeTab.value === 'circles') return filteredCirclesItems.value
  return followingList.value
})

const currentLoading = computed(() => {
  if (activeTab.value === 'resources') return resourcesLoading.value
  if (activeTab.value === 'circles') return circlesLoading.value
  return loading.value
})

const currentLoaded = computed(() => {
  if (activeTab.value === 'resources') return resourcesLoaded.value
  if (activeTab.value === 'circles') return circlesLoaded.value
  return loaded.value
})

const currentLoadError = computed(() => {
  if (activeTab.value === 'resources') return resourcesLoadError.value
  if (activeTab.value === 'circles') return circlesLoadError.value
  return loadError.value
})

const currentHasAny = computed(() => currentItems.value.length > 0)

// 搜索相关
const filterFollowingList = () => {
  const keyword = searchKeyword.value.trim().toLowerCase()
  if (!keyword) {
    followingList.value = [...allFollowingList.value]
    return
  }

  followingList.value = allFollowingList.value.filter(item => {
    const name = String(item.name || '').toLowerCase()
    const detail = String(item.detail || '').toLowerCase()
    const bio = String(item.bio || '').toLowerCase()
    return name.includes(keyword) || detail.includes(keyword) || bio.includes(keyword)
  })
}

const onSearchInput = (e) => {
  searchKeyword.value = e.detail.value
  filterFollowingList()
}

const onSearchConfirm = () => {
  filterFollowingList()
}

const onClearSearch = () => {
  searchKeyword.value = ''
  filterFollowingList()
}

const onSwitchTab = async (tabKey) => {
  if (activeTab.value === tabKey) return

  activeTab.value = tabKey

  if (tabKey === 'resources' && !resourcesLoaded.value) {
    await loadResources(true)
  } else if (tabKey === 'circles' && !circlesLoaded.value) {
    await loadCircles(true)
  }
}

const isUnfollowPending = (userId) => {
  return Boolean(unfollowPendingMap.value[userId])
}

const showToast = (title) => {
  uni.showToast({ title, icon: 'none' })
}

const mapFollowingItem = (item) => {
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
    isVerified: Boolean(item?.is_verified)
  }
}

const onBack = () => {
  uni.navigateBack()
}

const onExplore = () => {
  uni.switchTab({ url: '/pages/tab/discover/index' })
}

const loadFollowingList = async (reset = false) => {
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
    const response = await getInterestedUsers({
      cursor: reset ? '' : followingCursor.value,
      limit: PAGE_SIZE
    })

    const items = Array.isArray(response?.items)
      ? response.items.map(mapFollowingItem)
      : []

    if (reset) {
      allFollowingList.value = items
      followingList.value = items
    } else {
      const existed = new Set(allFollowingList.value.map(item => item.id))
      const newItems = items.filter(item => !existed.has(item.id))
      allFollowingList.value = [...allFollowingList.value, ...newItems]
      followingList.value = [...allFollowingList.value]
    }

    filterFollowingList()

    followingCursor.value = String(response?.next_cursor || '').trim()
    hasMore.value = Boolean(response?.has_more)
    loaded.value = true
  } catch (error) {
    console.error('Load following list failed:', error)
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

const loadResources = async (reset = false) => {
  if (resourcesLoading.value || resourcesLoadingMore.value) return
  if (!reset && (!resourcesHasMore.value || !resourcesCursor.value)) return

  if (reset) {
    resourcesLoading.value = true
    resourcesLoadError.value = ''
  } else {
    resourcesLoadingMore.value = true
  }

  try {
    const data = await getInterestedResources({
      cursor: reset ? '' : resourcesCursor.value,
      limit: PAGE_SIZE
    })

    const incoming = Array.isArray(data?.items) ? data.items.map(mapProfilePostItem) : []

    if (reset) {
      resourcesItems.value = incoming
    } else {
      const existed = new Set(resourcesItems.value.map(item => item.id))
      const appended = incoming.filter(item => !existed.has(item.id))
      resourcesItems.value = [...resourcesItems.value, ...appended]
    }

    resourcesCursor.value = String(data?.next_cursor || '').trim()
    resourcesHasMore.value = Boolean(data?.has_more)
    resourcesLoaded.value = true
  } catch (error) {
    console.error('Load resources failed:', error)
    const message = error?.message || '加载失败，请稍后重试'
    if (reset && resourcesItems.value.length === 0) {
      resourcesLoadError.value = message
    } else {
      showToast(message)
    }
  } finally {
    resourcesLoading.value = false
    resourcesLoadingMore.value = false
  }
}

const loadCircles = async (reset = false) => {
  if (circlesLoading.value || circlesLoadingMore.value) return
  if (!reset && (!circlesHasMore.value || !circlesCursor.value)) return

  if (reset) {
    circlesLoading.value = true
    circlesLoadError.value = ''
  } else {
    circlesLoadingMore.value = true
  }

  try {
    const data = await getCollectedCircles({
      cursor: reset ? '' : circlesCursor.value,
      limit: PAGE_SIZE
    })

    const incoming = Array.isArray(data?.items) ? data.items : []

    if (reset) {
      circlesItems.value = incoming
    } else {
      const existed = new Set(circlesItems.value.map(item => item.id))
      const appended = incoming.filter(item => !existed.has(item.id))
      circlesItems.value = [...circlesItems.value, ...appended]
    }

    circlesCursor.value = String(data?.next_cursor || '').trim()
    circlesHasMore.value = Boolean(data?.has_more)
    circlesLoaded.value = true
  } catch (error) {
    console.error('Load circles failed:', error)
    const message = error?.message || '加载失败，请稍后重试'
    if (reset && circlesItems.value.length === 0) {
      circlesLoadError.value = message
    } else {
      showToast(message)
    }
  } finally {
    circlesLoading.value = false
    circlesLoadingMore.value = false
  }
}

const onRefresh = async () => {
  refreshing.value = true
  if (activeTab.value === 'resources') {
    await loadResources(true)
  } else if (activeTab.value === 'circles') {
    await loadCircles(true)
  } else {
    await loadFollowingList(true)
  }
  setTimeout(() => {
    refreshing.value = false
  }, 300)
}

const onRefreshRestore = () => {
  refreshing.value = false
}

const onLoadMore = () => {
  if (activeTab.value === 'resources') {
    if (!resourcesLoadingMore.value && resourcesHasMore.value && resourcesItems.value.length > 0) {
      loadResources(false)
    }
  } else if (activeTab.value === 'circles') {
    if (!circlesLoadingMore.value && circlesHasMore.value && circlesItems.value.length > 0) {
      loadCircles(false)
    }
  } else {
    if (!loadingMore.value && hasMore.value && hasAny.value) {
      loadFollowingList(false)
    }
  }
}

const onRetry = () => {
  if (activeTab.value === 'resources') {
    loadResources(true)
  } else if (activeTab.value === 'circles') {
    loadCircles(true)
  } else {
    loadFollowingList(true)
  }
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

const onUnfollow = (item) => {
  unfollowTarget.value = item
  showUnfollowSheet.value = true
}

const onCancelUnfollow = () => {
  showUnfollowSheet.value = false
  unfollowTarget.value = null
}

const onConfirmUnfollow = async () => {
  if (!unfollowTarget.value) {
    return
  }

  const userId = unfollowTarget.value.id
  unfollowPendingMap.value[userId] = true
  showUnfollowSheet.value = false

  try {
    await toggleUserInterest(userId, false)

    allFollowingList.value = allFollowingList.value.filter(item => item.id !== userId)
    followingList.value = followingList.value.filter(item => item.id !== userId)
    showToast('已取消收藏')
  } catch (error) {
    console.error('Cancel network collection failed:', error)
    showToast('操作失败，请稍后重试')
  } finally {
    delete unfollowPendingMap.value[userId]
    unfollowTarget.value = null
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
  if (!postCode) return

  const targetIndex = resourcesItems.value.findIndex(item =>
    (item.postCode || item.rawPost?.post_code || item.post_code) === postCode
  )

  if (targetIndex >= 0) {
    const removedItem = resourcesItems.value[targetIndex]
    resourcesItems.value.splice(targetIndex, 1)

    try {
      await toggleResourceInterest(postCode, false)
      showToast('已取消感兴趣')
    } catch (err) {
      resourcesItems.value.splice(targetIndex, 0, removedItem)
      const message = err?.message || '操作失败，请稍后重试'
      showToast(message)
    }
  }
}

const onToggleCircleInterest = async (circle) => {
  const circleCode = String(circle?.circleCode || '').trim()
  if (!circleCode) return

  const targetIndex = circlesItems.value.findIndex(item => item.circleCode === circleCode)

  if (targetIndex >= 0) {
    const removedItem = circlesItems.value[targetIndex]
    circlesItems.value.splice(targetIndex, 1)

    try {
      await toggleCircleCollection(circleCode, false)
      showToast('已取消收藏')
    } catch (err) {
      circlesItems.value.splice(targetIndex, 0, removedItem)
      const message = err?.message || '操作失败，请稍后重试'
      showToast(message)
    }
  }
}

onLoad(() => {
  loadFollowingList(true)
})

onShow(() => {
  // Optionally refresh on show
})
</script>

<style scoped>
.following-page {
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

.tabs-bar {
  display: flex;
  align-items: center;
  gap: 32rpx;
  padding: 0 24rpx 16rpx;
}

.tab-item {
  position: relative;
  padding: 8rpx 0;
  cursor: pointer;
}

.tab-label {
  font-size: 28rpx;
  color: #64748b;
  font-weight: 500;
  transition: all 0.2s;
}

.tab-item-active .tab-label {
  color: #1a57db;
  font-weight: 600;
}

.tab-item-active::after {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  height: 4rpx;
  background: #1a57db;
  border-radius: 2rpx;
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
  color: #1e293b;
  font-weight: 300;
}

.header-title {
  flex: 1;
  text-align: center;
  font-size: 32rpx;
  font-weight: 600;
  color: #0f172a;
  letter-spacing: -0.01em;
}

.header-spacer {
  width: 56rpx;
}

.content-scroll {
  height: calc(100vh - 88rpx - 104rpx - 68rpx);
}

.following-list {
  padding: 24rpx 32rpx calc(24rpx + env(safe-area-inset-bottom));
}

/* Skeleton */
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
  border: 1rpx solid rgba(15, 23, 42, 0.06);
}

.skeleton-avatar {
  width: 96rpx;
  height: 96rpx;
  border-radius: 48rpx;
  background: linear-gradient(90deg, #f1f5f9 25%, #e2e8f0 50%, #f1f5f9 75%);
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s infinite;
  flex-shrink: 0;
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
  border-radius: 4rpx;
  background: linear-gradient(90deg, #f1f5f9 25%, #e2e8f0 50%, #f1f5f9 75%);
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s infinite;
}

.skeleton-name {
  width: 160rpx;
  height: 28rpx;
}

.skeleton-detail {
  width: 240rpx;
}

.skeleton-bio {
  width: 100%;
  margin-top: 4rpx;
}

@keyframes skeleton-loading {
  0% {
    background-position: 200% 0;
  }

  100% {
    background-position: -200% 0;
  }
}

/* Status states */
.status-wrap {
  padding: 120rpx 48rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24rpx;
}

.status-icon {
  width: 200rpx;
  height: 200rpx;
  opacity: 0.4;
}

.status-text {
  font-size: 28rpx;
  color: #64748b;
  text-align: center;
}

.retry-btn {
  margin-top: 16rpx;
  padding: 0 40rpx;
  height: 72rpx;
  background: #1a57db;
  border-radius: 36rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.retry-btn-active {
  opacity: 0.9;
}

.retry-btn-text {
  font-size: 28rpx;
  font-weight: 500;
  color: #ffffff;
}

/* Empty state */
.empty-wrap {
  padding: 120rpx 48rpx;
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
  line-height: 38rpx;
  margin-bottom: 40rpx;
}

.empty-action {
  padding: 0 48rpx;
  height: 80rpx;
  background: #1a57db;
  border-radius: 40rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.empty-action-active {
  opacity: 0.9;
}

.empty-action-text {
  font-size: 28rpx;
  font-weight: 500;
  color: #ffffff;
}

/* Following cards */
.following-card {
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

.following-card-active {
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
  letter-spacing: -0.01em;
}

.verified-badge {
  width: 32rpx;
  height: 32rpx;
  flex-shrink: 0;
}

.user-detail {
  display: block;
  font-size: 26rpx;
  color: #64748b;
  line-height: 36rpx;
  margin-bottom: 8rpx;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.user-bio {
  display: block;
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
  padding: 0 10rpx;
  background: rgba(26, 87, 219, 0.08);
  /* border: 1rpx solid rgba(26, 87, 219, 0.2); */
  border-radius: 10rpx;
  display: flex;
  align-items: center;
  gap: 6rpx;
  transition: all 0.2s;
}

.follow-status-hover {
  background: rgba(239, 68, 68, 0.08);
  border-color: rgba(239, 68, 68, 0.2);
}

.follow-status-pending {
  opacity: 0.5;
}

.follow-status-icon {
  font-size: 24rpx;
  line-height: 1;
  color: #1a57db;
  font-weight: 600;
}

.follow-status-hover .follow-status-icon {
  color: #ef4444;
}

.follow-status-text {
  font-size: 24rpx;
  font-weight: 500;
  color: #1a57db;
}

.follow-status-hover .follow-status-text {
  color: #ef4444;
}

/* Load more */
.load-more-wrap {
  padding: 32rpx 0 16rpx;
  text-align: center;
}

.load-more-text {
  font-size: 24rpx;
  color: #94a3b8;
}

.load-more-end {
  color: #cbd5e1;
}

/* Unfollow sheet */
.sheet-mask {
  position: fixed;
  left: 0;
  right: 0;
  top: 0;
  bottom: 0;
  background: rgba(15, 23, 42, 0.5);
  z-index: 100;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  animation: sheet-mask-in 0.25s ease-out;
}

@keyframes sheet-mask-in {
  from {
    opacity: 0;
  }

  to {
    opacity: 1;
  }
}

.unfollow-sheet {
  width: 100%;
  background: #ffffff;
  border-radius: 24rpx 24rpx 0 0;
  padding: 48rpx 32rpx calc(32rpx + env(safe-area-inset-bottom));
  animation: sheet-slide-up 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes sheet-slide-up {
  from {
    transform: translateY(100%);
  }

  to {
    transform: translateY(0);
  }
}

.sheet-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-bottom: 40rpx;
}

.sheet-avatar {
  width: 96rpx;
  height: 96rpx;
  border-radius: 48rpx;
  background: #f1f5f9;
  margin-bottom: 24rpx;
}

.sheet-title {
  font-size: 32rpx;
  font-weight: 600;
  color: #0f172a;
  margin-bottom: 12rpx;
  text-align: center;
}

.sheet-desc {
  font-size: 26rpx;
  color: #64748b;
  text-align: center;
  line-height: 38rpx;
}

.sheet-actions {
  display: flex;
  gap: 16rpx;
}

.sheet-btn {
  flex: 1;
  height: 88rpx;
  border-radius: 16rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: opacity 0.2s;
}

.sheet-btn-hover {
  opacity: 0.8;
}

.sheet-btn-cancel {
  background: #f1f5f9;
}

.sheet-btn-confirm {
  background: #ef4444;
}

.sheet-btn-text {
  font-size: 28rpx;
  font-weight: 500;
  color: #475569;
}

.sheet-btn-text-confirm {
  color: #ffffff;
}

@media (prefers-color-scheme: dark) {
  .following-page {
    background: #0f172a;
  }

  .page-header {
    background: #1e293b;
    border-bottom-color: rgba(241, 245, 249, 0.06);
  }

  .back-btn-active {
    background: rgba(241, 245, 249, 0.08);
  }

  .back-icon,
  .header-title {
    color: #f1f5f9;
  }

  .following-card {
    background: #1e293b;
    border-color: rgba(241, 245, 249, 0.06);
  }

  .following-card-active {
    background: #334155;
  }

  .user-name {
    color: #f1f5f9;
  }

  .user-detail {
    color: #94a3b8;
  }

  .user-bio {
    color: #64748b;
  }

  .empty-icon-wrap {
    background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%);
  }

  .empty-title {
    color: #f1f5f9;
  }

  .unfollow-sheet {
    background: #1e293b;
  }

  .sheet-title {
    color: #f1f5f9;
  }

  .sheet-btn-cancel {
    background: #334155;
  }

  .sheet-btn-text {
    color: #cbd5e1;
  }

  .tab-label {
    color: #94a3b8;
  }

  .tab-item-active .tab-label {
    color: #3b82f6;
  }

  .tab-item-active::after {
    background: #3b82f6;
  }
}
</style>
