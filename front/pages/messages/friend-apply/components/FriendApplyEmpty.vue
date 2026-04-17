<template>
  <view class="empty-wrap">
    <view class="empty-icon-shell">
      <view class="icon-head"></view>
      <view class="icon-body"></view>
      <view class="icon-plus-h"></view>
      <view class="icon-plus-v"></view>
    </view>
    <text class="empty-title">暂无待处理申请</text>
    <text class="empty-desc">当有人向你发起好友申请时，会显示在这里</text>
    <button class="action-btn" hover-class="action-btn-active" @tap="$emit('discover')">去发现新朋友</button>
  </view>
</template>

<script setup>
defineEmits(['discover'])
</script>

<style scoped>
.empty-wrap {
  min-height: 520rpx;
  padding: 80rpx 48rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.empty-icon-shell {
  position: relative;
  width: 180rpx;
  height: 180rpx;
  border-radius: 999rpx;
  background: linear-gradient(135deg, rgba(26, 87, 219, 0.35), rgba(26, 87, 219, 0.08));
}

.empty-icon-shell view {
  position: absolute;
  box-sizing: border-box;
}

.icon-head {
  left: 34%;
  top: 24%;
  width: 32%;
  height: 32%;
  border: 4rpx solid #1a57db;
  border-radius: 999rpx;
}

.icon-body {
  left: 28%;
  top: 60%;
  width: 44%;
  height: 24%;
  border: 4rpx solid #1a57db;
  border-bottom: 0;
  border-radius: 999rpx 999rpx 0 0;
}

.icon-plus-h {
  right: 20%;
  top: 44%;
  width: 24%;
  border-top: 4rpx solid #1a57db;
}

.icon-plus-v {
  right: 31%;
  top: 33%;
  height: 24%;
  border-left: 4rpx solid #1a57db;
}

.empty-title {
  margin-top: 30rpx;
  color: #1f2937;
  font-size: 32rpx;
  line-height: 42rpx;
  font-weight: 700;
}

.empty-desc {
  margin-top: 12rpx;
  color: #64748b;
  font-size: 24rpx;
  line-height: 34rpx;
}

.action-btn {
  margin-top: 36rpx;
  height: 84rpx;
  padding: 0 48rpx;
  border-radius: 18rpx;
  border: 0;
  background: #1a57db;
  color: #ffffff;
  font-size: 28rpx;
  line-height: 84rpx;
  font-weight: 700;
  box-shadow: 0 10rpx 24rpx rgba(26, 87, 219, 0.2);
}

.action-btn::after {
  border: 0;
}

.action-btn-active {
  opacity: 0.88;
}

@media (prefers-color-scheme: dark) {
  .icon-head,
  .icon-body,
  .icon-plus-h,
  .icon-plus-v {
    border-color: #60a5fa;
  }

  .empty-title {
    color: #e5e7eb;
  }

  .empty-desc {
    color: #9ca3af;
  }

  .action-btn {
    background: #2563eb;
    box-shadow: 0 10rpx 24rpx rgba(37, 99, 235, 0.3);
  }
}
</style>
