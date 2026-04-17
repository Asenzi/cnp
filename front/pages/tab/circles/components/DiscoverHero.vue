<template>
  <view class="hero-wrap">
    <view class="hero-card">
      <image class="hero-image" mode="aspectFill" :src="banner.image" />
      <view class="hero-mask"></view>
      <view class="hero-content">
        <text class="hero-label">{{ banner.label }}</text>
        <text class="hero-title">{{ banner.titleLine1 }}</text>
        <text class="hero-title">{{ banner.titleLine2 }}</text>
        <text class="hero-desc">{{ banner.desc }}</text>
      </view>
    </view>
  </view>
</template>

<script setup>
defineProps({
  banner: {
    type: Object,
    default: () => ({})
  }
})
</script>

<style scoped>
.hero-wrap {
  padding: 16rpx 32rpx 0;
}

.hero-card {
  position: relative;
  height: 300rpx;
  border-radius: 24rpx;
  overflow: hidden;
  box-shadow: 0 10rpx 24rpx rgba(15, 23, 42, 0.16);
}

.hero-image {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

.hero-mask {
  position: absolute;
  inset: 0;
  background: linear-gradient(to right, rgba(26, 87, 219, 0.9), rgba(26, 87, 219, 0.1));
}

.hero-content {
  position: relative;
  z-index: 2;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 0 34rpx;
  color: #ffffff;
}

.hero-label {
  align-self: flex-start;
  border-radius: 999rpx;
  padding: 3rpx 12rpx;
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(8rpx);
  font-size: 18rpx;
  line-height: 24rpx;
  text-transform: uppercase;
  letter-spacing: 2rpx;
  font-weight: 700;
  margin-bottom: 10rpx;
}

.hero-title {
  font-size: 40rpx;
  line-height: 46rpx;
  font-weight: 700;
}

.hero-desc {
  margin-top: 6rpx;
  color: rgba(255, 255, 255, 0.85);
  font-size: 22rpx;
  line-height: 30rpx;
}
</style>

