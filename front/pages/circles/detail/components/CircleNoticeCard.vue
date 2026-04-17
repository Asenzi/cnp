<template>
  <view class="notice-wrap">
    <view class="notice-head">
      <view class="notice-title-row">
        <image class="notice-icon" mode="aspectFit" src="/static/me-icons/badge-primary.png" />
        <text class="notice-title">最新公告</text>
      </view>

      <view class="more-link" hover-class="more-link-active" @tap="emit('more')">
        <text class="more-text">更多</text>
        <image class="more-chevron" mode="aspectFit" src="/static/me-icons/chevron-light.png" />
      </view>
    </view>

    <text class="notice-text">{{ notice }}</text>
  </view>
</template>

<script setup>
defineProps({
  notice: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['more'])
</script>

<style scoped>
.notice-wrap {
  margin: 16rpx 32rpx 0;
  border-radius: 16rpx;
  border: 1rpx solid rgba(26, 87, 219, 0.2);
  background: rgba(26, 87, 219, 0.06);
  padding: 18rpx;
}

.notice-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.notice-title-row {
  display: flex;
  align-items: center;
  gap: 8rpx;
}

.notice-icon {
  width: 30rpx;
  height: 30rpx;
}

.notice-title {
  color: #1a57db;
  font-size: 24rpx;
  line-height: 32rpx;
  font-weight: 700;
}

.more-link {
  display: flex;
  align-items: center;
  gap: 4rpx;
}

.more-link-active {
  opacity: 0.8;
}

.more-text {
  color: #1a57db;
  font-size: 20rpx;
  line-height: 28rpx;
  font-weight: 700;
}

.more-chevron {
  width: 18rpx;
  height: 18rpx;
  opacity: 0.7;
}

.notice-text {
  display: block;
  margin-top: 10rpx;
  color: #334155;
  font-size: 22rpx;
  line-height: 32rpx;
}

@media (prefers-color-scheme: dark) {
  .notice-wrap {
    background: rgba(26, 87, 219, 0.12);
    border-color: rgba(26, 87, 219, 0.3);
  }

  .notice-text {
    color: #cbd5e1;
  }
}
</style>
