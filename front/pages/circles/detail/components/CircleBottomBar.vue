<template>
  <view class="bottom-bar">
    <view class="price-wrap">
      <view class="price-row">
        <text class="price-main">¥{{ price.current }}</text>
        <text class="price-unit">/年</text>
      </view>
      <text class="price-sub">原价 ¥{{ price.original }}/年，限时优惠</text>
    </view>

    <view class="actions-row">
      <button class="apply-btn" hover-class="apply-btn-active" @tap="emit('apply')">申请加入</button>
      <button class="join-btn" hover-class="join-btn-active" @tap="emit('join')">立即加入圈子</button>
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
  background: rgba(255, 255, 255, 0.95);
  border-top: 1rpx solid #e2e8f0;
  backdrop-filter: blur(12rpx);
  padding: 14rpx 24rpx calc(14rpx + env(safe-area-inset-bottom));
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
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
  color: #1a57db;
  font-size: 36rpx;
  line-height: 1;
  font-weight: 700;
}

.price-unit {
  color: #64748b;
  font-size: 18rpx;
  line-height: 24rpx;
}

.price-sub {
  margin-top: 4rpx;
  color: #94a3b8;
  font-size: 16rpx;
  line-height: 22rpx;
}

.actions-row {
  display: flex;
  align-items: center;
  gap: 10rpx;
}

.apply-btn,
.join-btn {
  height: 72rpx;
  border-radius: 999rpx;
  border: 0;
  padding: 0 26rpx;
  font-size: 22rpx;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.apply-btn {
  background: #f1f5f9;
  color: #334155;
}

.join-btn {
  background: #1a57db;
  color: #ffffff;
  box-shadow: 0 8rpx 16rpx rgba(26, 87, 219, 0.25);
}

.apply-btn-active,
.join-btn-active {
  opacity: 0.86;
}

@media (prefers-color-scheme: dark) {
  .bottom-bar {
    background: rgba(17, 22, 33, 0.95);
    border-top-color: #1e293b;
  }

  .price-unit,
  .price-sub {
    color: #94a3b8;
  }

  .apply-btn {
    background: #1e293b;
    color: #cbd5e1;
  }
}
</style>
