<template>
  <view class="member-card-wrap" @tap="$emit('open')">
    <view class="member-card">
      <view class="member-icon">
        <image class="member-badge-img" mode="aspectFit" src="https://cos.cnptec.site/static/icon/huiyuan.png" />
      </view>

      <view class="member-main">
        <text class="member-title">会员中心</text>
        <text class="member-desc">开通会员，解锁更多权益</text>
      </view>

      <view class="member-open-btn">
        <text class="member-open-text">立即开通</text>
      </view>
    </view>
  </view>
</template>

<script setup>
defineEmits(['open'])
</script>

<style scoped>
.member-card-wrap {
  margin-top: 0;
  margin-bottom: 32rpx;
  border-radius: 16rpx;
  background: #fff9f5;
  border: 1rpx solid #f4e3cf;
  padding: 12rpx 0;
}

.member-card {
  min-height: 112rpx;
  display: flex;
  align-items: center;
  gap: 16rpx;
  padding: 0 24rpx;
}

.member-icon {
  width: 64rpx;
  height: 64rpx;
  border-radius: 14rpx;
  background: linear-gradient(180deg, #f7d98a 0%, #ecbb5d 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: inset 0 1rpx 0 rgba(255, 255, 255, 0.45);
}

.member-badge-img {
  width: 34rpx;
  height: 34rpx;
}

.member-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4rpx;
}

.member-title {
  color: #9b6a15;
  font-size: 30rpx;
  line-height: 38rpx;
  font-weight: 700;
}

.member-desc {
  color: #c08b34;
  font-size: 22rpx;
  line-height: 28rpx;
}

.member-open-btn {
  min-width: 128rpx;
  height: 52rpx;
  padding: 0 20rpx;
  border-radius: 999rpx;
  background: #ffffff;
  border: 1rpx solid #f0d7b2;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.member-open-text {
  color: #b67b1f;
  font-size: 22rpx;
  font-weight: 700;
  line-height: 1;
}

@media (prefers-color-scheme: dark) {
  .member-card-wrap {
    background: rgba(120, 76, 17, 0.22);
    border-color: rgba(224, 177, 83, 0.24);
  }

  .member-title {
    color: #f2d28c;
  }

  .member-desc {
    color: #dfb665;
  }

  .member-open-btn {
    background: rgba(255, 255, 255, 0.08);
    border-color: rgba(224, 177, 83, 0.3);
  }

  .member-open-text {
    color: #f2d28c;
  }
}
</style>
