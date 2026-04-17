<template>
  <view class="masonry-card" hover-class="masonry-card-active" @tap="onTapCard">
    <view class="cover-wrap">
      <image v-if="circle.coverImage" class="cover-image" mode="aspectFill" :src="circle.coverImage" />
      <view v-else class="cover-placeholder">
        <text class="cover-placeholder-text">&#x5708;&#x5B50;&#x5C01;&#x9762;</text>
      </view>
    </view>

    <view class="card-content">
      <text class="card-title">{{ circle.title }}</text>

      <view v-if="circle.ownerName || circle.ownerAvatar" class="owner-row">
        <view class="owner-avatar-wrap">
          <image v-if="circle.ownerAvatar" class="owner-avatar" mode="aspectFill" :src="circle.ownerAvatar" />
          <view v-else class="owner-avatar-placeholder">
            <text class="owner-avatar-text">&#x4E3B;</text>
          </view>
        </view>
        <text class="owner-name">{{ circle.ownerName || '\u5708\u4e3b' }}</text>
      </view>

      <text class="card-desc">{{ circle.description || '\u6682\u65e0\u5708\u5b50\u4ecb\u7ecd' }}</text>

      <view class="stats-row">
        <view class="stats-item">
          <text class="stats-label">&#x6210;&#x5458;</text>
          <text class="stats-value">{{ circle.members }}</text>
        </view>
        <view class="stats-item">
          <text class="stats-label">&#x52A8;&#x6001;</text>
          <text class="stats-value">{{ circle.posts }}</text>
        </view>
      </view>
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

const onTapCard = () => {
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
.masonry-card {
  width: 100%;
  border-radius: 24rpx;
  border: 1rpx solid #edf2f7;
  background: #ffffff;
  box-shadow: 0 8rpx 24rpx rgba(15, 23, 42, 0.06);
  overflow: hidden;
  box-sizing: border-box;
}

.masonry-card-active {
  background: #f8fafc;
}

.cover-wrap {
  width: 100%;
  height: 210rpx;
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
  font-size: 24rpx;
  line-height: 32rpx;
  font-weight: 600;
}

.card-content {
  padding: 18rpx 16rpx 16rpx;
}

.card-title {
  display: block;
  width: 100%;
  max-width: 100%;
  overflow: hidden;
  color: #111827;
  font-size: 28rpx;
  line-height: 36rpx;
  font-weight: 700;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.owner-row {
  margin-top: 10rpx;
  display: flex;
  align-items: center;
  gap: 8rpx;
  min-width: 0;
}

.owner-avatar-wrap {
  width: 34rpx;
  height: 34rpx;
  border-radius: 50%;
  overflow: hidden;
  flex-shrink: 0;
  background: #e2e8f0;
}

.owner-avatar,
.owner-avatar-placeholder {
  width: 100%;
  height: 100%;
}

.owner-avatar-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
}

.owner-avatar-text {
  color: #64748b;
  font-size: 16rpx;
  line-height: 1;
  font-weight: 700;
}

.owner-name {
  min-width: 0;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #475569;
  font-size: 22rpx;
  line-height: 30rpx;
  font-weight: 500;
}

.card-desc {
  margin-top: 10rpx;
  display: -webkit-box;
  overflow: hidden;
  color: #64748b;
  font-size: 20rpx;
  line-height: 28rpx;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  word-break: break-all;
}

.stats-row {
  margin-top: 12rpx;
  display: flex;
  align-items: flex-start;
  justify-content: flex-start;
  gap: 20rpx;
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
  font-size: 14rpx;
  line-height: 20rpx;
  text-align: left;
}

.stats-value {
  display: block;
  margin-top: 2rpx;
  color: #0f172a;
  font-size: 18rpx;
  line-height: 24rpx;
  font-weight: 700;
  text-align: left;
}
</style>
