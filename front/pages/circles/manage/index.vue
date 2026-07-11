<template>
  <view class="manage-page">
    <view class="tabs">
      <view class="tab" :class="{ active: activeTab === 'circles' }" @tap="switchTab('circles')">
        <text>圈子管理</text>
      </view>
      <view class="tab" :class="{ active: activeTab === 'pending' }" @tap="switchTab('pending')">
        <text>待处理</text>
        <text v-if="summary.pendingCount > 0" class="tab-badge">{{ summary.pendingCount }}</text>
      </view>
    </view>

    <view v-if="activeTab === 'circles'" class="tab-content">
      <view class="search-bar">
        <image class="search-icon" src="/static/icon/search.png" mode="aspectFit" />
        <input
          v-model="keyword"
          class="search-input"
          placeholder="搜索我创建的圈子"
          placeholder-class="search-placeholder"
          confirm-type="search"
          @confirm="loadAll"
        />
        <text v-if="keyword" class="clear-search" @tap="clearSearch">清除</text>
      </view>

      <view v-if="loading && circles.length === 0" class="state-wrap">
        <text class="state-text">正在加载圈子...</text>
      </view>

      <view v-else-if="!loading && circles.length === 0" class="empty-card">
        <image class="empty-icon" src="/static/icon/create.png" mode="aspectFit" />
        <text class="empty-title">还没有创建圈子</text>
        <text class="empty-desc">创建一个圈子，开始连接同领域伙伴</text>
        <button class="empty-button" @tap="goCreate">创建第一个圈子</button>
      </view>

      <view v-else class="circle-list">
        <view v-for="circle in circles" :key="circle.circleCode" class="circle-card">
          <view class="circle-main" @tap="goDetail(circle)">
            <image class="circle-avatar" :src="circle.avatar" mode="aspectFill" />
            <view class="circle-info">
              <view class="circle-title-row">
                <text class="circle-name">{{ circle.name }}</text>
                <text class="status-chip" :class="'status-' + circle.status">{{ circle.statusText }}</text>
              </view>
              <text class="circle-meta">{{ circle.industry }} · {{ circle.joinText }}</text>
              <text class="circle-description">{{ circle.description }}</text>
            </view>
            <text class="circle-arrow">></text>
          </view>

          <view class="metric-row">
            <view class="metric">
              <text class="metric-number">{{ circle.memberCount }}</text>
              <text class="metric-label">成员</text>
            </view>
            <view class="metric">
              <text class="metric-number">{{ circle.postCount }}</text>
              <text class="metric-label">内容</text>
            </view>
            <view class="metric">
              <text class="metric-number">{{ circle.collectCount }}</text>
              <text class="metric-label">收藏</text>
            </view>
            <view class="metric">
              <text class="metric-number" :class="{ alert: circle.pendingCount > 0 }">
                {{ circle.pendingCount }}
              </text>
              <text class="metric-label">待处理</text>
            </view>
          </view>

          <view class="action-row">
            <button class="action-button secondary" @tap="goDetail(circle)">查看主页</button>
            <button class="action-button secondary" @tap="goEdit(circle)">编辑资料</button>
            <button class="action-button primary" @tap="openCirclePending(circle)">
              处理事项
              <text v-if="circle.pendingCount > 0" class="button-badge">{{ circle.pendingCount }}</text>
            </button>
          </view>
        </view>
      </view>
    </view>

    <view v-else class="tab-content">
      <view v-if="pendingLoading" class="state-wrap">
        <text class="state-text">正在加载待处理事项...</text>
      </view>

      <view v-else-if="visiblePendingItems.length === 0" class="empty-card compact">
        <image class="empty-icon" src="/static/icon/data-block.png" mode="aspectFit" />
        <text class="empty-title">暂时没有待处理事项</text>
        <text class="empty-desc">新的加入申请会出现在这里</text>
      </view>

      <view v-else class="pending-list">
        <view v-for="item in visiblePendingItems" :key="item.key" class="pending-card">
          <view class="pending-head">
            <image class="pending-avatar" :src="item.avatar" mode="aspectFill" />
            <view class="pending-main">
              <view class="pending-title-row">
                <text class="pending-title">{{ item.title }}</text>
                <text class="pending-type">{{ item.typeLabel }}</text>
              </view>
              <text class="pending-circle">{{ item.circleName }}</text>
              <text class="pending-desc">{{ item.description }}</text>
            </view>
          </view>
          <view class="pending-actions">
            <button class="review-button reject" @tap="reviewPending(item, 'reject')">拒绝</button>
            <button class="review-button approve" @tap="reviewPending(item, 'approve')">通过</button>
          </view>
        </view>
      </view>
    </view>

    <button class="floating-create" hover-class="floating-create-active" @tap="goCreate">
      <image class="floating-create-icon" src="/static/icon/create.png" mode="aspectFit" />
      <text class="floating-create-text">创建圈子</text>
    </button>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onPullDownRefresh, onShow } from '@dcloudio/uni-app'
import {
  getCircleJoinRequests,
  getOwnedCircles,
  reviewCircleJoinRequest
} from '../../../api/circle'

const activeTab = ref('circles')
const keyword = ref('')
const circles = ref([])
const joinRequests = ref([])
const loading = ref(false)
const pendingLoading = ref(false)

const summary = computed(() => ({
  circleCount: circles.value.length,
  memberCount: circles.value.reduce((total, item) => total + item.memberCount, 0),
  pendingCount: joinRequests.value.length
}))

const visiblePendingItems = computed(() => [...joinRequests.value].sort((a, b) => b.timestamp - a.timestamp))

const safeImage = (value) => String(value || '').trim() || '/static/logo.png'
const formatJoinText = (item) => `付费入圈 ￥${Number(item.join_price || 0).toFixed(2)}`

const mapCircle = (item = {}) => {
  const pendingJoinCount = Number(item.pending_join_count || 0)
  const status = String(item.status || 'active').trim()
  return {
    circleCode: String(item.circle_code || '').trim(),
    name: String(item.name || '未命名圈子').trim(),
    industry: String(item.industry_label || '未分类').trim(),
    description: String(item.description || '暂无圈子简介').trim(),
    avatar: safeImage(item.avatar_url || item.cover_url),
    joinText: formatJoinText(item),
    status,
    statusText: status === 'active' ? '运营中' : status === 'pending' ? '审核中' : '已停用',
    memberCount: Number(item.member_count || 0),
    postCount: Number(item.post_count || 0),
    collectCount: Number(item.collect_count || 0),
    pendingJoinCount,
    pendingCount: pendingJoinCount
  }
}

const loadCircles = async () => {
  loading.value = true
  try {
    const data = await getOwnedCircles({ limit: 50, keyword: keyword.value })
    circles.value = (Array.isArray(data?.items) ? data.items : []).map(mapCircle)
  } catch (err) {
    circles.value = []
    uni.showToast({ title: err?.message || '圈子加载失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

const loadPending = async () => {
  pendingLoading.value = true
  try {
    const joinData = await getCircleJoinRequests({ status: 'pending', limit: 100 })
    joinRequests.value = (Array.isArray(joinData?.items) ? joinData.items : [])
      .filter(item => item.perspective === 'owner' && item.payment_status === 'paid')
      .map(item => ({
        key: `join-${item.id}`,
        id: item.id,
        type: 'join',
        typeLabel: '入圈申请',
        circleCode: String(item.circle?.circle_code || item.circle_code || '').trim(),
        circleName: String(item.circle?.name || '未命名圈子').trim(),
        title: String(item.user?.nickname || '一位用户').trim(),
        description: String(item.message || '申请加入你的圈子').trim(),
        avatar: safeImage(item.user?.avatar_url),
        timestamp: new Date(item.updated_at || item.created_at).getTime()
      }))
  } catch (err) {
    joinRequests.value = []
    uni.showToast({ title: err?.message || '待处理事项加载失败', icon: 'none' })
  } finally {
    pendingLoading.value = false
  }
}

const loadAll = async () => {
  await loadCircles()
  await loadPending()
}

const switchTab = (key) => {
  activeTab.value = key
}

const clearSearch = () => {
  keyword.value = ''
  loadAll()
}

const goCreate = () => uni.navigateTo({ url: '/pages/circles/create/index' })
const goDetail = (circle) => uni.navigateTo({
  url: `/pages/circles/detail/index?code=${encodeURIComponent(circle.circleCode)}`
})
const goEdit = (circle) => uni.navigateTo({
  url: `/pages/circles/edit/index?code=${encodeURIComponent(circle.circleCode)}`
})

const openCirclePending = (circle) => {
  activeTab.value = 'pending'
  if (circle.pendingCount === 0) {
    uni.showToast({ title: '暂无待处理事项', icon: 'none' })
  }
}

const reviewPending = (item, action) => {
  const isApprove = action === 'approve'
  uni.showModal({
    title: isApprove ? '确认通过' : '确认拒绝',
    content: isApprove
      ? `确认通过“${item.title}”的${item.typeLabel}吗？`
      : `确认拒绝“${item.title}”的${item.typeLabel}吗？`,
    confirmText: isApprove ? '通过' : '拒绝',
    confirmColor: isApprove ? '#2563eb' : '#ef4444',
    success: async (res) => {
      if (!res.confirm) return
      try {
        await reviewCircleJoinRequest(item.id, {
          action,
          reject_reason: isApprove ? '' : '暂不符合圈子要求'
        })
        uni.showToast({ title: isApprove ? '已通过' : '已拒绝', icon: 'success' })
        await loadAll()
      } catch (err) {
        uni.showToast({ title: err?.message || '处理失败', icon: 'none' })
      }
    }
  })
}

onShow(loadAll)
onPullDownRefresh(async () => {
  await loadAll()
  uni.stopPullDownRefresh()
})
</script>

<style scoped>
.manage-page {
  min-height: 100vh;
  box-sizing: border-box;
  padding: 16rpx 24rpx calc(150rpx + env(safe-area-inset-bottom));
  background: #f6f7fb;
  color: #172033;
}

.floating-create::after,
.action-button::after,
.review-button::after,
.empty-button::after {
  border: 0;
}

.tabs {
  position: sticky;
  position: -webkit-sticky;
  top: 0;
  z-index: 15;
  display: flex;
  margin: 0 0 20rpx;
  padding: 8rpx;
  /* border-radius: 18rpx; */
  background: #e9edf5;
  box-shadow: 0 10rpx 24rpx rgba(35, 52, 87, 0.06);
}

.tab {
  position: relative;
  flex: 1;
  height: 68rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10rpx;
  border-radius: 14rpx;
  color: #7a869c;
  font-size: 27rpx;
  font-weight: 500;
}

.tab.active {
  background: #fff;
  color: #1d4ed8;
  font-weight: 650;
  box-shadow: 0 4rpx 14rpx rgba(37, 56, 88, 0.08);
}

.tab-badge,
.button-badge {
  min-width: 30rpx;
  height: 30rpx;
  padding: 0 8rpx;
  box-sizing: border-box;
  border-radius: 15rpx;
  background: #ef4444;
  color: #fff;
  font-size: 19rpx;
  line-height: 30rpx;
  text-align: center;
}

.search-bar {
  height: 76rpx;
  display: flex;
  align-items: center;
  padding: 0 24rpx;
  border-radius: 18rpx;
  background: #fff;
  box-shadow: 0 4rpx 18rpx rgba(35, 52, 87, 0.04);
}

.search-icon {
  width: 30rpx;
  height: 30rpx;
  opacity: 0.52;
}

.search-input {
  flex: 1;
  height: 76rpx;
  margin-left: 14rpx;
  color: #26334b;
  font-size: 26rpx;
}

.search-placeholder {
  color: #a2abba;
}

.clear-search {
  color: #2563eb;
  font-size: 23rpx;
}

.circle-list,
.pending-list {
  display: flex;
  flex-direction: column;
  gap: 18rpx;
  margin-top: 18rpx;
}

.circle-card,
.pending-card {
  overflow: hidden;
  border: 1rpx solid #edf0f5;
  border-radius: 22rpx;
  background: #fff;
  box-shadow: 0 7rpx 24rpx rgba(35, 52, 87, 0.055);
}

.circle-main {
  display: flex;
  align-items: center;
  padding: 24rpx;
}

.circle-avatar {
  width: 104rpx;
  height: 104rpx;
  flex-shrink: 0;
  border-radius: 22rpx;
  background: #eef2f7;
}

.circle-info {
  flex: 1;
  min-width: 0;
  margin-left: 20rpx;
}

.circle-title-row {
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.circle-name {
  max-width: 340rpx;
  overflow: hidden;
  color: #172033;
  font-size: 30rpx;
  font-weight: 650;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.status-chip {
  padding: 5rpx 12rpx;
  border-radius: 10rpx;
  background: #e8f7ef;
  color: #16955e;
  font-size: 20rpx;
}

.status-pending {
  background: #fff4dd;
  color: #c37b00;
}

.status-disabled {
  background: #f1f3f6;
  color: #8792a7;
}

.circle-meta,
.circle-description {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.circle-meta {
  margin-top: 8rpx;
  color: #66748d;
  font-size: 23rpx;
}

.circle-description {
  margin-top: 7rpx;
  color: #98a2b3;
  font-size: 22rpx;
}

.circle-arrow {
  margin-left: 10rpx;
  color: #b7bfcc;
  font-size: 40rpx;
}

.metric-row {
  display: flex;
  padding: 20rpx 12rpx;
  border-top: 1rpx solid #f0f2f6;
  background: #fafbfc;
}

.metric {
  flex: 1;
  text-align: center;
}

.metric-number {
  display: block;
  color: #27344b;
  font-size: 27rpx;
  font-weight: 650;
}

.metric-number.alert {
  color: #ef4444;
}

.metric-label {
  display: block;
  margin-top: 4rpx;
  color: #98a2b3;
  font-size: 21rpx;
}

.action-row {
  display: flex;
  gap: 14rpx;
  padding: 18rpx 20rpx 22rpx;
}

.action-button {
  flex: 1;
  height: 66rpx;
  margin: 0;
  padding: 0;
  border-radius: 14rpx;
  font-size: 23rpx;
  line-height: 66rpx;
}

.action-button.secondary {
  background: #f2f5f9;
  color: #536178;
}

.action-button.primary {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 7rpx;
  background: #e8f0ff;
  color: #2563eb;
  font-weight: 600;
}

.pending-card {
  padding: 24rpx;
}

.pending-head {
  display: flex;
}

.pending-avatar {
  width: 82rpx;
  height: 82rpx;
  flex-shrink: 0;
  border-radius: 41rpx;
  background: #eef2f7;
}

.pending-main {
  flex: 1;
  min-width: 0;
  margin-left: 18rpx;
}

.pending-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
}

.pending-title {
  overflow: hidden;
  color: #172033;
  font-size: 28rpx;
  font-weight: 650;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.pending-type {
  flex-shrink: 0;
  padding: 5rpx 11rpx;
  border-radius: 9rpx;
  background: #fff1df;
  color: #c57910;
  font-size: 19rpx;
}

.pending-circle,
.pending-desc {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.pending-circle {
  margin-top: 6rpx;
  color: #66748d;
  font-size: 23rpx;
}

.pending-desc {
  margin-top: 7rpx;
  color: #98a2b3;
  font-size: 22rpx;
}

.pending-actions {
  display: flex;
  justify-content: flex-end;
  gap: 14rpx;
  margin-top: 22rpx;
}

.review-button {
  width: 150rpx;
  height: 62rpx;
  margin: 0;
  border-radius: 14rpx;
  font-size: 24rpx;
  line-height: 62rpx;
}

.review-button.reject {
  background: #f2f4f7;
  color: #64748b;
}

.review-button.approve {
  background: #2563eb;
  color: #fff;
}

.state-wrap {
  padding: 120rpx 20rpx;
  text-align: center;
}

.state-text {
  color: #98a2b3;
  font-size: 25rpx;
}

.empty-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-top: 18rpx;
  padding: 92rpx 32rpx;
  border-radius: 22rpx;
  background: #fff;
}

.empty-card.compact {
  padding-top: 76rpx;
  padding-bottom: 76rpx;
}

.empty-icon {
  width: 106rpx;
  height: 106rpx;
  opacity: 0.62;
}

.empty-title {
  margin-top: 22rpx;
  color: #37445b;
  font-size: 29rpx;
  font-weight: 650;
}

.empty-desc {
  margin-top: 10rpx;
  color: #98a2b3;
  font-size: 23rpx;
}

.empty-button {
  height: 68rpx;
  margin-top: 28rpx;
  padding: 0 32rpx;
  border-radius: 34rpx;
  background: #2563eb;
  color: #fff;
  font-size: 24rpx;
  line-height: 68rpx;
}

.floating-create {
  position: fixed;
  right: 30rpx;
  bottom: calc(34rpx + env(safe-area-inset-bottom));
  z-index: 20;
  height: 88rpx;
  display: flex;
  align-items: center;
  gap: 12rpx;
  margin: 0;
  padding: 0 30rpx 0 24rpx;
  border: 0;
  border-radius: 44rpx;
  background: #2563eb;
  box-shadow: 0 12rpx 32rpx rgba(37, 99, 235, 0.32);
}

.floating-create-active {
  opacity: 0.88;
  transform: scale(0.97);
}

.floating-create-icon {
  width: 36rpx;
  height: 36rpx;
  filter: brightness(0) invert(1);
}

.floating-create-text {
  color: #fff;
  font-size: 26rpx;
  font-weight: 600;
}
</style>
