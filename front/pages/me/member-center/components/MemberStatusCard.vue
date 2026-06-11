<template>
  <view class="status-card">
    <view class="status-glow"></view>

    <view class="status-top">
      <view>
        <text class="status-title">尊享会员 VIP</text>
        <text class="status-subtitle">圈脉链 · 商务社交首选</text>
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
  padding: 40rpx 40rpx 40rpx 10rpx;
  color: #111827;
  border: 0;
  box-shadow: none;
  font-family: var(--member-body-font, 'PingFang SC', 'Microsoft YaHei', sans-serif);
}

.status-glow {
  position: absolute;
  width: 360rpx;
  height: 360rpx;
  right: -140rpx;
  top: -140rpx;
  border-radius: 999px;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.2) 0%, transparent 70%);
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
}

.status-subtitle {
  display: block;
  margin-top: 12rpx;
  /* color: rgba(255, 255, 255, 0.8) ; */
  font-size: 24rpx;
  line-height: 36rpx;
  letter-spacing: 0.02em;
}

.status-pill {
  flex-shrink: 0;
  border-radius: 999px;
  border: 0;
  background: rgba(255, 255, 255, 0.2);
  -webkit-backdrop-filter: blur(10rpx);
  backdrop-filter: blur(10rpx);
  min-width: 104rpx;
  height: 48rpx;
  padding: 6rpx 10rpx;
  box-shadow: none;
  display: flex;
  align-items: center;
  justify-content: center;
}

.status-pill-text {
  /* color: #ffffff ; */
  font-size: 22rpx;
  line-height: 48rpx;
  font-weight: 700;
  letter-spacing: 0.02em;
  text-align: center;
}

.status-bottom {
  position: relative;
  z-index: 1;
  margin-top: 56rpx;
  display: block;
}

.status-expire {
  display: block;
  /* color: rgba(255, 255, 255, 0.85) ; */
  font-size: 24rpx;
  line-height: 36rpx;
}

.status-slogan {
  display: block;
  margin-top: 12rpx;
  /* color: #ffffff ; */
  font-size: 28rpx;
  line-height: 40rpx;
  font-style: normal;
  font-weight: 600;
  letter-spacing: 0.02em;
  font-family: var(--member-heading-font, 'PingFang SC', 'Microsoft YaHei', sans-serif);
}

</style>
