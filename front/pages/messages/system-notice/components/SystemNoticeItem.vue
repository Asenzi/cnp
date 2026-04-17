<template>
  <view class="notice-item">
    <view class="dot" :class="notice.isUnread ? 'dot-unread' : ''"></view>
    <view class="main">
      <view class="head-row">
        <text class="title">{{ notice.title }}</text>
        <text class="time">{{ notice.timeText }}</text>
      </view>
      <text class="content">{{ notice.content }}</text>
    </view>
  </view>
</template>

<script setup>
defineProps({
  notice: {
    type: Object,
    default: () => ({})
  }
})
</script>

<style scoped>
.notice-item {
  padding: 24rpx;
  display: flex;
  align-items: flex-start;
  gap: 14rpx;
  border-bottom: 1rpx solid #f1f5f9;
  background: #ffffff;
}

.dot {
  margin-top: 14rpx;
  width: 12rpx;
  height: 12rpx;
  border-radius: 999rpx;
  background: #d1d5db;
  flex-shrink: 0;
}

.dot-unread {
  background: #ef4444;
}

.main {
  flex: 1;
  min-width: 0;
}

.head-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12rpx;
}

.title {
  color: #0f172a;
  font-size: 28rpx;
  line-height: 38rpx;
  font-weight: 700;
}

.time {
  color: #94a3b8;
  font-size: 20rpx;
  line-height: 28rpx;
}

.content {
  margin-top: 6rpx;
  display: block;
  color: #475569;
  font-size: 24rpx;
  line-height: 34rpx;
}

@media (prefers-color-scheme: dark) {
  .notice-item {
    background: #0f172a;
    border-bottom-color: #1f2937;
  }

  .title {
    color: #f8fafc;
  }

  .content {
    color: #94a3b8;
  }
}
</style>
