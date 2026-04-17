<template>
  <view class="list-card" hover-class="list-card-active" @tap="openCircle">
    <view class="main-row">
      <view class="cover-wrap">
        <image v-if="circle.coverImage" class="cover-image" mode="aspectFill" :src="circle.coverImage" />
        <view v-else class="cover-placeholder">
          <text class="cover-placeholder-text">&#x5708;</text>
        </view>
      </view>

      <view class="content-wrap">
        <text class="title">{{ circle.title }}</text>

        <view class="badge-row">
          <text v-if="circle.ownerVerified" class="badge badge-premium">PREMIUM</text>
          <text class="badge badge-industry">{{ circle.industryLabel || '\u5708\u5b50' }}</text>
        </view>

        <text class="desc">{{ circle.description || '\u6682\u65e0\u5708\u5b50\u4ecb\u7ecd' }}</text>
      </view>
    </view>

    <view class="bottom-row">
      <view class="stats-wrap">
        <view class="stats-item">
          <text class="stats-label">&#x6210;&#x5458;</text>
          <text class="stats-value">{{ circle.members }}</text>
        </view>
        <view class="stats-item">
          <text class="stats-label">&#x52A8;&#x6001;</text>
          <text class="stats-value">{{ circle.posts }}</text>
        </view>
      </view>

      <button class="action-btn" hover-class="action-btn-active" @tap.stop="openCircle">
        &#x67E5;&#x770B;&#x5708;&#x5B50;
      </button>
    </view>
  </view>
</template>

<script setup>
const props = defineProps({
  circle: {
    type: Object,
    default: () => ({})
  }
})

const openCircle = () => {
  const circleCode = String(props.circle?.circleCode || '').trim()
  if (!circleCode) {
    return
  }
  uni.navigateTo({
    url: `/pages/circles/detail/index?code=${encodeURIComponent(circleCode)}`
  })
}
</script>

<style scoped>
.list-card {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
  padding: 22rpx;
  border-radius: 26rpx;
  background: #ffffff;
  border: 1rpx solid #edf2f7;
  box-shadow: 0 12rpx 28rpx rgba(15, 23, 42, 0.06);
}

.list-card-active {
  background: #f8fafc;
}

.main-row {
  display: flex;
  align-items: flex-start;
  gap: 20rpx;
  min-width: 0;
}

.cover-wrap {
  width: 144rpx;
  height: 144rpx;
  border-radius: 22rpx;
  overflow: hidden;
  flex-shrink: 0;
  background: linear-gradient(135deg, #dbeafe 0%, #e2e8f0 100%);
}

.cover-image {
  width: 100%;
  height: 100%;
  display: block;
}

.cover-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.cover-placeholder-text {
  color: #64748b;
  font-size: 56rpx;
  line-height: 1;
  font-weight: 700;
}

.content-wrap {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.title {
  overflow: hidden;
  color: #111827;
  font-size: 30rpx;
  line-height: 40rpx;
  font-weight: 700;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.badge-row {
  margin-top: 8rpx;
  display: flex;
  align-items: center;
  gap: 10rpx;
  flex-wrap: wrap;
}

.badge {
  border-radius: 999rpx;
  padding: 4rpx 12rpx;
  font-size: 18rpx;
  line-height: 24rpx;
  font-weight: 700;
}

.badge-premium {
  color: #2563eb;
  background: rgba(37, 99, 235, 0.12);
}

.badge-industry {
  color: #16a34a;
  background: rgba(22, 163, 74, 0.12);
}

.desc {
  margin-top: 8rpx;
  display: -webkit-box;
  overflow: hidden;
  color: #64748b;
  font-size: 22rpx;
  line-height: 30rpx;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  word-break: break-all;
}

.bottom-row {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 20rpx;
}

.stats-wrap {
  display: flex;
  align-items: flex-start;
  justify-content: flex-start;
  gap: 24rpx;
  flex-shrink: 0;
}

.stats-item {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  text-align: left;
}

.stats-label {
  display: block;
  color: #94a3b8;
  font-size: 18rpx;
  line-height: 24rpx;
  text-align: left;
}

.stats-value {
  display: block;
  margin-top: 4rpx;
  color: #0f172a;
  font-size: 28rpx;
  line-height: 34rpx;
  font-weight: 700;
  text-align: left;
}

.action-btn {
  margin: 0;
  min-width: 170rpx;
  height: 72rpx;
  padding: 0 24rpx;
  border: 0;
  border-radius: 18rpx;
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
  color: #ffffff;
  font-size: 24rpx;
  line-height: 72rpx;
  font-weight: 700;
  box-shadow: 0 10rpx 20rpx rgba(37, 99, 235, 0.22);
  flex-shrink: 0;
}

.action-btn::after {
  border: 0;
}

.action-btn-active {
  opacity: 0.88;
}
</style>
