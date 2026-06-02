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
  border: 0;
  border-radius: 16rpx;
  padding: 28rpx;
  display: flex;
  flex-direction: column;
  gap: 20rpx;
  box-shadow: none;
  transition: all 0.2s ease;
}

.benefit-card:active {
  transform: scale(0.98);
  box-shadow: none;
}

.is-wide {
  grid-column: span 2;
  flex-direction: row;
  align-items: center;
}

.benefit-icon {
  width: 72rpx;
  height: 72rpx;
  background: linear-gradient(135deg, #e8f1ff 0%, #d7e6fb 100%);
  border-radius: 14rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: none;
}

.icon-img {
  width: 40rpx;
  height: 40rpx;
}

.icon-text {
  color: #2f5fbd;
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
  font-size: 24rpx;
  line-height: 32rpx;
  font-weight: 500;
  margin-bottom: 6rpx;
}

.benefit-desc {
  display: block;
  color: #6b7280;
  font-size: 22rpx;
  line-height: 32rpx;
}
</style>
