<template>
  <view class="footer-wrap">
    <text class="footer-tip">没有更多已加入的圈子了</text>
    <button class="discover-btn" hover-class="discover-btn-active" @tap="onDiscover">
      <text class="discover-icon">+</text>
      <text class="discover-text">发现更多圈子</text>
    </button>
  </view>
</template>

<script setup>
const emit = defineEmits(['discover'])

const onDiscover = () => {
  emit('discover')
}
</script>

<style scoped>
.footer-wrap {
  padding: 32rpx 0 16rpx;
  text-align: center;
}

.footer-tip {
  display: block;
  color: #94a3b8;
  font-size: 22rpx;
  line-height: 30rpx;
  font-style: italic;
}

.discover-btn {
  margin-top: 14rpx;
  height: 58rpx;
  border-radius: 12rpx;
  border: 0;
  background: rgba(26, 87, 219, 0.08);
  color: #1a57db;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8rpx;
  padding: 0 20rpx;
}

.discover-btn-active {
  opacity: 0.85;
}

.discover-icon {
  font-size: 24rpx;
  line-height: 1;
  font-weight: 700;
}

.discover-text {
  font-size: 24rpx;
  line-height: 32rpx;
  font-weight: 700;
}
</style>
