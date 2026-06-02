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
      <view
        v-for="tab in tabs"
        :key="tab.key"
        class="tab-item"
        :class="{ 'tab-active': activeTab === tab.key }"
        @tap="switchTab(tab.key)"
      >
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
        <view class="empty-icon">
          <image class="icon-img" mode="aspectFit" :src="emptyIcon" />
        </view>
        <text class="empty-title">暂无{{ currentTabLabel }}</text>
        <text class="empty-hint">{{ emptyHint }}</text>
      </view>

      <!-- 消息列表 -->
      <view v-else class="message-list">
        <!-- 圈子申请卡片 -->
        <template v-if="activeTab === 'circle'">
          <view
            v-for="item in currentList"
            :key="item.id"
            class="apply-card"
            :class="{ 'card-read': item.read }"
          >
            <view class="card-main" @tap="viewApplicantProfile(item)">
              <!-- 申请人头像 -->
              <image class="applicant-avatar" mode="aspectFill" :src="item.avatar" />

              <!-- 申请信息 -->
              <view class="apply-info">
                <view class="info-top">
                  <text class="applicant-name">{{ item.applicantName }}</text>
                  <text class="apply-time">{{ item.timeText }}</text>
                </view>
                <text class="apply-text">{{ item.content }}</text>
                <view v-if="item.message" class="apply-message">
                  <text class="message-label">申请留言：</text>
                  <text class="message-text">{{ item.message }}</text>
                </view>
              </view>

              <!-- 未读标记 -->
              <view v-if="!item.read" class="unread-dot"></view>
            </view>

            <!-- 操作按钮 -->
            <view v-if="item.status === 'pending'" class="card-actions">
              <button class="action-btn btn-reject" hover-class="btn-reject-active" @tap.stop="handleReject(item)">
                拒绝
              </button>
              <button class="action-btn btn-approve" hover-class="btn-approve-active" @tap.stop="handleApprove(item)">
                通过
              </button>
            </view>

            <!-- 已处理状态 -->
            <view v-else class="card-status">
              <text class="status-text" :class="item.status === 'approved' ? 'status-approved' : 'status-rejected'">
                {{ item.status === 'approved' ? '已通过' : '已拒绝' }}
              </text>
            </view>
          </view>
        </template>

        <!-- 系统通知卡片 -->
        <template v-else>
          <view
            v-for="item in currentList"
            :key="item.id"
            class="notice-card"
            :class="{ 'card-read': item.read }"
            @tap="handleItemTap(item)"
          >
            <!-- 图标 -->
            <view class="notice-icon">
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
        </template>
      </view>
    </scroll-view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { getCircleJoinRequests, reviewCircleJoinRequest } from '../../../api/circle'
import { getSystemNotifications, markNotificationAsRead } from '../../../api/notification'

const { statusBarHeight = 0 } = uni.getSystemInfoSync()

// 状态
const loading = ref(false)
const activeTab = ref('circle')
const circleList = ref([])
const systemList = ref([])

// 选项卡配置
const tabs = computed(() => [
  {
    key: 'circle',
    label: '圈子通知',
    badge: circleList.value.filter(item => !item.read).length
  },
  {
    key: 'system',
    label: '系统通知',
    badge: systemList.value.filter(item => !item.read).length
  }
])

// 当前选项卡数据
const currentList = computed(() => {
  return activeTab.value === 'circle' ? circleList.value : systemList.value
})

const currentTabLabel = computed(() => {
  const tab = tabs.value.find(t => t.key === activeTab.value)
  return tab ? tab.label : ''
})

const emptyIcon = computed(() => {
  return activeTab.value === 'circle' ? '/static/icon/mennber.png' : '/static/icon/block.png'
})

const emptyHint = computed(() => {
  return activeTab.value === 'circle'
    ? '圈子加入申请和审核结果会在这里显示'
    : '系统公告和重要通知会在这里显示'
})

// 图标映射
const typeIcons = {
  circle: '/static/icon/mennber.png',
  system: '/static/icon/block.png'
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

// 切换选项卡
const switchTab = (key) => {
  activeTab.value = key
}

// 加载数据
const loadData = async () => {
  loading.value = true
  try {
    // 并行加载圈子申请和系统通知
    await Promise.all([
      loadCircleRequests(),
      loadSystemNotifications()
    ])
  } catch (err) {
    uni.showToast({
      title: err?.message || '加载失败',
      icon: 'none'
    })
  } finally {
    loading.value = false
  }
}

// 加载圈子申请
const loadCircleRequests = async () => {
  try {
    const data = await getCircleJoinRequests({ limit: 50 })
    const items = Array.isArray(data?.items) ? data.items : []

    circleList.value = items.map(item => ({
      id: String(item.id || item.request_id || ''),
      type: 'circle',
      applicantName: String(item.user?.nickname || item.applicant_name || '未知用户').trim(),
      content: `申请加入你的圈子"${String(item.circle?.name || item.circle_name || '').trim()}"`,
      message: String(item.message || '').trim(),
      circleName: String(item.circle?.name || item.circle_name || '').trim(),
      circleCode: String(item.circle?.circle_code || item.circle_code || '').trim(),
      timestamp: new Date(item.created_at).getTime(),
      timeText: formatTime(new Date(item.created_at).getTime()),
      read: item.status !== 'pending',
      status: String(item.status || 'pending').trim(),
      avatar: String(item.user?.avatar_url || item.applicant_avatar || '/static/logo.png').trim(),
      applicantId: String(item.user?.user_id || item.user_pk || '').trim()
    }))
  } catch (err) {
    console.error('加载圈子申请失败:', err)
    circleList.value = []
  }
}

// 加载系统通知
const loadSystemNotifications = async () => {
  try {
    const data = await getSystemNotifications({ limit: 50 })
    const items = Array.isArray(data?.items) ? data.items : []

    systemList.value = items.map(item => ({
      id: String(item.id || item.notification_id || ''),
      type: 'system',
      title: String(item.title || '系统通知').trim(),
      content: String(item.content || item.message || '').trim(),
      timestamp: new Date(item.created_at).getTime(),
      timeText: formatTime(new Date(item.created_at).getTime()),
      read: Boolean(item.is_read || item.read)
    }))
  } catch (err) {
    console.error('加载系统通知失败:', err)
    systemList.value = []
  }
}

// 查看申请人资料
const viewApplicantProfile = (item) => {
  if (!item.applicantId) return

  uni.navigateTo({
    url: `/pages/me/card/index?userId=${item.applicantId}`
  })
}

// 通过申请
const handleApprove = async (item) => {
  try {
    await reviewCircleJoinRequest(item.id, { action: 'approve' })

    // 更新状态
    item.status = 'approved'
    item.read = true

    uni.showToast({
      title: '已通过申请',
      icon: 'success'
    })

    // 刷新列表
    setTimeout(() => {
      loadCircleRequests()
    }, 1000)
  } catch (err) {
    uni.showToast({
      title: err?.message || '操作失败',
      icon: 'none'
    })
  }
}

// 拒绝申请
const handleReject = async (item) => {
  uni.showModal({
    title: '拒绝申请',
    content: '确定要拒绝该申请吗？',
    success: async (res) => {
      if (res.confirm) {
        try {
          await reviewCircleJoinRequest(item.id, {
            action: 'reject',
            reject_reason: '不符合圈子要求'
          })

          // 更新状态
          item.status = 'rejected'
          item.read = true

          uni.showToast({
            title: '已拒绝申请',
            icon: 'success'
          })

          // 刷新列表
          setTimeout(() => {
            loadCircleRequests()
          }, 1000)
        } catch (err) {
          uni.showToast({
            title: err?.message || '操作失败',
            icon: 'none'
          })
        }
      }
    }
  })
}

// 点击系统通知
const handleItemTap = async (item) => {
  // 标记为已读
  if (!item.read && item.id) {
    try {
      await markNotificationAsRead(item.id)
      item.read = true
    } catch (err) {
      console.error('标记已读失败:', err)
    }
  }

  uni.showToast({
    title: '查看通知详情',
    icon: 'none'
  })
}

// 返回上一页
const goBack = () => {
  uni.navigateBack({
    delta: 1
  })
}

onShow(() => {
  loadData()
})
</script>

<style scoped>
.messages-page {
  min-height: 100vh;
  background: #f6f6f8;
  display: flex;
  flex-direction: column;
}

/* 顶部导航 */
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

/* 选项卡 */
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

.empty-icon {
  width: 160rpx;
  height: 160rpx;
  border-radius: 80rpx;
  background: #f1f5f9;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 32rpx;
}

.empty-icon .icon-img {
  width: 80rpx;
  height: 80rpx;
  opacity: 0.3;
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

/* 圈子申请卡片 */
.apply-card {
  background: #f8fafc;
  border-radius: 16rpx;
  border: 1rpx solid transparent;
  overflow: hidden;
}

.apply-card.card-read {
  opacity: 0.7;
}

.apply-card:not(.card-read) {
  background: #ffffff;
  border-color: #e7ecf3;
  box-shadow: 0 2rpx 12rpx rgba(15, 23, 42, 0.04);
}

.card-main {
  position: relative;
  display: flex;
  gap: 20rpx;
  padding: 24rpx;
}

.applicant-avatar {
  width: 96rpx;
  height: 96rpx;
  border-radius: 48rpx;
  background: #e2e8f0;
  flex-shrink: 0;
}

.apply-info {
  flex: 1;
  min-width: 0;
}

.info-top {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 16rpx;
  margin-bottom: 8rpx;
}

.applicant-name {
  font-size: 30rpx;
  font-weight: 600;
  color: #172033;
}

.apply-time {
  font-size: 22rpx;
  color: #94a3b8;
  flex-shrink: 0;
}

.apply-text {
  display: block;
  font-size: 26rpx;
  line-height: 38rpx;
  color: #475569;
  margin-bottom: 8rpx;
}

.apply-message {
  margin-top: 12rpx;
  padding: 16rpx;
  background: #f1f5f9;
  border-radius: 12rpx;
}

.message-label {
  font-size: 22rpx;
  color: #64748b;
}

.message-text {
  font-size: 24rpx;
  line-height: 36rpx;
  color: #475569;
}

.unread-dot {
  position: absolute;
  top: 28rpx;
  right: 24rpx;
  width: 16rpx;
  height: 16rpx;
  border-radius: 8rpx;
  background: #ef4444;
}

/* 操作按钮 */
.card-actions {
  display: flex;
  gap: 16rpx;
  padding: 0 24rpx 24rpx;
}

.action-btn {
  flex: 1;
  height: 72rpx;
  border-radius: 12rpx;
  border: 0;
  font-size: 28rpx;
  font-weight: 500;
  line-height: 72rpx;
  transition: all 0.2s;
}

.action-btn::after {
  border: 0;
}

.btn-reject {
  background: #f1f5f9;
  color: #475569;
}

.btn-reject-active {
  background: #e2e8f0;
}

.btn-approve {
  background: #2563eb;
  color: #ffffff;
}

.btn-approve-active {
  background: #1d4ed8;
}

/* 已处理状态 */
.card-status {
  padding: 0 24rpx 24rpx;
  text-align: center;
}

.status-text {
  display: inline-block;
  padding: 12rpx 32rpx;
  border-radius: 8rpx;
  font-size: 24rpx;
  font-weight: 500;
}

.status-approved {
  background: rgba(16, 185, 129, 0.1);
  color: #059669;
}

.status-rejected {
  background: rgba(239, 68, 68, 0.1);
  color: #dc2626;
}

/* 系统通知卡片 */
.notice-card {
  position: relative;
  display: flex;
  gap: 20rpx;
  padding: 24rpx;
  background: #f8fafc;
  border-radius: 16rpx;
  border: 1rpx solid transparent;
  transition: all 0.2s;
}

.notice-card:active {
  background: #f1f5f9;
}

.notice-card.card-read {
  opacity: 0.7;
}

.notice-card:not(.card-read) {
  background: #ffffff;
  border-color: #e7ecf3;
  box-shadow: 0 2rpx 12rpx rgba(15, 23, 42, 0.04);
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

  .empty-icon {
    background: #1e293b;
  }

  .empty-title {
    color: #cbd5e1;
  }

  .empty-hint {
    color: #64748b;
  }

  .apply-card {
    background: rgba(30, 41, 59, 0.5);
  }

  .apply-card:not(.card-read) {
    background: #1e293b;
    border-color: #334155;
    box-shadow: none;
  }

  .applicant-avatar {
    background: #334155;
  }

  .applicant-name {
    color: #f8fafc;
  }

  .apply-time {
    color: #64748b;
  }

  .apply-text {
    color: #cbd5e1;
  }

  .apply-message {
    background: rgba(15, 23, 42, 0.8);
  }

  .message-label {
    color: #94a3b8;
  }

  .message-text {
    color: #cbd5e1;
  }

  .btn-reject {
    background: #334155;
    color: #cbd5e1;
  }

  .btn-reject-active {
    background: #475569;
  }

  .btn-approve {
    background: #3b82f6;
  }

  .btn-approve-active {
    background: #2563eb;
  }

  .status-approved {
    background: rgba(16, 185, 129, 0.15);
    color: #34d399;
  }

  .status-rejected {
    background: rgba(239, 68, 68, 0.15);
    color: #f87171;
  }

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
