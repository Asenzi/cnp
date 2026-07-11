<template>
  <view class="messages-page">
    <!-- 顶部导航 -->
    <view class="header" :style="{ paddingTop: statusBarHeight + 'px' }">
      <view class="header-content">
        <view class="back-btn" @tap="goBack">
          <text class="back-icon">‹</text>
        </view>
        <text class="title">消息通知</text>
      </view>
    </view>

    <!-- 选项卡 -->
    <view class="tabs-bar">
      <view v-for="tab in tabs" :key="tab.key" class="tab-item" :class="{ 'tab-active': activeTab === tab.key }"
        @tap="switchTab(tab.key)">
        <text class="tab-label">{{ tab.label }}</text>
        <view v-if="tab.badge > 0" class="tab-badge">
          <text class="badge-text">{{ tab.badge > 99 ? '99+' : tab.badge }}</text>
        </view>
      </view>
    </view>

    <!-- 内容区域 -->
    <scroll-view class="content-scroll" scroll-y :show-scrollbar="false">
      <!-- 加载中 -->
      <view v-if="loading" class="loading-wrap">
        <text class="loading-text">加载中...</text>
      </view>

      <!-- 空状态 -->
      <view v-else-if="currentList.length === 0" class="empty-state">
        <image class="empty-icon-image" src="https://cos.cnptec.site/static/icon/data-block.png" mode="aspectFit" />
        <text class="empty-title">暂无{{ currentTabLabel }}</text>
        <text class="empty-hint">{{ emptyHint }}</text>
      </view>

      <!-- 消息列表 -->
      <view v-else class="message-list">
        <!-- 系统通知卡片 -->
        <view v-for="item in currentList" :key="item.id" class="notice-card" :class="[
          { 'card-read': item.read },
          `notice-card--${item.noticeKind}`
        ]" @tap="handleItemTap(item)">
          <!-- 头像或图标 -->
          <view v-if="item.avatarUrl" class="notice-avatar-wrap">
            <image class="notice-avatar" mode="aspectFill" :src="item.avatarUrl" />
          </view>
          <view v-else class="notice-icon">
            <image class="icon-img" mode="aspectFit" :src="getTypeIcon(item.type)" />
          </view>

          <!-- 内容 -->
          <view class="notice-content">
            <view class="notice-header">
              <text class="notice-title">{{ item.title }}</text>
              <text class="notice-time">{{ item.timeText }}</text>
            </view>
            <text class="notice-text">{{ item.content }}</text>
          </view>

          <!-- 未读标记 -->
          <view v-if="!item.read" class="unread-dot"></view>
        </view>
      </view>
    </scroll-view>
  </view>
</template>

<script setup>
import { computed, onUnmounted, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import {
  getCollectionNotifications,
  getSystemNotifications,
  markNotificationAsRead,
  markNotificationsAsRead
} from '../../../api/notification'
import { connectRealtimeSocket, subscribeRealtime } from '../../../utils/realtime'

// 获取状态栏高度
const { statusBarHeight = 0 } = uni.getSystemInfoSync()

// 状态
const loading = ref(false)
const activeTab = ref('collection')
const collectionList = ref([])
const systemList = ref([])
let realtimeRefreshTimer = null

// 选项卡配置
const tabs = computed(() => [
  {
    key: 'collection',
    label: '收藏通知',
    badge: collectionList.value.filter(item => !item.read).length
  },
  {
    key: 'system',
    label: '系统通知',
    badge: systemList.value.filter(item => !item.read).length
  }
])

// 当前选项卡数据
const currentList = computed(() => {
  if (activeTab.value === 'collection') return collectionList.value
  return systemList.value
})

const currentTabLabel = computed(() => {
  const tab = tabs.value.find(t => t.key === activeTab.value)
  return tab ? tab.label : ''
})

const emptyIcon = computed(() => {
  return activeTab.value === 'collection' ? 'https://cos.cnptec.site/static/icon/interested.png' : 'https://cos.cnptec.site/static/icon/block.png'
})
const emptyHint = computed(() => {
  if (activeTab.value === 'collection') {
    return '别人收藏你的人脉、资源或圈子后会在这里显示'
  }
  return '系统公告和重要通知会在这里显示'
})

// 图标映射
const typeIcons = {
  circle: 'https://cos.cnptec.site/static/icon/mennber.png',
  network: 'https://cos.cnptec.site/static/icon/interested.png',
  collection: 'https://cos.cnptec.site/static/icon/interested.png',
  system: 'https://cos.cnptec.site/static/icon/block.png'
}

const getTypeIcon = (type) => {
  return typeIcons[type] || typeIcons.system
}

// 格式化时间
const formatTime = (timestamp) => {
  const now = Date.now()
  const diff = now - timestamp
  const minute = 60 * 1000
  const hour = 60 * minute
  const day = 24 * hour

  if (diff < minute) {
    return '刚刚'
  } else if (diff < hour) {
    return `${Math.floor(diff / minute)}分钟前`
  } else if (diff < day) {
    return `${Math.floor(diff / hour)}小时前`
  } else if (diff < 2 * day) {
    return '昨天'
  } else if (diff < 7 * day) {
    return `${Math.floor(diff / day)}天前`
  } else {
    const date = new Date(timestamp)
    return `${date.getMonth() + 1}月${date.getDate()}日`
  }
}

const mapNotificationItem = (item, fallbackType, fallbackTitle) => ({
  id: String(item.id || item.notification_id || ''),
  type: String(item.type || fallbackType).trim(),
  title: String(item.title || fallbackTitle).trim(),
  content: String(item.content || item.message || '').trim(),
  linkType: String(item.link_type || '').trim(),
  linkId: String(item.link_id || '').trim(),
  noticeKind: ['user', 'resource', 'circle'].includes(String(item.link_type || '').trim())
    ? String(item.link_type || '').trim()
    : 'system',
  timestamp: new Date(item.created_at).getTime(),
  timeText: formatTime(new Date(item.created_at).getTime()),
  read: Boolean(item.is_read || item.read),
  avatarUrl: String(item.avatar_url || '').trim() || null,
  relatedUserId: String(item.related_user_id || '').trim() || null
})

// 加载人脉、资源和圈子收藏通知
const loadCollectionNotifications = async () => {
  try {
    const data = await getCollectionNotifications({ limit: 50 })
    const items = Array.isArray(data?.items) ? data.items : []
    collectionList.value = items.map(item => mapNotificationItem(item, 'collection', '收藏通知'))
  } catch (err) {
    console.error('加载收藏通知失败:', err)
    collectionList.value = []
  }
}

// 加载系统通知
const loadSystemNotifications = async () => {
  try {
    const data = await getSystemNotifications({ limit: 50 })
    const items = Array.isArray(data?.items) ? data.items : []

    systemList.value = items.map(item => mapNotificationItem(item, 'system', '系统通知'))
  } catch (err) {
    console.error('加载系统通知失败:', err)
    systemList.value = []
  }
}

// 切换选项卡
const getTabList = (key) => {
  if (key === 'collection') return collectionList.value
  if (key === 'system') return systemList.value
  return []
}

const markTabAsRead = async (key) => {
  const list = getTabList(key)
  const unreadItems = list.filter(item => !item.read)
  if (unreadItems.length === 0) return

  unreadItems.forEach(item => {
    item.read = true
  })

  try {
    await markNotificationsAsRead(key)
  } catch (err) {
    console.error(`标记${key}通知已读失败:`, err)
    unreadItems.forEach(item => {
      item.read = false
    })
  }
}

const switchTab = async (key) => {
  activeTab.value = key
  await markTabAsRead(key)
}

// 加载数据
const loadData = async () => {
  loading.value = true
  try {
    await Promise.all([
      loadCollectionNotifications(),
      loadSystemNotifications()
    ])
    await markTabAsRead(activeTab.value)
  } catch (err) {
    uni.showToast({
      title: err?.message || '加载失败',
      icon: 'none'
    })
  } finally {
    loading.value = false
  }
}

const scheduleRealtimeRefresh = () => {
  if (realtimeRefreshTimer) return
  realtimeRefreshTimer = setTimeout(async () => {
    realtimeRefreshTimer = null
    await Promise.all([
      loadCollectionNotifications(),
      loadSystemNotifications()
    ])
    await markTabAsRead(activeTab.value)
  }, 250)
}

const unsubscribeRealtime = subscribeRealtime((payload) => {
  if (payload?.event === 'notification.changed') {
    scheduleRealtimeRefresh()
  }
})

// 点击通知
const handleItemTap = async (item) => {
  if (!item.read && item.id) {
    try {
      await markNotificationAsRead(item.id)
      item.read = true
    } catch (err) {
      console.error('标记已读失败:', err)
    }
  }

  if (activeTab.value === 'collection' && item.relatedUserId) {
    uni.navigateTo({
      url: `/pages/me/card/index?userId=${encodeURIComponent(item.relatedUserId)}`
    })
    return
  }

  if (item.linkType === 'user' && item.linkId) {
    uni.navigateTo({
      url: `/pages/me/card/index?userId=${encodeURIComponent(item.linkId)}`
    })
    return
  }

  if (item.linkType === 'circle' && item.linkId) {
    uni.navigateTo({
      url: `/pages/circles/detail/index?code=${encodeURIComponent(item.linkId)}`
    })
    return
  }

  if (item.linkType === 'resource' && item.linkId) {
    uni.navigateTo({
      url: `/pages/resources/detail/index?postCode=${encodeURIComponent(item.linkId)}`
    })
  }
}

const goBack = () => {
  uni.navigateBack({
    delta: 1
  })
}

onShow(() => {
  connectRealtimeSocket()
  loadData()
})

onUnmounted(() => {
  unsubscribeRealtime()
  if (realtimeRefreshTimer) {
    clearTimeout(realtimeRefreshTimer)
    realtimeRefreshTimer = null
  }
})
</script>

<style scoped>
.messages-page {
  min-height: 100vh;
  background: #f6f6f8;
  display: flex;
  flex-direction: column;
}

/* 椤堕儴瀵艰埅 */
.header {
  background: #ffffff;
  border-bottom: 1rpx solid #e7ecf3;
}

.header-content {
  position: relative;
  height: 88rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.back-btn {
  position: absolute;
  left: 0;
  top: 0;
  width: 88rpx;
  height: 88rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
}

.back-icon {
  font-size: 40rpx;
  font-weight: 300;
  color: #172033;
  line-height: 1;
}

.title {
  font-size: 34rpx;
  font-weight: 600;
  color: #172033;
}

/* 閫夐」鍗?*/
.tabs-bar {
  display: flex;
  background: #ffffff;
  padding: 0 32rpx;
}

.tab-item {
  position: relative;
  flex: 1;
  height: 96rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8rpx;
}

.tab-label {
  font-size: 28rpx;
  color: #66758a;
  transition: all 0.2s;
}

.tab-active .tab-label {
  font-size: 30rpx;
  font-weight: 600;
  color: #172033;
}

.tab-active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 56rpx;
  height: 6rpx;
  border-radius: 3rpx;
  background: #2563eb;
}

.tab-badge {
  min-width: 32rpx;
  height: 32rpx;
  padding: 0 8rpx;
  border-radius: 16rpx;
  background: #ef4444;
  display: flex;
  align-items: center;
  justify-content: center;
}

.badge-text {
  font-size: 20rpx;
  font-weight: 600;
  color: #ffffff;
  line-height: 1;
  transform: scale(0.85);
}

/* 内容区域 */
.content-scroll {
  flex: 1;
  height: 0;
}

.loading-wrap {
  padding: 120rpx 32rpx;
  text-align: center;
}

.loading-text {
  font-size: 26rpx;
  color: #94a3b8;
}

/* 空状态 */
.empty-state {
  padding: 160rpx 32rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.empty-icon-image {
  width: 200rpx;
  height: 200rpx;
  margin-bottom: 32rpx;
}

.empty-title {
  font-size: 28rpx;
  font-weight: 500;
  color: #475569;
  margin-bottom: 12rpx;
}

.empty-hint {
  font-size: 24rpx;
  color: #94a3b8;
}

/* 消息列表 */
.message-list {
  padding: 24rpx 24rpx calc(24rpx + env(safe-area-inset-bottom));
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

/* 系统通知卡片 */
.notice-card {
  position: relative;
  display: flex;
  gap: 20rpx;
  padding: 24rpx;
  background: #f1f5f9;
  border-radius: 16rpx;
  /* border: 1rpx solid transparent; */
  transition: all 0.2s;
}

.notice-card:active {
  background: #e2e8f0;
}

.notice-card.card-read {
  opacity: 0.7;
}

.notice-card:not(.card-read) {
  background: #f1f5f9;
  border-color: #e7ecf3;
  box-shadow: 0 2rpx 12rpx rgba(15, 23, 42, 0.04);
}

.notice-card--user,
.notice-card--user:not(.card-read) {
  background: #e8f2ff;
  border-color: #cfe2fb;
}

.notice-card--resource,
.notice-card--resource:not(.card-read) {
  background: #fff0dc;
  border-color: #f5dcb9;
}

.notice-card--circle,
.notice-card--circle:not(.card-read) {
  background: #f0e8ff;
  border-color: #ddcff8;
}

.notice-card--user:active {
  background: #dcecff;
}

.notice-card--resource:active {
  background: #ffe6c5;
}

.notice-card--circle:active {
  background: #e6d9ff;
}

.notice-card--user .notice-icon {
  background: rgba(59, 130, 246, 0.09);
}

.notice-card--resource .notice-icon {
  background: rgba(245, 158, 11, 0.09);
}

.notice-card--circle .notice-icon {
  background: rgba(139, 92, 246, 0.09);
}

.notice-avatar-wrap {
  width: 88rpx;
  height: 88rpx;
  flex-shrink: 0;
}

.notice-avatar {
  width: 88rpx;
  height: 88rpx;
  border-radius: 44rpx;
  background: #e2e8f0;
}

.notice-icon {
  width: 88rpx;
  height: 88rpx;
  border-radius: 44rpx;
  background: rgba(37, 99, 235, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.notice-icon .icon-img {
  width: 44rpx;
  height: 44rpx;
  opacity: 0.6;
}

.notice-content {
  flex: 1;
  min-width: 0;
}

.notice-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 16rpx;
  margin-bottom: 8rpx;
}

.notice-title {
  flex: 1;
  font-size: 28rpx;
  font-weight: 600;
  color: #172033;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.notice-time {
  font-size: 22rpx;
  color: #94a3b8;
  flex-shrink: 0;
}

.notice-text {
  display: block;
  font-size: 26rpx;
  line-height: 38rpx;
  color: #475569;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

/* 深色模式 */
@media (prefers-color-scheme: dark) {
  .messages-page {
    background: #0f172a;
  }

  .header {
    background: #1e293b;
    border-bottom-color: #334155;
  }

  .back-icon {
    color: #f8fafc;
  }

  .title {
    color: #f8fafc;
  }

  .tabs-bar {
    background: #1e293b;
  }

  .tab-label {
    color: #94a3b8;
  }

  .tab-active .tab-label {
    color: #f8fafc;
  }

  .tab-active::after {
    background: #3b82f6;
  }

  .loading-text {
    color: #64748b;
  }

  .empty-title {
    color: #cbd5e1;
  }

  .empty-hint {
    color: #64748b;
  }

  /* 系统通知卡片 - 深色模式 */

  .notice-card {
    background: rgba(30, 41, 59, 0.5);
  }

  .notice-card:active {
    background: #1e293b;
  }

  .notice-card:not(.card-read) {
    background: #1e293b;
    border-color: #334155;
    box-shadow: none;
  }

  .notice-card--user,
  .notice-card--user:not(.card-read) {
    background: rgba(30, 58, 100, 0.38);
    border-color: rgba(96, 165, 250, 0.14);
  }

  .notice-card--resource,
  .notice-card--resource:not(.card-read) {
    background: rgba(82, 55, 24, 0.38);
    border-color: rgba(251, 191, 36, 0.14);
  }

  .notice-card--circle,
  .notice-card--circle:not(.card-read) {
    background: rgba(62, 44, 92, 0.38);
    border-color: rgba(167, 139, 250, 0.14);
  }

  .notice-card--user:active {
    background: rgba(30, 58, 100, 0.58);
  }

  .notice-card--resource:active {
    background: rgba(82, 55, 24, 0.58);
  }

  .notice-card--circle:active {
    background: rgba(62, 44, 92, 0.58);
  }

  .notice-icon {
    background: rgba(59, 130, 246, 0.15);
  }

  .notice-title {
    color: #f8fafc;
  }

  .notice-time {
    color: #64748b;
  }

  .notice-text {
    color: #cbd5e1;
  }
}
</style>
