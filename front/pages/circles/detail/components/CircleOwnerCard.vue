<template>
  <view class="owner-wrap">
    <view class="owner-main">
      <image class="owner-avatar" mode="aspectFill" :src="owner.avatar" />
      <view class="owner-info">
        <text class="owner-name">{{ owner.name }} <text class="owner-role">{{ owner.role }}</text></text>
        <text class="owner-intro">{{ owner.intro }}</text>
      </view>
    </view>

    <button class="share-btn" open-type="share" hover-class="share-btn-active">
      <image class="share-icon" mode="aspectFit" src="/static/icon/share.png" />
    </button>
  </view>
</template>

<script setup>
defineProps({
  owner: {
    type: Object,
    default: () => ({})
  }
})
</script>

<style scoped>
.owner-wrap {
  margin: 0 32rpx;
  padding: 20rpx 0;
  border-bottom: 1rpx solid #f3f4f6;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
}

.owner-main {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.owner-avatar {
  width: 72rpx;
  height: 72rpx;
  border-radius: 8rpx;
  background: #f3f4f6;
  flex-shrink: 0;
}

.owner-info {
  flex: 1;
  min-width: 0;
}

.owner-name {
  display: block;
  color: #111827;
  font-size: 26rpx;
  line-height: 34rpx;
  font-weight: 500;
}

.owner-role {
  color: #6b7280;
  font-weight: 400;
}

.owner-intro {
  display: block;
  margin-top: 2rpx;
  color: #9ca3af;
  font-size: 22rpx;
  line-height: 30rpx;
}

.share-btn {
  width: 56rpx;
  height: 56rpx;
  padding: 0;
  border: 0;
  border-radius: 8rpx;
  background: #eff6ff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.share-btn::after {
  border: 0;
}

.share-icon {
  width: 32rpx;
  height: 32rpx;
}

.share-btn-active {
  opacity: 0.6;
}

@media (prefers-color-scheme: dark) {
  .owner-wrap {
    border-bottom-color: #1f2937;
  }

  .owner-avatar {
    background: #1f2937;
  }

  .owner-name {
    color: #f9fafb;
  }

  .owner-role {
    color: #9ca3af;
  }

  .owner-intro {
    color: #6b7280;
  }

  .share-btn {
    background: rgba(37, 99, 235, 0.15);
  }
}
</style>
