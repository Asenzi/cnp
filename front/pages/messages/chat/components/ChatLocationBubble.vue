<template>
  <view class="location-bubble" :class="self ? 'location-bubble-self' : ''" @tap="$emit('tap-location', location)">
    <view class="location-icon">
      <ChatGlyph name="location" :size="20" :color="self ? '#1a57db' : '#475569'" />
    </view>
    <view class="location-meta">
      <text class="location-name">{{ location.name }}</text>
      <text class="location-address">{{ location.address || '点击查看地图位置' }}</text>
    </view>
  </view>
</template>

<script setup>
import ChatGlyph from './ChatGlyph.vue'

defineProps({
  location: {
    type: Object,
    default: () => ({})
  },
  self: {
    type: Boolean,
    default: false
  }
})

defineEmits(['tap-location'])
</script>

<style scoped>
.location-bubble {
  min-width: 280rpx;
  max-width: 460rpx;
  border-radius: 20rpx;
  border-top-left-radius: 8rpx;
  background: #f8fafc;
  border: 1rpx solid #e2e8f0;
  padding: 18rpx;
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.location-bubble-self {
  border-top-left-radius: 20rpx;
  border-top-right-radius: 8rpx;
  border-color: #d7e4ff;
}

.location-icon {
  width: 56rpx;
  height: 56rpx;
  border-radius: 12rpx;
  background: #e2e8f0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.location-meta {
  min-width: 0;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4rpx;
}

.location-name {
  color: #0f172a;
  font-size: 24rpx;
  line-height: 34rpx;
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.location-address {
  color: #64748b;
  font-size: 20rpx;
  line-height: 28rpx;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

@media (prefers-color-scheme: dark) {
  .location-bubble {
    background: #1f2937;
    border-color: #334155;
  }

  .location-icon {
    background: #334155;
  }

  .location-name {
    color: #e2e8f0;
  }

  .location-address {
    color: #94a3b8;
  }
}
</style>
