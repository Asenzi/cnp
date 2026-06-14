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
        <image class="empty-icon-image" src="https://cos.cnptec.site/static/icon/data-block.png" mode="aspectFit" />
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
            @tap="handleCircleRequestTap(item)"
          >
            <view class="card-body">
              <!-- 头像和主要信息 -->
              <view class="card-top">
                <image class="user-avatar" mode="aspectFill" :src="item.avatar" />
                <view class="main-info">
                  <text class="user-name">{{ item.displayName }}</text>
                  <text class="circle-title">{{ item.circleName }}</text>
                </view>
                <text class="time-ago">{{ item.timeText }}</text>
              </view>

              <!-- 操作或状态 -->
              <view v-if="item.perspective === 'owner' && item.status === 'pending' && item.paymentStatus === 'paid'" class="actions">
                <view class="btn-reject" hover-class="btn-reject-hover" @tap.stop="handleReject(item)">
                  <text class="btn-text">拒绝</text>
                </view>
                <view class="btn-approve" hover-class="btn-approve-hover" @tap.stop="handleApprove(item)">
                  <text class="btn-text">通过</text>
                </view>
              </view>

              <view
                v-else-if="item.statusText && item.perspective === 'applicant' && item.status === 'pending' && item.paymentStatus === 'paid'"
                class="status-row"
              >
                <view class="status-btn" hover-class="status-btn-hover" @tap.stop="handleCancelRequest(item)">
                  <text class="btn-text">{{ item.statusText }}</text>
                </view>
              </view>

              <view v-else-if="item.statusText" class="status-row">
                <view class="status-chip" :class="item.statusClass">
                  <text class="chip-text">{{ item.statusText }}</text>
                </view>
              </view>
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
import { computed, onUnmounted, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { cancelCircleJoinRequest, getCircleJoinRequests, reviewCircleJoinRequest } from '../../../api/circle'
import { getSystemNotifications, markNotificationAsRead } from '../../../api/notification'
import { connectRealtimeSocket, subscribeRealtime } from '../../../utils/realtime'

// 获取状态栏高度
const { statusBarHeight = 0 } = uni.getSystemInfoSync()

// 状态
const loading = ref(false)
const activeTab = ref('circle')
const circleList = ref([])
const systemList = ref([])
let realtimeRefreshTimer = null

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
  return activeTab.value === 'circle' ? 'https://cos.cnptec.site/static/icon/mennber.png' : 'https://cos.cnptec.site/static/icon/block.png'
})
const emptyHint = computed(() => {
  return activeTab.value === 'circle'
    ? '圈子加入申请和审核结果会在这里显示'
    : '系统公告和重要通知会在这里显示'
})

// 图标映射
const typeIcons = {
  circle: 'https://cos.cnptec.site/static/icon/mennber.png',
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

const formatDeadline = (value) => {
  const timestamp = new Date(value || '').getTime()
  if (!Number.isFinite(timestamp)) return ''
  const now = Date.now()
  const diff = timestamp - now

  if (diff <= 0) return ''

  const hour = 60 * 60 * 1000
  const day = 24 * hour

  if (diff < hour) {
    const minutes = Math.ceil(diff / (60 * 1000))
    return `${minutes}分钟后自动通过`
  } else if (diff < day) {
    const hours = Math.ceil(diff / hour)
    return `${hours}小时后自动通过`
  } else {
    const days = Math.ceil(diff / day)
    return `${days}天后自动通过`
  }
}

const resolveRequestStatus = (item, perspective) => {
  const status = String(item.status || 'pending').trim()
  const paymentStatus = String(item.payment_status || 'unpaid').trim()
  const refundStatus = String(item.refund_status || 'none').trim()
  if (status === 'approved') {
    return { text: perspective === 'applicant' ? '已加入圈子' : '已通过', className: 'status-approved' }
  }
  if (status === 'rejected') {
    if (Number(item.amount || 0) > 0 && refundStatus === 'success') {
      return { text: '已拒绝 · 费用已退回', className: 'status-rejected' }
    }
    return { text: '已拒绝', className: 'status-rejected' }
  }
  if (status === 'cancelled') {
    if (Number(item.amount || 0) > 0 && refundStatus === 'success') {
      return { text: '已取消 · 费用已退回', className: 'status-cancelled' }
    }
    return { text: '已取消', className: 'status-cancelled' }
  }
  if (paymentStatus === 'pending') {
    return { text: '待完成支付', className: 'status-pending' }
  }
  return {
    text: perspective === 'applicant' ? '取消加入' : '待处理',
    className: 'status-pending'
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

const scheduleRealtimeRefresh = () => {
  if (realtimeRefreshTimer) return
  realtimeRefreshTimer = setTimeout(async () => {
    realtimeRefreshTimer = null
    await Promise.all([
      loadCircleRequests(),
      loadSystemNotifications()
    ])
  }, 250)
}

const unsubscribeRealtime = subscribeRealtime((payload) => {
  if (payload?.event === 'notification.changed') {
    scheduleRealtimeRefresh()
  }
})

// 加载圈子申请
const loadCircleRequests = async () => {
  try {
    const data = await getCircleJoinRequests({ limit: 50 })
    const items = Array.isArray(data?.items) ? data.items : []

    circleList.value = items.map(item => {
      const perspective = String(item.perspective || 'owner').trim()
      const circleName = String(item.circle?.name || item.circle_name || '').trim()
      const applicantName = String(item.user?.nickname || item.applicant_name || '未知用户').trim()
      const status = resolveRequestStatus(item, perspective)
      const amount = Number(item.amount || 0)
      return {
        id: String(item.id || item.request_id || ''),
        type: 'circle',
        perspective,
        displayName: perspective === 'applicant' ? circleName : applicantName,
        content: perspective === 'applicant'
          ? `你申请加入圈子”${circleName}”`
          : `${applicantName}申请加入你的圈子”${circleName}”`,
        message: String(item.message || '').trim(),
        amount,
        autoApproveText: item.status === 'pending' && item.auto_approve_at ? formatDeadline(item.auto_approve_at) : '',
        circleName,
        circleCode: String(item.circle?.circle_code || item.circle_code || '').trim(),
        timestamp: new Date(item.updated_at || item.created_at).getTime(),
        timeText: formatTime(new Date(item.updated_at || item.created_at).getTime()),
        read: perspective === 'applicant' || item.status !== 'pending',
        status: String(item.status || 'pending').trim(),
        statusText: status.text,
        statusClass: status.className,
        paymentStatus: String(item.payment_status || 'unpaid').trim(),
        refundStatus: String(item.refund_status || 'none').trim(),
        avatar: String(
          perspective === 'applicant'
            ? item.circle?.avatar_url || item.circle?.cover_url
            : item.user?.avatar_url || item.applicant_avatar
        ).trim() || 'https://cos.cnptec.site/static/logo.png',
        applicantId: String(item.user?.user_id || item.user_pk || '').trim()
      }
    })
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

const handleCircleRequestTap = (item) => {
  if (item.perspective === 'applicant') {
    if (!item.circleCode) return
    uni.navigateTo({
      url: `/pages/circles/detail/index?code=${encodeURIComponent(item.circleCode)}`
    })
    return
  }
  if (item.applicantId) {
    uni.navigateTo({
      url: `/pages/me/card/index?userId=${encodeURIComponent(item.applicantId)}`
    })
  }
}

// 通过申请
const handleApprove = async (item) => {
  try {
    await reviewCircleJoinRequest(item.id, { action: 'approve' })

    item.status = 'approved'
    item.read = true

    uni.showToast({
      title: '已通过申请',
      icon: 'success'
    })

    // 鍒锋柊鍒楄〃
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
    content: item.amount > 0
      ? `确定拒绝该申请并退回 ¥${item.amount.toFixed(2)} 入圈费用吗？`
      : '确定要拒绝该申请吗？',
    success: async (res) => {
      if (res.confirm) {
        try {
          await reviewCircleJoinRequest(item.id, {
            action: 'reject',
            reject_reason: '不符合圈子要求'
          })

          item.status = 'rejected'
          item.read = true

          uni.showToast({
            title: '已拒绝申请',
            icon: 'success'
          })

          // 鍒锋柊鍒楄〃
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

// 取消加入申请
const handleCancelRequest = async (item) => {
  uni.showModal({
    title: '取消加入',
    content: '确定要取消加入该圈子的申请吗？',
    success: async (res) => {
      if (res.confirm) {
        try {
          await cancelCircleJoinRequest(item.id)

          uni.showToast({
            title: '已取消申请',
            icon: 'success'
          })

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

/* 娑堟伅鍒楄〃 */
.message-list {
  padding: 24rpx 24rpx calc(24rpx + env(safe-area-inset-bottom));
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

/* 圈子申请卡片 */
.apply-card {
  background: #ffffff;
  border-radius: 16rpx;
  overflow: hidden;
  box-shadow: 0 1rpx 3rpx rgba(15, 23, 42, 0.06);
}

.apply-card.card-read {
  opacity: 0.6;
}

.card-body {
  padding: 24rpx;
}

/* 顶部：头像+信息 */
.card-top {
  display: flex;
  gap: 16rpx;
  margin-bottom: 16rpx;
}

.user-avatar {
  width: 80rpx;
  height: 80rpx;
  border-radius: 40rpx;
  background: #f1f5f9;
  flex-shrink: 0;
}

.main-info {
  flex: 1;
  min-width: 0;
}

.user-name {
  display: block;
  font-size: 32rpx;
  font-weight: 600;
  color: #0f172a;
  line-height: 1.3;
  margin-bottom: 6rpx;
}

.circle-title {
  display: block;
  font-size: 26rpx;
  color: #64748b;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.time-ago {
  font-size: 24rpx;
  color: #94a3b8;
  flex-shrink: 0;
  line-height: 1.3;
}

/* 操作按钮 */
.actions {
  display: flex;
  gap: 12rpx;
}

.btn-reject,
.btn-approve {
  flex: 1;
  height: 76rpx;
  border-radius: 12rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.btn-reject {
  background: #f1f5f9;
}

.btn-reject-hover {
  background: #e2e8f0;
  transform: scale(0.98);
}

.btn-approve {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  box-shadow: 0 4rpx 12rpx rgba(37, 99, 235, 0.2);
}

.btn-approve-hover {
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
  transform: scale(0.98);
  box-shadow: 0 2rpx 8rpx rgba(37, 99, 235, 0.3);
}

.btn-text {
  font-size: 28rpx;
  font-weight: 500;
  line-height: 1.3;
}

.btn-reject .btn-text {
  color: #64748b;
}

.btn-approve .btn-text {
  color: #ffffff;
}

/* 状态显示 */
.status-row {
  display: flex;
  justify-content: flex-end;
}

.status-btn {
  padding: 12rpx 32rpx;
  background: #1296db;
  border-radius: 24rpx;
  box-shadow: 0 4rpx 12rpx rgba(18, 150, 219, 0.2);
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.status-btn-hover {
  background: #0d7ab8;
  transform: scale(0.98);
  box-shadow: 0 2rpx 8rpx rgba(18, 150, 219, 0.3);
}

.status-btn .btn-text {
  font-size: 26rpx;
  font-weight: 500;
  color: #ffffff;
  line-height: 1.3;
}

.status-chip {
  padding: 10rpx 24rpx;
  border-radius: 24rpx;
  display: inline-flex;
  align-items: center;
}

.chip-text {
  font-size: 26rpx;
  font-weight: 500;
  line-height: 1.3;
}

.status-approved {
  background: rgba(16, 185, 129, 0.12);
}

.status-approved .chip-text {
  color: #059669;
}

.status-rejected {
  background: rgba(239, 68, 68, 0.12);
}

.status-rejected .chip-text {
  color: #dc2626;
}

.status-cancelled {
  background: rgba(100, 116, 139, 0.12);
}

.status-cancelled .chip-text {
  color: #64748b;
}

.status-pending,
.status-paid,
.status-unpaid,
.status-refunded {
  background: #f1f5f9;
}

.status-pending .chip-text,
.status-paid .chip-text,
.status-unpaid .chip-text,
.status-refunded .chip-text {
  color: #64748b;
}

.status-pending {
  background: rgba(217, 119, 6, 0.1);
  color: #b45309;
}

/* 绯荤粺閫氱煡鍗＄墖 */
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

  .empty-title {
    color: #cbd5e1;
  }

  .empty-hint {
    color: #64748b;
  }

  /* 圈子申请卡片 - 深色模式 */
  .apply-card {
    background: #1e293b;
    box-shadow: 0 1rpx 3rpx rgba(0, 0, 0, 0.2);
  }

  .user-avatar {
    background: #334155;
  }

  .user-name {
    color: #f1f5f9;
  }

  .circle-title {
    color: #94a3b8;
  }

  .time-ago {
    color: #64748b;
  }

  .btn-reject {
    background: #334155;
  }

  .btn-reject-hover {
    background: #475569;
  }

  .btn-reject .btn-text {
    color: #cbd5e1;
  }

  .btn-approve {
    background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  }

  .btn-approve-hover {
    background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
  }

  .status-approved {
    background: rgba(16, 185, 129, 0.18);
  }

  .status-approved .chip-text {
    color: #34d399;
  }

  .status-rejected {
    background: rgba(239, 68, 68, 0.18);
  }

  .status-rejected .chip-text {
    color: #f87171;
  }

  .status-btn {
    background: #1296db;
  }

  .status-btn-hover {
    background: #0d7ab8;
  }

  .status-pending,
  .status-paid,
  .status-unpaid,
  .status-refunded {
    background: #f1f5f9;
  }

  .status-pending .chip-text,
  .status-paid .chip-text,
  .status-unpaid .chip-text,
  .status-refunded .chip-text {
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
