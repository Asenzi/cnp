<template>
  <view>
    <view class="guest-profile-row" @tap="$emit('login')">
      <view class="guest-avatar-wrap">
        <view class="guest-avatar">
          <view class="guest-avatar-icon">
            <view class="guest-avatar-head"></view>
            <view class="guest-avatar-body"></view>
          </view>
        </view>
      </view>

      <view class="guest-profile-info">
        <view class="guest-name-row">
          <text class="guest-name">登录/注册</text>
        </view>
        <view class="guest-tip-row">
          <text class="guest-tip-tag">请先登录</text>
        </view>
        <text class="guest-summary">登录后即可开启您的商务社交之旅</text>
      </view>
    </view>

    <view class="guest-intro-card">
      <view class="guest-intro-title-row">
        <image class="intro-mark-img" mode="aspectFit" src="/static/me-icons/description-primary.png" />
        <text class="guest-intro-title">个人简介</text>
      </view>
      <text class="guest-intro-text">您还没有登录，暂无个人简介信息</text>
    </view>

    <view class="guest-stats-row">
      <view class="guest-stat-card guest-stat-card-click" hover-class="guest-stat-card-active" @tap="$emit('open-circles')">
        <text class="guest-stat-value">--</text>
        <text class="guest-stat-label">我的圈子</text>
      </view>
      <!-- 积分功能暂时隐藏
      <view class="guest-stat-card guest-stat-card-click" hover-class="guest-stat-card-active" @tap="$emit('open-points')">
        <text class="guest-stat-value">--</text>
        <text class="guest-stat-label">积分</text>
      </view>
      -->
      <view class="guest-stat-card">
        <text class="guest-stat-value">--</text>
        <text class="guest-stat-label">账户余额</text>
      </view>
    </view>
  </view>
</template>

<script setup>
defineEmits(['login', 'open-circles'])
</script>

<style scoped>
.guest-profile-row {
  display: flex;
  align-items: flex-start;
  gap: 32rpx;
  margin-bottom: 32rpx;
}

.guest-avatar-wrap {
  position: relative;
}

.guest-avatar {
  width: 192rpx;
  height: 192rpx;
  border-radius: 24rpx;
  border: 4rpx solid #ffffff;
  background: #e2e8f0;
  box-shadow: 0 4rpx 12rpx rgba(15, 23, 42, 0.06);
  display: flex;
  align-items: center;
  justify-content: center;
}

.guest-avatar-icon {
  position: relative;
  width: 96rpx;
  height: 96rpx;
  border-radius: 999rpx;
  background: #cbd5e1;
}

.guest-avatar-head {
  position: absolute;
  left: 50%;
  top: 16rpx;
  transform: translateX(-50%);
  width: 28rpx;
  height: 28rpx;
  border-radius: 999rpx;
  background: #94a3b8;
}

.guest-avatar-body {
  position: absolute;
  left: 50%;
  bottom: 14rpx;
  transform: translateX(-50%);
  width: 52rpx;
  height: 30rpx;
  border-radius: 30rpx 30rpx 10rpx 10rpx;
  background: #94a3b8;
}

.guest-profile-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.guest-name-row {
  display: flex;
  align-items: center;
}

.guest-name {
  color: #0f172a;
  font-size: 40rpx;
  line-height: 48rpx;
  font-weight: 700;
}

.guest-tip-row {
  margin-top: 2rpx;
}

.guest-tip-tag {
  display: inline-block;
  border-radius: 999rpx;
  border: 1rpx solid #e2e8f0;
  background: #f8fafc;
  color: #64748b;
  font-size: 20rpx;
  line-height: 28rpx;
  font-weight: 700;
  padding: 4rpx 12rpx;
}

.guest-summary {
  margin-top: 4rpx;
  color: #64748b;
  font-size: 28rpx;
  line-height: 36rpx;
}

.guest-intro-card {
  margin-bottom: 48rpx;
  padding: 32rpx;
  border: 1rpx solid rgba(26, 87, 219, 0.1);
  border-radius: 24rpx;
  background: rgba(26, 87, 219, 0.05);
}

.guest-intro-title-row {
  display: flex;
  align-items: center;
  gap: 12rpx;
  margin-bottom: 8rpx;
}

.intro-mark-img {
  width: 36rpx;
  height: 36rpx;
}

.guest-intro-title {
  font-size: 28rpx;
  color: #334155;
  font-weight: 600;
}

.guest-intro-text {
  font-size: 28rpx;
  color: #94a3b8;
  line-height: 1.65;
  font-style: italic;
}

.guest-stats-row {
  display: flex;
  gap: 24rpx;
  margin-bottom: 64rpx;
}

.guest-stat-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8rpx;
  padding: 24rpx 12rpx;
  border-radius: 24rpx;
  border: 1rpx solid #f1f5f9;
  background: #ffffff;
  box-shadow: 0 4rpx 12rpx rgba(15, 23, 42, 0.04);
}

.guest-stat-card-click {
  transition: opacity 0.2s ease;
}

.guest-stat-card-active {
  opacity: 0.82;
}

.guest-stat-value {
  font-size: 40rpx;
  font-weight: 700;
  color: #94a3b8;
  line-height: 1.2;
}

.guest-stat-label {
  font-size: 22rpx;
  color: #64748b;
  font-weight: 500;
}

@media (prefers-color-scheme: dark) {
  .guest-name {
    color: #f1f5f9;
  }

  .guest-summary,
  .guest-stat-label {
    color: #94a3b8;
  }

  .guest-avatar {
    border-color: #1e293b;
    background: #334155;
  }

  .guest-avatar-icon {
    background: #64748b;
  }

  .guest-avatar-head,
  .guest-avatar-body {
    background: #cbd5e1;
  }

  .guest-tip-tag {
    border-color: #334155;
    background: #1e293b;
    color: #94a3b8;
  }

  .guest-intro-card {
    background: rgba(26, 87, 219, 0.1);
    border-color: rgba(26, 87, 219, 0.2);
  }

  .guest-intro-title {
    color: #cbd5e1;
  }

  .guest-intro-text {
    color: #94a3b8;
  }

  .guest-stat-card {
    border-color: #334155;
    background: #1e293b;
    box-shadow: none;
  }

  .guest-stat-value {
    color: #94a3b8;
  }
}
</style>
