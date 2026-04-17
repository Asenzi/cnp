<template>
  <view class="actions-wrap">
    <button class="action-btn secondary-btn" hover-class="btn-active" @tap="$emit('message')">
      <ProfileSymbol name="mail" :size="20" color="#1a57db" />
      <text class="secondary-text">发送消息</text>
    </button>
  </view>
</template>

<script setup>
import ProfileSymbol from './ProfileSymbol.vue'

defineEmits(['message'])
</script>

<style scoped>
.actions-wrap {
  position: fixed;
  left: 50%;
  bottom: 0;
  transform: translateX(-50%);
  width: 100%;
  max-width: 750rpx;
  z-index: 30;
  background: #ffffff;
  border-top: 1rpx solid #e2e8f0;
  box-shadow: 0 -8rpx 20rpx rgba(15, 23, 42, 0.05);
  padding: 18rpx 24rpx calc(18rpx + env(safe-area-inset-bottom));
  display: flex;
  gap: 16rpx;
}

.action-btn {
  height: 92rpx;
  border-radius: 18rpx;
  border: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8rpx;
}

.secondary-btn {
  flex: 1;
  border: 2rpx solid #1a57db;
  background: transparent;
}

.primary-btn {
  flex: 1;
  background: #1a57db;
  box-shadow: 0 10rpx 18rpx rgba(26, 87, 219, 0.3);
}

.secondary-text {
  color: #1a57db;
  font-size: 28rpx;
  line-height: 36rpx;
  font-weight: 700;
}

.primary-text {
  color: #ffffff;
  font-size: 28rpx;
  line-height: 36rpx;
  font-weight: 700;
}

.btn-active {
  opacity: 0.88;
}

@media (prefers-color-scheme: dark) {
  .actions-wrap {
    background: #0f172a;
    border-top-color: #1e293b;
  }
}
</style>
