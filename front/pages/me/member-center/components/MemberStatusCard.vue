<template>
  <view class="status-card">
    <view class="status-glow"></view>

    <view class="status-top">
      <view>
        <text class="status-title">尊享会员 VIP</text>
        <text class="status-subtitle">全脉联 · 商务社交首选</text>
      </view>
      <view class="status-pill">
        <text class="status-pill-text">{{ status?.statusText || '未开通' }}</text>
      </view>
    </view>

    <view class="status-bottom">
      <view>
        <text class="status-expire">有效期至：{{ status?.expireDateText || '--' }}</text>
        <text class="status-slogan">升级会员，解锁无限商机</text>
      </view>
      <image class="status-vip-icon" mode="aspectFit" src="/static/me-icons/badge-primary.png" />
    </view>
  </view>
</template>

<script setup>
defineProps({
  status: {
    type: Object,
    default: () => ({})
  }
})
</script>

<style scoped>
.status-card {
  position: relative;
  overflow: hidden;
  border-radius: 24rpx;
  padding: 48rpx 40rpx 40rpx;
  background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
  border: 1rpx solid rgba(51, 65, 85, 0.6);
  box-shadow: 0 8rpx 24rpx rgba(15, 23, 42, 0.24);
  font-family: var(--member-body-font, 'PingFang SC', 'Microsoft YaHei', sans-serif);
}

.status-glow {
  position: absolute;
  width: 360rpx;
  height: 360rpx;
  right: -140rpx;
  top: -140rpx;
  border-radius: 999px;
  background: rgba(212, 175, 55, 0.1);
}

.status-top {
  position: relative;
  z-index: 1;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 32rpx;
}

.status-title {
  display: block;
  font-size: 40rpx;
  line-height: 56rpx;
  font-weight: 700;
  letter-spacing: 0.02em;
  font-family: var(--member-heading-font, 'PingFang SC', 'Microsoft YaHei', sans-serif);
  background: linear-gradient(to right, #fde68a, #d4af37);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

.status-subtitle {
  display: block;
  margin-top: 12rpx;
  color: #94a3b8;
  font-size: 24rpx;
  line-height: 36rpx;
  letter-spacing: 0.02em;
}

.status-pill {
  flex-shrink: 0;
  border-radius: 999px;
  border: 1rpx solid rgba(212, 175, 55, 0.4);
  background: rgba(212, 175, 55, 0.18);
  padding: 8rpx 24rpx;
}

.status-pill-text {
  color: #d4af37;
  font-size: 22rpx;
  line-height: 32rpx;
  font-weight: 700;
  letter-spacing: 0.02em;
}

.status-bottom {
  position: relative;
  z-index: 1;
  margin-top: 56rpx;
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 32rpx;
}

.status-expire {
  display: block;
  color: #cbd5e1;
  font-size: 24rpx;
  line-height: 36rpx;
}

.status-slogan {
  display: block;
  margin-top: 12rpx;
  color: #e2e8f0;
  font-size: 28rpx;
  line-height: 40rpx;
  font-style: normal;
  font-weight: 600;
  letter-spacing: 0.02em;
  font-family: var(--member-heading-font, 'PingFang SC', 'Microsoft YaHei', sans-serif);
}

.status-vip-icon {
  width: 96rpx;
  height: 96rpx;
  opacity: 0.44;
  flex-shrink: 0;
}
</style>
