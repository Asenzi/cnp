<template>
  <view class="owner-wrap">
    <view class="owner-main">
      <image class="owner-avatar" mode="aspectFill" :src="owner.avatar" />
      <view class="owner-info">
        <view class="name-row">
          <text class="owner-name">{{ owner.name }} ({{ owner.role }})</text>
          <image class="verified-icon" mode="aspectFit" src="/static/me-icons/verified-emerald.png" />
        </view>
        <text class="owner-intro">{{ owner.intro }}</text>
      </view>
    </view>

    <button class="dm-btn" hover-class="dm-btn-active" @tap="emit('dm')">私信</button>
  </view>
</template>

<script setup>
defineProps({
  owner: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['dm'])
</script>

<style scoped>
.owner-wrap {
  margin: 16rpx 32rpx 0;
  background: #ffffff;
  border-radius: 16rpx;
  border: 1rpx solid #e2e8f0;
  padding: 18rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14rpx;
}

.owner-main {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.owner-avatar {
  width: 88rpx;
  height: 88rpx;
  border-radius: 999rpx;
  background: #e2e8f0;
  flex-shrink: 0;
}

.owner-info {
  flex: 1;
  min-width: 0;
}

.name-row {
  display: flex;
  align-items: center;
  gap: 6rpx;
}

.owner-name {
  max-width: 380rpx;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: #0f172a;
  font-size: 24rpx;
  line-height: 32rpx;
  font-weight: 700;
}

.verified-icon {
  width: 22rpx;
  height: 22rpx;
  flex-shrink: 0;
}

.owner-intro {
  display: block;
  margin-top: 4rpx;
  color: #64748b;
  font-size: 20rpx;
  line-height: 28rpx;
}

.dm-btn {
  height: 60rpx;
  border-radius: 12rpx;
  border: 0;
  padding: 0 20rpx;
  background: rgba(26, 87, 219, 0.1);
  color: #1a57db;
  font-size: 22rpx;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.dm-btn-active {
  opacity: 0.84;
}

@media (prefers-color-scheme: dark) {
  .owner-wrap {
    background: #0f172a;
    border-color: #1e293b;
  }

  .owner-name {
    color: #f8fafc;
  }

  .owner-intro {
    color: #94a3b8;
  }
}
</style>
