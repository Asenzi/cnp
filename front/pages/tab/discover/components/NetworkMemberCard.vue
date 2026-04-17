<template>
  <view
    class="member-card"
    :class="{ 'member-card-faded': member.faded }"
    hover-class="member-card-active"
    @tap="$emit('view', member)"
  >
    <view class="top-row">
      <view class="avatar-wrap">
        <image
          class="avatar-image"
          :class="{ 'avatar-image-gray': member.verifyType === 'realname' }"
          mode="aspectFill"
          :src="member.avatar"
        />
        <view
          v-if="member.verifyType"
          class="verify-dot"
          :class="member.verifyType === 'realname' ? 'verify-dot-amber' : 'verify-dot-primary'"
        >
          <text class="verify-dot-text">✓</text>
        </view>
      </view>

      <view class="profile-wrap">
        <view class="name-row">
          <text class="name">{{ member.name }}</text>
          <text
            v-if="member.verifyType"
            class="verify-tag"
            :class="member.verifyType === 'realname' ? 'verify-tag-amber' : 'verify-tag-primary'"
          >
            {{ member.verifyText }}
          </text>
        </view>

        <text class="detail-text">{{ member.detailLine }}</text>

        <view class="tag-row">
          <text v-for="tag in member.circleTags" :key="`${member.id}-${tag}`" class="tag-chip">{{ tag }}</text>
        </view>
      </view>
    </view>

    <view v-if="member.privacyHint" class="privacy-row">
      <view class="privacy-left">
        <view class="privacy-lock-icon">
          <view class="lock-head"></view>
          <view class="lock-body"></view>
        </view>
        <text class="privacy-text">{{ member.privacyHint }}</text>
      </view>
      <button class="verify-btn" hover-class="verify-btn-active" @tap.stop="$emit('verify', member)">
        去认证
      </button>
    </view>

    <view v-else class="action-row">
      <text class="active-text">{{ member.activeText || '最近活跃' }}</text>
      <button
        v-if="showInterest"
        class="interest-btn"
        :class="{ 'interest-btn-liked': isInterested(member) }"
        hover-class="interest-btn-active"
        @tap.stop="$emit('interest', member)"
      >
        <image class="interest-icon" :src="getInterestIcon(member)" mode="aspectFit" />
      </button>
    </view>
  </view>
</template>

<script setup>
const getInterestIcon = (item = {}) => {
  return isInterested(item) ? '/static/icon/like.png' : '/static/icon/ulike.png'
}

const isInterested = (item = {}) => {
  return Boolean(
    item.interested
    || item.isInterested
    || item.is_interested
    || item.followed
    || item.isFollowed
    || item.is_followed
  )
}

defineProps({
  member: {
    type: Object,
    default: () => ({})
  },
  showInterest: {
    type: Boolean,
    default: true
  }
})

defineEmits(['view', 'verify', 'interest'])
</script>

<style scoped>
.member-card {
  border-radius: 16rpx;
  background: #ffffff;
  border: 1rpx solid #f1f5f9;
  box-shadow: 0 2rpx 10rpx rgba(15, 23, 42, 0.04);
  padding: 24rpx;
}

.member-card-active {
  background: #f8fafc;
}

.member-card-faded {
  opacity: 0.82;
}

.top-row {
  display: flex;
  align-items: flex-start;
  gap: 16rpx;
}

.avatar-wrap {
  position: relative;
  width: 128rpx;
  height: 128rpx;
  flex-shrink: 0;
}

.avatar-image {
  width: 100%;
  height: 100%;
  border-radius: 999rpx;
  border: 4rpx solid #ffffff;
  background: #e2e8f0;
  box-shadow: 0 2rpx 8rpx rgba(15, 23, 42, 0.08);
}

.avatar-image-gray {
  filter: grayscale(1);
}

.verify-dot {
  position: absolute;
  right: -4rpx;
  bottom: -4rpx;
  min-width: 28rpx;
  height: 28rpx;
  padding: 0 6rpx;
  border-radius: 999rpx;
  border: 3rpx solid #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
}

.verify-dot-primary {
  background: #1a57db;
}

.verify-dot-amber {
  background: #f59e0b;
}

.verify-dot-text {
  color: #ffffff;
  font-size: 16rpx;
  line-height: 1;
  font-weight: 700;
}

.profile-wrap {
  flex: 1;
  min-width: 0;
}

.name-row {
  display: flex;
  align-items: center;
  gap: 8rpx;
}

.name {
  color: #0f172a;
  font-size: 30rpx;
  line-height: 38rpx;
  font-weight: 700;
  max-width: 240rpx;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.verify-tag {
  flex-shrink: 0;
  border-radius: 6rpx;
  padding: 2rpx 8rpx;
  font-size: 16rpx;
  line-height: 22rpx;
  font-weight: 700;
}

.verify-tag-primary {
  color: #1a57db;
  background: rgba(26, 87, 219, 0.1);
}

.verify-tag-amber {
  color: #d97706;
  background: rgba(245, 158, 11, 0.12);
}

.detail-text {
  display: block;
  margin-top: 4rpx;
  color: #64748b;
  font-size: 24rpx;
  line-height: 32rpx;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.tag-row {
  margin-top: 8rpx;
  display: flex;
  align-items: center;
  gap: 6rpx;
  flex-wrap: wrap;
}

.tag-chip {
  border-radius: 6rpx;
  padding: 4rpx 10rpx;
  background: #f1f5f9;
  color: #64748b;
  font-size: 18rpx;
  line-height: 24rpx;
}

.privacy-row {
  margin-top: 16rpx;
  border-radius: 12rpx;
  background: #f8fafc;
  padding: 14rpx 16rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10rpx;
}

.privacy-left {
  display: flex;
  align-items: center;
  gap: 8rpx;
}

.privacy-lock-icon {
  position: relative;
  width: 24rpx;
  height: 24rpx;
  flex-shrink: 0;
}

.lock-head {
  position: absolute;
  left: 6rpx;
  top: 1rpx;
  width: 12rpx;
  height: 10rpx;
  border: 2rpx solid #94a3b8;
  border-bottom: 0;
  border-radius: 10rpx 10rpx 0 0;
}

.lock-body {
  position: absolute;
  left: 4rpx;
  bottom: 2rpx;
  width: 16rpx;
  height: 12rpx;
  border-radius: 4rpx;
  border: 2rpx solid #94a3b8;
}

.privacy-text {
  color: #64748b;
  font-size: 20rpx;
  line-height: 28rpx;
}

.verify-btn {
  height: 44rpx;
  padding: 0 18rpx;
  border: 0;
  border-radius: 10rpx;
  background: transparent;
  color: #1a57db;
  font-size: 20rpx;
  line-height: 44rpx;
  font-weight: 700;
}

.verify-btn::after {
  border: 0;
}

.verify-btn-active {
  opacity: 0.72;
}

.action-row {
  margin-top: 16rpx;
  padding-top: 16rpx;
  border-top: 1rpx solid #f8fafc;
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 10rpx;
}

.active-text {
  color: #94a3b8;
  font-size: 20rpx;
  line-height: 28rpx;
  min-width: 0;
  flex: 1;
}

.interest-btn {
  width: 66rpx;
  height: 48rpx;
  border: 0;
  flex-shrink: 0;
  margin-left: auto;
  padding: 0;
  border-radius: 0;
  background: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
}

.interest-btn::after {
  border: 0;
}

.interest-btn-active {
  opacity: 0.8;
}

.interest-icon {
  width: 32rpx;
  height: 32rpx;
}

@media (prefers-color-scheme: dark) {
  .member-card {
    background: #0f172a;
    border-color: #1e293b;
    box-shadow: none;
  }

  .member-card-active {
    background: #162033;
  }

  .avatar-image {
    border-color: #1e293b;
    background: #334155;
  }

  .verify-dot {
    border-color: #1e293b;
  }

  .name {
    color: #f8fafc;
  }

  .detail-text {
    color: #94a3b8;
  }

  .tag-chip {
    background: #1e293b;
    color: #94a3b8;
  }

  .privacy-row {
    background: rgba(30, 41, 59, 0.5);
  }

  .privacy-text {
    color: #94a3b8;
  }

  .lock-head,
  .lock-body {
    border-color: #64748b;
  }

  .action-row {
    border-top-color: #1e293b;
  }

  .interest-btn {
    background: transparent;
  }
}
</style>
