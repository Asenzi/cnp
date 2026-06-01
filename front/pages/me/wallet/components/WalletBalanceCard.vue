<template>
  <view class="wallet-card">
    <view class="card-shine"></view>
    <view class="card-pattern"></view>

    <view class="wallet-inner">
      <view class="card-header">
        <text class="wallet-caption">账户余额</text>
        <view class="card-chip"></view>
      </view>

      <view class="wallet-amount-row">
        <text class="wallet-yuan">¥</text>
        <text class="wallet-amount">{{ balanceText }}</text>
      </view>

      <view class="card-footer">
        <text class="wallet-id-label">{{ walletId }}</text>
        <view class="card-logo">
          <view class="logo-circle"></view>
          <view class="logo-circle logo-circle-right"></view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
defineProps({
  balanceText: {
    type: String,
    default: '0.00'
  },
  walletId: {
    type: String,
    default: '--'
  }
})
</script>

<style scoped>
.wallet-card {
  border-radius: 20rpx;
  padding: 32rpx 36rpx;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  box-shadow: 0 12rpx 32rpx rgba(102, 126, 234, 0.3);
  position: relative;
  overflow: hidden;
  height: 320rpx;
}

.card-shine {
  position: absolute;
  top: -50%;
  right: -30%;
  width: 300rpx;
  height: 300rpx;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.15) 0%, transparent 70%);
  pointer-events: none;
}

.card-pattern {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 100%;
  height: 100%;
  opacity: 0.05;
  background-image:
    repeating-linear-gradient(45deg, transparent, transparent 35rpx, rgba(255, 255, 255, 0.3) 35rpx, rgba(255, 255, 255, 0.3) 70rpx);
  pointer-events: none;
}

.wallet-inner {
  position: relative;
  z-index: 1;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 16rpx;
}

.wallet-caption {
  color: rgba(255, 255, 255, 0.9);
  font-size: 24rpx;
  font-weight: 400;
  letter-spacing: 1rpx;
}

.card-chip {
  width: 48rpx;
  height: 38rpx;
  border-radius: 6rpx;
  background: linear-gradient(135deg, #f0e68c 0%, #daa520 100%);
  position: relative;
  overflow: hidden;
}

.card-chip::before {
  content: '';
  position: absolute;
  top: 6rpx;
  left: 6rpx;
  right: 6rpx;
  bottom: 6rpx;
  border: 2rpx solid rgba(0, 0, 0, 0.1);
  border-radius: 3rpx;
}

.wallet-amount-row {
  display: flex;
  align-items: baseline;
  gap: 4rpx;
  margin-bottom: auto;
}

.wallet-yuan {
  color: #ffffff;
  font-size: 36rpx;
  font-weight: 500;
}

.wallet-amount {
  color: #ffffff;
  font-size: 64rpx;
  line-height: 1;
  font-weight: 600;
  letter-spacing: 2rpx;
}

.card-footer {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
}

.wallet-id-label {
  color: rgba(255, 255, 255, 0.8);
  font-size: 22rpx;
  font-weight: 400;
  font-family: 'Courier New', monospace;
  letter-spacing: 2rpx;
}

.card-logo {
  display: flex;
  align-items: center;
  gap: -16rpx;
  position: relative;
}

.logo-circle {
  width: 40rpx;
  height: 40rpx;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.3);
  border: 2rpx solid rgba(255, 255, 255, 0.5);
}

.logo-circle-right {
  margin-left: -16rpx;
}
</style>
