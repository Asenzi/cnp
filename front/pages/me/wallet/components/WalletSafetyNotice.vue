<template>
  <view class="safety-card">
    <image class="safety-icon" mode="aspectFit" src="/static/me-icons/shield-person-primary.png" />
    <text class="safety-text">资金由 Sapphire Ledger 保护</text>
  </view>
</template>

<style scoped>
.safety-card {
  margin-top: 28rpx;
  padding: 16rpx 20rpx;
  border-radius: 16rpx;
  border: 1rpx solid rgba(26, 87, 219, 0.08);
  background: rgba(26, 87, 219, 0.04);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10rpx;
}

.safety-icon {
  width: 24rpx;
  height: 24rpx;
  opacity: 0.7;
}

.safety-text {
  color: #64748b;
  font-size: 22rpx;
  font-weight: 600;
}

@media (prefers-color-scheme: dark) {
  .safety-card {
    border-color: rgba(26, 87, 219, 0.2);
    background: rgba(26, 87, 219, 0.08);
  }

  .safety-text {
    color: #94a3b8;
  }
}
</style>
