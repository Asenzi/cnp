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
  padding: 0 32rpx 24rpx;
  display: flex;
  justify-content: flex-start;
  flex-wrap: nowrap;
  gap: 12rpx;
}

.stat-card {
  flex: 0 0 172rpx;
  width: 172rpx;
  border-radius: 18rpx;
  padding: 16rpx 12rpx;
  background: rgba(26, 87, 219, 0.05);
  border: 1rpx solid rgba(26, 87, 219, 0.12);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4rpx;
  min-height: 108rpx;
  text-align: center;
}

.stat-value {
  color: #0f172a;
  font-size: 32rpx;
  line-height: 40rpx;
  font-weight: 700;
}

.stat-label {
  color: #64748b;
  font-size: 20rpx;
  line-height: 28rpx;
  font-weight: 500;
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
