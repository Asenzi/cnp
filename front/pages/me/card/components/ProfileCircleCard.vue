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
  gap: 18rpx;
  border-radius: 20rpx;
  border: 1rpx solid #f1f5f9;
  background: #ffffff;
  padding: 18rpx;
}

.circle-card-active {
  opacity: 0.9;
}

.cover {
  width: 110rpx;
  height: 110rpx;
  border-radius: 16rpx;
  background: linear-gradient(135deg, #1a57db 0%, #60a5fa 100%);
  flex-shrink: 0;
}

.cover-image {
  background: #e2e8f0;
}

.meta {
  flex: 1;
  min-width: 0;
}

.name {
  color: #0f172a;
  font-size: 28rpx;
  line-height: 36rpx;
  font-weight: 700;
}

.sub-row {
  margin-top: 6rpx;
  display: flex;
  align-items: center;
  gap: 8rpx;
}

.sub-text,
.dot {
  color: #64748b;
  font-size: 22rpx;
  line-height: 30rpx;
}

.industry-text {
  margin-top: 4rpx;
  display: block;
  color: #94a3b8;
  font-size: 20rpx;
  line-height: 28rpx;
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
