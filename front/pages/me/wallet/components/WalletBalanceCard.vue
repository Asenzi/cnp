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
          <image class="wallet-icon" mode="aspectFit" src="/static/me-icons/payments-green.png" />
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
  border-radius: 48rpx;
  padding: 56rpx 48rpx;
  background: #1a57db;
  box-shadow: 0 18rpx 40rpx rgba(26, 87, 219, 0.25);
}

.wallet-glow {
  position: absolute;
  border-radius: 999rpx;
}

.wallet-glow-right {
  width: 520rpx;
  height: 520rpx;
  right: -180rpx;
  top: -180rpx;
  background: rgba(255, 255, 255, 0.1);
  filter: blur(20rpx);
}

.wallet-glow-left {
  width: 420rpx;
  height: 420rpx;
  left: -130rpx;
  bottom: -180rpx;
  background: rgba(96, 165, 250, 0.2);
  filter: blur(24rpx);
}

.wallet-inner {
  position: relative;
  z-index: 1;
}

.wallet-caption {
  display: block;
  color: #bfdbfe;
  font-size: 24rpx;
  font-weight: 600;
}

.wallet-amount-row {
  margin-top: 12rpx;
  display: flex;
  align-items: baseline;
  gap: 8rpx;
}

.wallet-yuan {
  color: #bfdbfe;
  font-size: 40rpx;
  font-weight: 700;
}

.wallet-amount {
  color: #ffffff;
  font-size: 72rpx;
  line-height: 1.05;
  font-weight: 800;
  letter-spacing: 1rpx;
}

.wallet-footer {
  margin-top: 56rpx;
  padding-top: 24rpx;
  border-top: 1rpx solid rgba(255, 255, 255, 0.15);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.wallet-id-wrap {
  display: flex;
  flex-direction: column;
  gap: 6rpx;
}

.wallet-id-label {
  color: #bfdbfe;
  font-size: 18rpx;
  font-weight: 700;
  letter-spacing: 2rpx;
  text-transform: uppercase;
}

.wallet-id-value {
  color: #ffffff;
  font-size: 24rpx;
  font-weight: 600;
}

.wallet-icon-wrap {
  width: 64rpx;
  height: 64rpx;
  border-radius: 20rpx;
  background: rgba(255, 255, 255, 0.12);
  display: flex;
  align-items: center;
  justify-content: center;
}

.wallet-icon {
  width: 38rpx;
  height: 38rpx;
}
</style>
