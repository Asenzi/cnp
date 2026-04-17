<template>
  <view class="card-bubble" :class="self ? 'card-bubble-self' : ''">
    <view class="card-body">
      <view class="card-meta">
        <text class="card-name">{{ card.name }}</text>
        <text class="card-subtitle">{{ card.subtitle }}</text>
        <button class="profile-btn" hover-class="profile-btn-active" @tap="$emit('tap-card', card)">
          <ChatGlyph name="card" :size="14" color="#334155" />
          <text class="profile-btn-text">查看个人主页</text>
        </button>
      </view>

      <image class="card-avatar" :src="card.avatar || '/static/logo.png'" mode="aspectFill" />
    </view>
  </view>
</template>

<script setup>
import ChatGlyph from './ChatGlyph.vue'

defineProps({
  self: {
    type: Boolean,
    default: false
  },
  card: {
    type: Object,
    default: () => ({})
  }
})

defineEmits(['tap-card'])
</script>

<style scoped>
.card-bubble {
  width: 100%;
  border-radius: 20rpx;
  border: 1rpx solid #eef2f7;
  background: #ffffff;
  box-shadow: 0 4rpx 12rpx rgba(15, 23, 42, 0.04);
}

.card-bubble-self {
  border-color: #dce6fb;
}

.card-body {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14rpx;
  padding: 20rpx;
}

.card-meta {
  min-width: 0;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 8rpx;
}

.card-name {
  color: #0f172a;
  font-size: 29rpx;
  line-height: 38rpx;
  font-weight: 700;
}

.card-subtitle {
  color: #64748b;
  font-size: 21rpx;
  line-height: 30rpx;
}

.profile-btn {
  margin: 0;
  padding: 0 16rpx;
  height: 54rpx;
  border-radius: 12rpx;
  border: 0;
  background: #f1f5f9;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8rpx;
}

.profile-btn::after {
  border: 0;
}

.profile-btn-active {
  opacity: 0.85;
}

.profile-btn-text {
  color: #1f2937;
  font-size: 19rpx;
  line-height: 26rpx;
  font-weight: 600;
}

.card-avatar {
  width: 108rpx;
  height: 108rpx;
  border-radius: 12rpx;
  background: #e5e7eb;
  flex-shrink: 0;
}

@media (prefers-color-scheme: dark) {
  .card-bubble {
    border-color: #1f2937;
    background: #111827;
    box-shadow: none;
  }

  .card-name {
    color: #f8fafc;
  }

  .card-subtitle {
    color: #94a3b8;
  }

  .profile-btn {
    background: #1f2937;
  }

  .profile-btn-text {
    color: #e2e8f0;
  }

  .card-avatar {
    background: #334155;
  }
}
</style>
