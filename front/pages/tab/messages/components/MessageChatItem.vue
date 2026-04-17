<template>
  <view class="chat-row" hover-class="chat-row-active" @tap="$emit('tap', item)">
    <view class="avatar-wrap">
      <image class="avatar" :src="item.avatar" mode="aspectFill" />
      <view v-if="item.unread > 0" class="unread-dot">{{ item.unread }}</view>
    </view>

    <view class="main">
      <view class="head-row">
        <text class="name">{{ item.name }} {{ separator }} {{ item.company }}</text>
        <text class="time">{{ item.timeText }}</text>
      </view>
      <text class="preview">{{ item.preview }}</text>
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

defineEmits(['tap'])

const separator = '\u00b7'
</script>

<style scoped>
.chat-row {
  min-height: 112rpx;
  padding: 22rpx 28rpx;
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.chat-row-active {
  background: #f8fafc;
}

.avatar-wrap {
  position: relative;
  width: 88rpx;
  height: 88rpx;
  flex-shrink: 0;
}

.avatar {
  width: 88rpx;
  height: 88rpx;
  border-radius: 18rpx;
  background: #e2e8f0;
}

.unread-dot {
  position: absolute;
  top: -4rpx;
  right: -6rpx;
  min-width: 28rpx;
  height: 28rpx;
  padding: 0 6rpx;
  border-radius: 999rpx;
  background: #ef4444;
  color: #ffffff;
  font-size: 16rpx;
  line-height: 28rpx;
  text-align: center;
  border: 2rpx solid #ffffff;
}

.main {
  flex: 1;
  min-width: 0;
}

.head-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10rpx;
}

.name {
  flex: 1;
  min-width: 0;
  color: #0f172a;
  font-size: 28rpx;
  line-height: 36rpx;
  font-weight: 600;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.time {
  flex-shrink: 0;
  color: #94a3b8;
  font-size: 20rpx;
  line-height: 28rpx;
}

.preview {
  display: block;
  margin-top: 4rpx;
  color: #64748b;
  font-size: 24rpx;
  line-height: 32rpx;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

@media (prefers-color-scheme: dark) {
  .chat-row-active {
    background: #111827;
  }

  .name {
    color: #f8fafc;
  }

  .preview {
    color: #94a3b8;
  }

  .unread-dot {
    border-color: #0f172a;
  }
}
</style>
