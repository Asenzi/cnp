<template>
  <view class="request-card" :class="request.faded ? 'request-card-faded' : ''">
    <view class="card-row">
      <view class="avatar-wrap">
        <image class="avatar" :src="request.avatar" mode="aspectFill" />
        <view v-if="request.unread" class="unread-dot"></view>
      </view>

      <view class="main">
        <view class="head-row">
          <text class="name-line">
            {{ request.name }}
            <text class="split"> | </text>
            <text class="role">{{ request.role }}</text>
          </text>
          <text class="time">{{ request.timeText }}</text>
        </view>

        <text class="message">{{ request.message }}</text>

        <view v-if="request.canOperate !== false" class="action-row">
          <button class="accept-btn" hover-class="accept-btn-active" @tap="$emit('accept', request)">接受</button>
          <button class="ignore-btn" hover-class="ignore-btn-active" @tap="$emit('ignore', request)">忽略</button>
        </view>
        <view v-else class="sent-row">
          <text class="sent-text">{{ statusText }}</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  request: {
    type: Object,
    default: () => ({})
  }
})

defineEmits(['accept', 'ignore'])

const statusText = computed(() => {
  const status = String(props.request?.status || 'pending').trim().toLowerCase()
  if (status === 'accepted') {
    return '对方已通过'
  }
  if (status === 'ignored') {
    return '对方暂未通过'
  }
  return '等待对方处理'
})
</script>

<style scoped>
.request-card {
  padding: 24rpx;
  border-bottom: 1rpx solid rgba(26, 87, 219, 0.08);
}

.request-card-faded {
  opacity: 0.9;
}

.card-row {
  display: flex;
  align-items: flex-start;
  gap: 16rpx;
}

.avatar-wrap {
  width: 112rpx;
  height: 112rpx;
  position: relative;
  flex-shrink: 0;
}

.avatar {
  width: 112rpx;
  height: 112rpx;
  border-radius: 999rpx;
  background: #e2e8f0;
}

.unread-dot {
  position: absolute;
  right: 2rpx;
  top: 2rpx;
  width: 18rpx;
  height: 18rpx;
  border-radius: 999rpx;
  background: #ef4444;
  border: 2rpx solid #f8f6f6;
}

.main {
  flex: 1;
  min-width: 0;
}

.head-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12rpx;
}

.name-line {
  flex: 1;
  min-width: 0;
  color: #0f172a;
  font-size: 30rpx;
  line-height: 40rpx;
  font-weight: 700;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.split {
  color: #cbd5e1;
  font-weight: 400;
}

.role {
  color: #475569;
  font-size: 24rpx;
  line-height: 34rpx;
  font-weight: 500;
}

.time {
  color: #94a3b8;
  font-size: 18rpx;
  line-height: 28rpx;
  flex-shrink: 0;
}

.message {
  margin-top: 4rpx;
  color: #64748b;
  font-size: 24rpx;
  line-height: 34rpx;
  display: -webkit-box;
  overflow: hidden;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.action-row {
  margin-top: 16rpx;
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.accept-btn,
.ignore-btn {
  flex: 1;
  height: 72rpx;
  border-radius: 14rpx;
  border: 0;
  font-size: 26rpx;
  line-height: 72rpx;
  font-weight: 700;
}

.accept-btn::after,
.ignore-btn::after {
  border: 0;
}

.accept-btn {
  color: #ffffff;
  background: #1a57db;
}

.ignore-btn {
  color: #1a57db;
  background: rgba(26, 87, 219, 0.12);
}

.accept-btn-active,
.ignore-btn-active {
  opacity: 0.85;
}

.sent-row {
  margin-top: 16rpx;
  height: 56rpx;
  border-radius: 12rpx;
  background: #f1f5f9;
  display: flex;
  align-items: center;
  justify-content: center;
}

.sent-text {
  color: #64748b;
  font-size: 22rpx;
  line-height: 30rpx;
  font-weight: 600;
}

@media (prefers-color-scheme: dark) {
  .request-card {
    border-bottom-color: rgba(59, 130, 246, 0.18);
  }

  .name-line {
    color: #f8fafc;
  }

  .role {
    color: #cbd5e1;
  }

  .message {
    color: #9ca3af;
  }

  .unread-dot {
    border-color: #221610;
  }

  .accept-btn {
    background: #2563eb;
  }

  .ignore-btn {
    color: #60a5fa;
    background: rgba(37, 99, 235, 0.24);
  }

  .sent-row {
    background: #312019;
  }

  .sent-text {
    color: #9ca3af;
  }
}
</style>
