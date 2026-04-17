<template>
  <view class="safety-card">
    <view class="safety-icon-wrap">
      <image class="safety-icon" mode="aspectFit" src="/static/me-icons/shield-person-primary.png" />
    </view>
    <view class="safety-main">
      <text class="safety-title">安全保障</text>
      <text class="safety-desc"
        >您的资金由 Sapphire Ledger 多重签名验证系统保护，并符合地区金融监管标准。</text
      >
    </view>
  </view>
</template>

<style scoped>
.safety-card {
  margin-top: 32rpx;
  padding: 24rpx;
  border-radius: 28rpx;
  border: 1rpx solid rgba(26, 87, 219, 0.1);
  background: rgba(26, 87, 219, 0.05);
  display: flex;
  align-items: flex-start;
  gap: 16rpx;
}

.safety-icon-wrap {
  width: 40rpx;
  height: 40rpx;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.safety-icon {
  width: 36rpx;
  height: 36rpx;
}

.safety-main {
  min-width: 0;
}

.safety-title {
  display: block;
  color: #0f172a;
  font-size: 24rpx;
  font-weight: 700;
}

.safety-desc {
  display: block;
  margin-top: 8rpx;
  color: #64748b;
  font-size: 22rpx;
  line-height: 1.55;
}

@media (prefers-color-scheme: dark) {
  .safety-card {
    border-color: rgba(26, 87, 219, 0.25);
    background: rgba(26, 87, 219, 0.12);
  }

  .safety-title {
    color: #e2e8f0;
  }

  .safety-desc {
    color: #94a3b8;
  }
}
</style>
