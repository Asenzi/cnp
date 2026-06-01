<template>
  <view class="circle-card" hover-class="circle-card-active" @tap="$emit('enter', item)">
    <image v-if="item.coverUrl" class="cover cover-image" :src="item.coverUrl" mode="aspectFill" />
    <view v-else class="cover"></view>
    <view class="meta">
      <text class="name">{{ item.name }}</text>
      <view class="sub-row">
        <text class="sub-text">{{ item.members }} 人</text>
        <text class="dot">·</text>
        <text class="sub-text">{{ item.role }}</text>
      </view>
      <text v-if="item.industryLabel" class="industry-text">{{ item.industryLabel }}</text>
    </view>
  </view>
</template>

<script setup>
defineProps({
  item: {
    type: Object,
    default: () => ({})
  }
})

defineEmits(['enter'])
</script>

<style scoped>
.circle-card {
  display: flex;
  align-items: center;
  gap: 16rpx;
  border-radius: 16rpx;
  border: 1rpx solid rgba(0, 0, 0, 0.06);
  background: #ffffff;
  padding: 16rpx;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.04), 0 1rpx 2rpx rgba(0, 0, 0, 0.02);
  transition: all 0.2s ease;
}

.circle-card-active {
  transform: scale(0.98);
  box-shadow: 0 1rpx 4rpx rgba(0, 0, 0, 0.06);
}

.cover {
  width: 104rpx;
  height: 104rpx;
  border-radius: 12rpx;
  background: linear-gradient(135deg, #1a57db 0%, #60a5fa 100%);
  flex-shrink: 0;
}

.cover-image {
  background: #f3f4f6;
}

.meta {
  flex: 1;
  min-width: 0;
}

.name {
  color: #111827;
  font-size: 28rpx;
  line-height: 36rpx;
  font-weight: 600;
}

.sub-row {
  margin-top: 8rpx;
  display: flex;
  align-items: center;
  gap: 8rpx;
}

.sub-text,
.dot {
  color: #6b7280;
  font-size: 24rpx;
  line-height: 32rpx;
}

.industry-text {
  margin-top: 4rpx;
  display: block;
  color: #9ca3af;
  font-size: 22rpx;
  line-height: 30rpx;
}

@media (prefers-color-scheme: dark) {
  .circle-card {
    background: #0f172a;
    border-color: #1e293b;
  }

  .name {
    color: #f8fafc;
  }

  .sub-text,
  .dot {
    color: #94a3b8;
  }

  .industry-text {
    color: #64748b;
  }
}
</style>
