<template>
  <view class="bio-wrap">
    <view class="bio-card">
      <text class="bio-text">
        {{ bio }}
      </text>
    </view>
  </view>
</template>

<script setup>
defineProps({
  bio: {
    type: String,
    default: ''
  }
})
</script>

<style scoped>
.bio-wrap {
  background: #ffffff;
  padding: 0 32rpx 32rpx;
}

.bio-card {
  background: #f9fafb;
  border-radius: 16rpx;
  padding: 24rpx;
  /* border: 1rpx solid rgba(0, 0, 0, 0.04); */
}

.bio-text {
  color: #6b7280;
  font-size: 26rpx;
  line-height: 40rpx;
}

@media (prefers-color-scheme: dark) {
  .bio-wrap {
    background: rgba(15, 23, 42, 0.82);
  }

  .bio-card {
    background: rgba(30, 41, 59, 0.45);
  }

  .bio-text {
    color: #cbd5e1;
  }

}
</style>
