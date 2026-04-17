<template>
  <button class="fab-btn" hover-class="fab-btn-active" @tap="$emit('tap')">
    <view class="plus-horizontal"></view>
    <view class="plus-vertical"></view>
  </button>
</template>

<script setup>
defineEmits(['tap'])
</script>

<style scoped>
.fab-btn {
  position: fixed;
  right: 24rpx;
  bottom: calc(150rpx + env(safe-area-inset-bottom));
  width: 96rpx;
  height: 96rpx;
  border-radius: 999rpx;
  border: 0;
  background: #1a57db;
  box-shadow: 0 10rpx 22rpx rgba(26, 87, 219, 0.32);
}

.fab-btn::after {
  border: 0;
}

.plus-horizontal,
.plus-vertical {
  position: absolute;
  left: 50%;
  top: 50%;
  background: #ffffff;
  border-radius: 999rpx;
}

.plus-horizontal {
  width: 32rpx;
  height: 6rpx;
  transform: translate(-50%, -50%);
}

.plus-vertical {
  width: 6rpx;
  height: 32rpx;
  transform: translate(-50%, -50%);
}

.fab-btn-active {
  transform: scale(0.96);
  opacity: 0.9;
}
</style>
