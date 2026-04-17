<template>
  <view class="member-card-wrap">
    <view class="member-card">
      <view class="member-icon">
        <view class="member-icon-badge">
          <text class="member-star">★</text>
        </view>
      </view>

      <view class="member-main">
        <text class="member-title">会员中心</text>
        <text class="member-desc">开通会员享特权</text>
      </view>

      <button class="member-open-btn" hover-class="member-open-btn-active" @tap="$emit('open')">
        立即开通
      </button>
    </view>
  </view>
</template>

<script setup>
defineEmits(['open'])
</script>

<style scoped>
.member-card-wrap {
  margin-top: 0;
  margin-bottom: 46rpx;
  border-radius: 20rpx;
  background: #ffffff;
  border: 1rpx solid #f1f5f9;
  padding: 16rpx;
}

.member-card {
  border-radius: 20rpx;
  background: linear-gradient(135deg, #2f6cff 0%, #1a57db 100%);
  min-height: 132rpx;
  display: flex;
  align-items: center;
  gap: 18rpx;
  padding: 0 22rpx;
}

.member-icon {
  width: 76rpx;
  height: 76rpx;
  border-radius: 16rpx;
  background: rgba(255, 255, 255, 0.16);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.member-icon-badge {
  width: 40rpx;
  height: 40rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.92);
  display: flex;
  align-items: center;
  justify-content: center;
}

.member-star {
  color: #1a57db;
  font-size: 22rpx;
  line-height: 1;
  font-weight: 700;
}

.member-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4rpx;
}

.member-title {
  color: #ffffff;
  font-size: 34rpx;
  line-height: 42rpx;
  font-weight: 700;
}

.member-desc {
  color: rgba(255, 255, 255, 0.88);
  font-size: 24rpx;
  line-height: 32rpx;
}

.member-open-btn {
  margin: 0;
  padding: 0 24rpx;
  height: 56rpx;
  line-height: 56rpx;
  border-radius: 999rpx;
  border: 0;
  background: #ffffff;
  color: #1a57db;
  font-size: 22rpx;
  font-weight: 700;
  flex-shrink: 0;
}

.member-open-btn::after {
  border: 0;
}

.member-open-btn-active {
  opacity: 0.86;
}

@media (prefers-color-scheme: dark) {
  .member-card-wrap {
    background: #0f172a;
    border-color: #1e293b;
  }

  .member-card {
    background: linear-gradient(135deg, #1d4ed8 0%, #1e40af 100%);
  }

  .member-open-btn {
    background: #e2e8f0;
    color: #1e40af;
  }
}
</style>
