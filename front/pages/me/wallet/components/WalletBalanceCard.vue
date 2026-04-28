<template>
  <view class="wallet-card">
    <view class="wallet-glow wallet-glow-right"></view>
    <view class="wallet-glow wallet-glow-left"></view>

    <view class="wallet-inner">
      <text class="wallet-caption">账户总余额</text>

      <view class="wallet-amount-row">
        <text class="wallet-yuan">¥</text>
        <text class="wallet-amount">{{ balanceText }}</text>
      </view>

      <view class="wallet-footer">
        <view class="wallet-id-wrap">
          <text class="wallet-id-label">钱包ID</text>
          <text class="wallet-id-value">{{ walletId }}</text>
        </view>
        <view class="wallet-icon-wrap">
          <image class="wallet-icon" mode="aspectFit" src="/static/icon/wallet.png" />
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
  position: relative;
  overflow: hidden;
  border-radius: 28rpx;
  padding: 56rpx 44rpx;
  background: linear-gradient(135deg, #1a57db 0%, #1e40af 100%);
  box-shadow: 0 16rpx 40rpx rgba(26, 87, 219, 0.3);
}

.wallet-card::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, transparent 50%);
  opacity: 0.5;
}

.wallet-glow {
  position: absolute;
  border-radius: 999rpx;
  pointer-events: none;
}

.wallet-glow-right {
  width: 500rpx;
  height: 500rpx;
  right: -180rpx;
  top: -180rpx;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.15) 0%, transparent 70%);
  filter: blur(30rpx);
}

.wallet-glow-left {
  width: 400rpx;
  height: 400rpx;
  left: -140rpx;
  bottom: -180rpx;
  background: radial-gradient(circle, rgba(96, 165, 250, 0.25) 0%, transparent 70%);
  filter: blur(35rpx);
}

.wallet-inner {
  position: relative;
  z-index: 1;
}

.wallet-caption {
  display: block;
  color: rgba(255, 255, 255, 0.8);
  font-size: 24rpx;
  font-weight: 600;
  letter-spacing: 0.5rpx;
  text-transform: uppercase;
}

.wallet-amount-row {
  margin-top: 16rpx;
  display: flex;
  align-items: baseline;
  gap: 8rpx;
}

.wallet-yuan {
  color: rgba(255, 255, 255, 0.9);
  font-size: 40rpx;
  font-weight: 700;
}

.wallet-amount {
  color: #ffffff;
  font-size: 72rpx;
  line-height: 1;
  font-weight: 800;
  letter-spacing: 2rpx;
  text-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.15);
}

.wallet-footer {
  margin-top: 56rpx;
  padding-top: 24rpx;
  border-top: 1rpx solid rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.wallet-id-wrap {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.wallet-id-label {
  color: rgba(255, 255, 255, 0.7);
  font-size: 20rpx;
  font-weight: 700;
  letter-spacing: 2rpx;
  text-transform: uppercase;
}

.wallet-id-value {
  color: #ffffff;
  font-size: 26rpx;
  font-weight: 600;
  letter-spacing: 1rpx;
}

.wallet-icon-wrap {
  width: 64rpx;
  height: 64rpx;
  border-radius: 18rpx;
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(10rpx);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.1);
}

.wallet-icon {
  width: 36rpx;
  height: 36rpx;
}
</style>
