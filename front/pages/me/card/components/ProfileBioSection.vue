<template>
  <view class="bio-wrap">
    <view class="bio-card">
      <text class="bio-text">
        <text class="bio-title">个人简介：</text>{{ bio }}
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
  padding: 0 32rpx 24rpx;
}

.bio-card {
  background: #f6f6f8;
  border-radius: 20rpx;
  padding: 24rpx;
}

.bio-text {
  color: #475569;
  font-size: 24rpx;
  line-height: 38rpx;
}

.bio-title {
  color: #0f172a;
  font-weight: 700;
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

  .bio-title {
    color: #f8fafc;
  }
}
</style>
