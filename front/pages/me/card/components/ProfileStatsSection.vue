<template>
  <view class="stats-wrap">
    <view v-for="item in stats" :key="item.key" class="stat-card">
      <text class="stat-value">{{ item.value }}</text>
      <text class="stat-label">{{ item.label }}</text>
    </view>
  </view>
</template>

<script setup>
defineProps({
  stats: {
    type: Array,
    default: () => []
  }
})
</script>

<style scoped>
.stats-wrap {
  background: #ffffff;
  padding: 0 32rpx 32rpx;
  display: flex;
  justify-content: flex-start;
  flex-wrap: nowrap;
  gap: 16rpx;
}

.stat-card {
  flex: 0 0 168rpx;
  width: 168rpx;
  border-radius: 16rpx;
  padding: 20rpx 16rpx;
  background: rgba(26, 87, 219, 0.04);
  border: 1rpx solid rgba(26, 87, 219, 0.08);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8rpx;
  min-height: 104rpx;
  text-align: center;
}

.stat-value {
  color: #111827;
  font-size: 32rpx;
  line-height: 40rpx;
  font-weight: 600;
}

.stat-label {
  color: #6b7280;
  font-size: 24rpx;
  line-height: 32rpx;
}

@media (prefers-color-scheme: dark) {
  .stats-wrap {
    background: rgba(15, 23, 42, 0.82);
  }

  .stat-card {
    border-color: rgba(26, 87, 219, 0.25);
    background: rgba(26, 87, 219, 0.12);
  }

  .stat-label {
    color: #94a3b8;
  }

  .stat-value {
    color: #f8fafc;
  }
}
</style>
