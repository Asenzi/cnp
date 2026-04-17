<template>
  <view class="file-bubble" :class="self ? 'file-bubble-self' : ''" @tap="$emit('tap-file', file)">
    <view class="file-icon-wrap">
      <ChatGlyph name="file" :size="20" :color="self ? '#1a57db' : '#475569'" />
    </view>
    <view class="file-meta">
      <text class="file-name">{{ file.name }}</text>
      <text class="file-size">{{ formatSize(file.size) }}</text>
    </view>
  </view>
</template>

<script setup>
import ChatGlyph from './ChatGlyph.vue'

defineProps({
  file: {
    type: Object,
    default: () => ({})
  },
  self: {
    type: Boolean,
    default: false
  }
})

defineEmits(['tap-file'])

const formatSize = (size) => {
  const value = Number(size || 0)
  if (value <= 0) {
    return '未知大小'
  }
  if (value < 1024) {
    return `${value}B`
  }
  if (value < 1024 * 1024) {
    return `${(value / 1024).toFixed(1)}KB`
  }
  return `${(value / (1024 * 1024)).toFixed(1)}MB`
}
</script>

<style scoped>
.file-bubble {
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

.file-bubble-self {
  border-top-left-radius: 20rpx;
  border-top-right-radius: 8rpx;
  border-color: #d7e4ff;
}

.file-icon-wrap {
  width: 56rpx;
  height: 56rpx;
  border-radius: 12rpx;
  background: #e2e8f0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.file-meta {
  min-width: 0;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4rpx;
}

.file-name {
  color: #0f172a;
  font-size: 24rpx;
  line-height: 34rpx;
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-size {
  color: #64748b;
  font-size: 20rpx;
  line-height: 28rpx;
}

@media (prefers-color-scheme: dark) {
  .file-bubble {
    background: #1f2937;
    border-color: #334155;
  }

  .file-icon-wrap {
    background: #334155;
  }

  .file-name {
    color: #e2e8f0;
  }

  .file-size {
    color: #94a3b8;
  }
}
</style>
