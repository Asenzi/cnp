<template>
  <view class="time-row">
    <text class="time-text">{{ text }}</text>
  </view>
</template>

<script setup>
defineProps({
  text: {
    type: String,
    default: ''
  }
})
</script>

<style scoped>
.time-row {
  display: flex;
  justify-content: center;
  margin: 8rpx 0 20rpx;
}

.time-text {
  max-width: 420rpx;
  padding: 6rpx 18rpx;
  border-radius: 999rpx;
  background: #e9eef5;
  color: #94a3b8;
  font-size: 20rpx;
  line-height: 28rpx;
}

@media (prefers-color-scheme: dark) {
  .time-text {
    background: rgba(30, 41, 59, 0.7);
    color: #94a3b8;
  }
}
</style>
