<template>
  <view class="bottom-bar">
    <view class="price-wrap">
      <view class="price-row">
        <text class="price-main">¥{{ price.current }}</text>
        <text class="price-unit">/年</text>
      </view>
      <text class="price-sub">原价 ¥{{ price.original }}</text>
    </view>

    <view class="actions-row">
      <button class="apply-btn" hover-class="apply-btn-active" @tap="emit('apply')">申请加入</button>
      <button class="join-btn" hover-class="join-btn-active" @tap="emit('join')">立即加入</button>
    </view>
  </view>
</template>

<script setup>
defineProps({
  price: {
    type: Object,
    default: () => ({ current: '99.00', original: '299' })
  }
})

const emit = defineEmits(['apply', 'join'])
</script>

<style scoped>
.bottom-bar {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 40;
  background: #ffffff;
  border-top: 1rpx solid #f3f4f6;
  padding: 16rpx 32rpx calc(16rpx + env(safe-area-inset-bottom));
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20rpx;
}

.price-wrap {
  display: flex;
  flex-direction: column;
}

.price-row {
  display: flex;
  align-items: flex-end;
  gap: 4rpx;
}

.price-main {
  color: #dc2626;
  font-size: 36rpx;
  line-height: 1;
  font-weight: 600;
}

.price-unit {
  color: #6b7280;
  font-size: 22rpx;
  line-height: 30rpx;
}

.price-sub {
  margin-top: 4rpx;
  color: #9ca3af;
  font-size: 22rpx;
  line-height: 30rpx;
  text-decoration: line-through;
}

.actions-row {
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.apply-btn,
.join-btn {
  height: 72rpx;
  border-radius: 6rpx;
  border: 0;
  padding: 0 28rpx;
  font-size: 26rpx;
  font-weight: 500;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.apply-btn {
  background: #f3f4f6;
  color: #374151;
}

.join-btn {
  background: #2563eb;
  color: #ffffff;
}

.apply-btn-active,
.join-btn-active {
  opacity: 0.8;
}

@media (prefers-color-scheme: dark) {
  .bottom-bar {
    background: #111827;
    border-top-color: #1f2937;
  }

  .apply-btn {
    background: #1f2937;
    color: #d1d5db;
  }
}
</style>
