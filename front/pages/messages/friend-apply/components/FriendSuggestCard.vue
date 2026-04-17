<template>
  <view class="suggest-card" hover-class="suggest-card-active" @tap="$emit('tap', user)">
    <image class="avatar" :src="user.avatar" mode="aspectFill" />
    <text class="name">{{ user.name }}</text>
    <text class="meta">共同好友 {{ user.mutualCount }}位</text>
    <button class="add-btn" hover-class="add-btn-active" @tap.stop="$emit('add', user)">添加好友</button>
  </view>
</template>

<script setup>
defineProps({
  user: {
    type: Object,
    default: () => ({})
  }
})

defineEmits(['tap', 'add'])
</script>

<style scoped>
.suggest-card {
  border-radius: 20rpx;
  border: 1rpx solid rgba(26, 87, 219, 0.1);
  background: #ffffff;
  padding: 24rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.suggest-card-active {
  opacity: 0.9;
}

.avatar {
  width: 128rpx;
  height: 128rpx;
  border-radius: 999rpx;
  background: #e2e8f0;
}

.name {
  margin-top: 12rpx;
  color: #0f172a;
  font-size: 28rpx;
  line-height: 36rpx;
  font-weight: 700;
}

.meta {
  margin-top: 6rpx;
  color: #64748b;
  font-size: 22rpx;
  line-height: 30rpx;
}

.add-btn {
  margin-top: 14rpx;
  width: 100%;
  height: 64rpx;
  border-radius: 12rpx;
  border: 0;
  background: rgba(26, 87, 219, 0.12);
  color: #1a57db;
  font-size: 22rpx;
  line-height: 64rpx;
  font-weight: 700;
}

.add-btn::after {
  border: 0;
}

.add-btn-active {
  opacity: 0.86;
}

@media (prefers-color-scheme: dark) {
  .suggest-card {
    background: #312019;
    border-color: rgba(59, 130, 246, 0.2);
  }

  .name {
    color: #f8fafc;
  }

  .meta {
    color: #9ca3af;
  }

  .add-btn {
    color: #60a5fa;
    background: rgba(37, 99, 235, 0.24);
  }
}
</style>
