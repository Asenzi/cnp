<template>
  <view>
    <image class="banner-image" mode="aspectFill" :src="detail.bannerImage" />

    <view class="info-wrap">
      <view class="top-row">
        <image class="logo-image" mode="aspectFill" :src="detail.logoImage" />
        <view class="title-wrap">
          <text class="title">{{ detail.title }}</text>
          <view class="meta-row">
            <text class="level-tag">{{ detail.levelTag }}</text>
            <text class="meta-text">{{ detail.membersText }} · {{ detail.postsText }}</text>
          </view>
        </view>
      </view>
      <text class="description">{{ detail.description }}</text>
    </view>
  </view>
</template>

<script setup>
defineProps({
  detail: {
    type: Object,
    default: () => ({})
  }
})
</script>

<style scoped>
.banner-image {
  width: 100%;
  height: 320rpx;
  background: #cbd5e1;
}

.info-wrap {
  background: #ffffff;
  padding: 28rpx 32rpx 20rpx;
}

.top-row {
  display: flex;
  align-items: flex-start;
  gap: 18rpx;
}

.logo-image {
  width: 160rpx;
  height: 160rpx;
  border-radius: 20rpx;
  border: 4rpx solid #ffffff;
  box-shadow: 0 8rpx 18rpx rgba(15, 23, 42, 0.15);
  background: #e2e8f0;
}

.title-wrap {
  flex: 1;
  min-width: 0;
}

.title {
  display: block;
  color: #0f172a;
  font-size: 40rpx;
  line-height: 48rpx;
  font-weight: 700;
}

.meta-row {
  margin-top: 8rpx;
  display: flex;
  align-items: center;
  gap: 10rpx;
  flex-wrap: wrap;
}

.level-tag {
  color: #1a57db;
  background: rgba(26, 87, 219, 0.1);
  border-radius: 999rpx;
  font-size: 20rpx;
  line-height: 28rpx;
  font-weight: 600;
  padding: 4rpx 14rpx;
}

.meta-text {
  color: #64748b;
  font-size: 22rpx;
  line-height: 30rpx;
}

.description {
  display: block;
  margin-top: 18rpx;
  color: #475569;
  font-size: 24rpx;
  line-height: 36rpx;
}

@media (prefers-color-scheme: dark) {
  .info-wrap {
    background: #0f172a;
  }

  .logo-image {
    border-color: #1e293b;
    background: #334155;
  }

  .title {
    color: #f8fafc;
  }

  .meta-text,
  .description {
    color: #94a3b8;
  }
}
</style>
