<template>
  <view class="circle-card">
    <view class="card-top">
      <view class="card-main">
        <view class="title-row">
          <text class="circle-title">{{ circle.title }}</text>
          <text v-if="circle.officialTag" class="official-tag">{{ circle.officialTag }}</text>
        </view>
        <text class="circle-desc">{{ circle.description }}</text>

        <view class="metric-row">
          <text class="metric-text">{{ circle.memberCountText }}</text>
          <text class="metric-text">{{ circle.postCountText }}</text>
        </view>
      </view>

      <image class="cover-image" mode="aspectFill" :src="circle.coverImage" />
    </view>

    <view class="card-bottom">
      <view class="bottom-left">
        <view v-if="circle.recentVisitors && circle.recentVisitors.length" class="avatar-stack">
          <image
            v-for="(avatar, idx) in circle.recentVisitors"
            :key="`${circle.id}-avatar-${idx}`"
            class="avatar"
            mode="aspectFill"
            :src="avatar"
          />
        </view>
        <text v-else class="active-text">{{ circle.lastActiveText }}</text>
      </view>

      <button
        class="enter-btn"
        hover-class="enter-btn-active"
        @tap="onEnter"
      >
        <text class="enter-btn-text">进入圈子</text>
        <image class="enter-chevron" mode="aspectFit" src="/static/me-icons/chevron-light.png" />
      </button>
    </view>
  </view>
</template>

<script setup>
const props = defineProps({
  circle: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['enter'])

const onEnter = () => {
  emit('enter', props.circle)
}
</script>

<style scoped>
.circle-card {
  border-radius: 20rpx;
  padding: 24rpx;
  background: #ffffff;
  border: 1rpx solid #f1f5f9;
  box-shadow: 0 2rpx 10rpx rgba(15, 23, 42, 0.06);
  box-sizing: border-box;
}

.card-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20rpx;
}

.card-main {
  flex: 1;
  min-width: 0;
}

.title-row {
  display: flex;
  align-items: center;
  gap: 10rpx;
}

.circle-title {
  color: #0f172a;
  font-size: 32rpx;
  line-height: 40rpx;
  font-weight: 700;
  max-width: 360rpx;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.official-tag {
  background: rgba(26, 87, 219, 0.1);
  color: #1a57db;
  font-size: 18rpx;
  line-height: 24rpx;
  font-weight: 700;
  border-radius: 6rpx;
  padding: 2rpx 8rpx;
  flex-shrink: 0;
}

.circle-desc {
  display: block;
  margin-top: 8rpx;
  color: #64748b;
  font-size: 22rpx;
  line-height: 30rpx;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.metric-row {
  margin-top: 10rpx;
  display: flex;
  align-items: center;
  gap: 20rpx;
}

.metric-text {
  color: #94a3b8;
  font-size: 20rpx;
  line-height: 28rpx;
}

.cover-image {
  width: 128rpx;
  height: 128rpx;
  border-radius: 12rpx;
  border: 1rpx solid #f1f5f9;
  flex-shrink: 0;
  background: #e2e8f0;
}

.card-bottom {
  margin-top: 16rpx;
  padding-top: 14rpx;
  border-top: 1rpx solid #f8fafc;
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.bottom-left {
  flex: 1;
  min-width: 0;
}

.avatar-stack {
  display: flex;
  align-items: center;
}

.avatar {
  width: 44rpx;
  height: 44rpx;
  border-radius: 999rpx;
  border: 2rpx solid #ffffff;
  margin-left: -10rpx;
  background: #e2e8f0;
}

.avatar:first-child {
  margin-left: 0;
}

.active-text {
  color: #94a3b8;
  font-size: 20rpx;
  line-height: 28rpx;
}

.enter-btn {
  height: 56rpx;
  border-radius: 999rpx;
  padding: 0 24rpx;
  border: 0;
  margin-left: auto;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6rpx;
  flex-shrink: 0;
  background: #1a57db;
  box-shadow: 0 6rpx 14rpx rgba(26, 87, 219, 0.2);
}

.enter-btn-text {
  font-size: 22rpx;
  line-height: 30rpx;
  font-weight: 700;
  color: #ffffff;
}

.enter-chevron {
  width: 20rpx;
  height: 20rpx;
  opacity: 0.95;
  filter: brightness(2.4);
}

.enter-btn-active {
  opacity: 0.88;
}

@media (prefers-color-scheme: dark) {
  .circle-card {
    background: #0f172a;
    border-color: #1e293b;
    box-shadow: none;
  }

  .circle-title {
    color: #f8fafc;
  }

  .circle-desc {
    color: #94a3b8;
  }

  .metric-text,
  .active-text {
    color: #64748b;
  }

  .cover-image {
    border-color: #334155;
    background: #1e293b;
  }

  .card-bottom {
    border-top-color: #1e293b;
  }

  .avatar {
    border-color: #0f172a;
  }

}
</style>
