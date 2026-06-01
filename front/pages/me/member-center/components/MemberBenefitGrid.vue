<template>
  <view class="benefit-grid">
    <view
      v-for="item in items"
      :key="item.key"
      class="benefit-card"
      :class="{ 'is-wide': item.wide }"
    >
      <view class="benefit-icon">
        <image v-if="item.iconPath" class="icon-img" mode="aspectFit" :src="item.iconPath" />
        <text v-else class="icon-text">{{ item.iconText || '会' }}</text>
      </view>
      <view class="benefit-content">
        <text class="benefit-title">{{ item.title }}</text>
        <text class="benefit-desc">{{ item.desc }}</text>
      </view>
    </view>
  </view>
</template>

<script setup>
defineProps({
  items: {
    type: Array,
    default: () => []
  }
})
</script>

<style scoped>
.benefit-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16rpx;
}

.benefit-card {
  background: #ffffff;
  border: 1rpx solid #e5e7eb;
  border-radius: 16rpx;
  padding: 28rpx;
  display: flex;
  flex-direction: column;
  gap: 20rpx;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.04), 0 1rpx 2rpx rgba(0, 0, 0, 0.02);
  transition: all 0.2s ease;
}

.benefit-card:active {
  transform: scale(0.98);
  box-shadow: 0 1rpx 4rpx rgba(0, 0, 0, 0.06);
}

.is-wide {
  grid-column: span 2;
  flex-direction: row;
  align-items: center;
}

.benefit-icon {
  width: 72rpx;
  height: 72rpx;
  background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
  border-radius: 14rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 2rpx 8rpx rgba(59, 130, 246, 0.15), inset 0 1rpx 0 rgba(255, 255, 255, 0.5);
}

.icon-img {
  width: 40rpx;
  height: 40rpx;
}

.icon-text {
  color: #1a57db;
  font-size: 28rpx;
  font-weight: 700;
}

.benefit-content {
  flex: 1;
  min-width: 0;
}

.benefit-title {
  display: block;
  color: #111827;
  font-size: 28rpx;
  line-height: 36rpx;
  font-weight: 600;
  margin-bottom: 6rpx;
}

.benefit-desc {
  display: block;
  color: #6b7280;
  font-size: 24rpx;
  line-height: 32rpx;
}
</style>
