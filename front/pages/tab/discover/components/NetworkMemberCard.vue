<template>
  <view
    class="member-card"
    :class="{ 'member-card-faded': member.faded }"
    hover-class="member-card-active"
    @tap="$emit('view', member)"
  >
    <view class="card-header">
      <view class="avatar-wrap">
        <image
          class="avatar-image"
          :class="{ 'avatar-image-gray': member.verifyType === 'realname' }"
          mode="aspectFill"
          :src="member.avatar"
        />
      </view>

      <view class="header-info">
        <view class="name-row">
          <text class="name">{{ member.name }}</text>
          <image
            v-if="member.memberEnabled"
            class="member-badge"
            src="https://cos.cnptec.site/static/icon/mennber1.png"
            mode="aspectFit"
          />
          <text
            v-if="member.verifyType"
            class="verify-tag"
            :class="member.verifyType === 'realname' ? 'verify-tag-amber' : 'verify-tag-primary'"
          >
            已认证
          </text>
        </view>
        <text class="detail-text">{{ member.detailLine }}</text>
        <text v-if="member.postCount && member.postCount > 0" class="post-count-line">已发布 {{ member.postCount }}</text>
      </view>

      <button
        v-if="showFollow && !member.privacyHint"
        class="follow-btn-header"
        :class="{ 'follow-btn-followed': isFollowed(member) }"
        :disabled="followPending"
        hover-class="follow-btn-active"
        @tap.stop="$emit('follow', member)"
      >
        <text class="follow-icon">{{ isFollowed(member) ? '♥' : '♡' }}</text>
      </button>
    </view>

    <view class="card-body">
      <view class="tag-row">
        <text
          v-if="!member.circleTags || member.circleTags.length === 0"
          class="tag-chip tag-chip-placeholder"
        >
          该用户很低调，暂未进行个人介绍
        </text>
        <text
          v-else
          v-for="tag in member.circleTags"
          :key="`${member.id}-${tag}`"
          class="tag-chip"
        >
          {{ tag }}
        </text>
      </view>
    </view>

    <view v-if="member.privacyHint" class="privacy-footer">
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
  </view>
</template>

<script setup>
const isFollowed = (item = {}) => {
  return Boolean(
    item.followed
    || item.isFollowed
    || item.is_followed
  )
}

defineProps({
  member: {
    type: Object,
    default: () => ({})
  },
  showFollow: {
    type: Boolean,
    default: true
  },
  followPending: {
    type: Boolean,
    default: false
  }
})

defineEmits(['view', 'verify', 'follow'])
</script>

<style scoped>
.member-card {
  border-radius: 20rpx;
  background: #fefdfb;
  border: 1rpx solid rgba(148, 163, 184, 0.08);
  box-shadow: 0 1rpx 3rpx rgba(100, 116, 139, 0.04), 0 4rpx 16rpx rgba(148, 163, 184, 0.06);
  padding: 28rpx;
  transition: all 0.2s ease;
  margin-top: 10rpx;
}

.member-card-active {
  background: #faf9f7;
  box-shadow: 0 1rpx 2rpx rgba(100, 116, 139, 0.06), 0 2rpx 8rpx rgba(148, 163, 184, 0.08);
}

.member-card-faded {
  opacity: 0.82;
}

.card-header {
  display: flex;
  align-items: flex-start;
  gap: 16rpx;
  position: relative;
}

.avatar-wrap {
  position: relative;
  width: 110rpx;
  height: 110rpx;
  flex-shrink: 0;
}

.avatar-image {
  width: 100%;
  height: 100%;
  border-radius: 999rpx;
  background: linear-gradient(135deg, #e2e8f0 0%, #cbd5e1 100%);
  box-shadow: 0 0 0 3rpx #fefdfb, 0 0 0 4rpx rgba(148, 163, 184, 0.12), 0 2rpx 8rpx rgba(100, 116, 139, 0.08);
}

.avatar-image-gray {
  filter: grayscale(1);
}

.verify-dot {
  position: absolute;
  right: -8rpx;
  bottom: -2rpx;
  min-width: 32rpx;
  height: 44rpx;
  padding: 0 6rpx;
  border-radius: 999rpx;
  box-shadow: 0 0 0 3rpx #fefdfb, 0 2rpx 6rpx rgba(15, 23, 42, 0.12);
  display: flex;
  align-items: center;
  justify-content: center;
}

.verify-dot-primary {
  background: linear-gradient(135deg, #2563eb 0%, #1a57db 100%);
}

.verify-dot-amber {
  background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
}

.verify-dot-text {
  color: #ffffff;
  font-size: 16rpx;
  line-height: 1;
  font-weight: 700;
}

.header-info {
  flex: 1;
  min-width: 0;
}

.name-row {
  display: flex;
  align-items: center;
  gap: 10rpx;
  margin-bottom: 6rpx;
}

.name {
  color: #1e293b;
  font-size: 34rpx;
  line-height: 40rpx;
  font-weight: 600;
  letter-spacing: -0.02em;
  max-width: 300rpx;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.member-badge {
  width: 32rpx;
  height: 32rpx;
  flex-shrink: 0;
  display: block;
}

.verify-tag {
  flex-shrink: 0;
  border-radius: 8rpx;
  padding: 3rpx 10rpx;
  font-size: 18rpx;
  line-height: 24rpx;
  font-weight: 600;
  letter-spacing: -0.01em;
}

.verify-tag-primary {
  color: #1e40af;
  background: rgba(37, 99, 235, 0.08);
}

.detail-text {
  display: block;
  color: #64748b;
  font-size: 26rpx;
  line-height: 34rpx;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
  margin-bottom: 8rpx;
}

.post-count-line {
  display: block;
  color: #94a3b8;
  font-size: 22rpx;
  line-height: 28rpx;
}

.follow-btn-header {
  position: absolute;
  top: 0;
  right: 0;
  flex-shrink: 0;
  width: 48rpx;
  height: 48rpx;
  border-radius: 12rpx;
  background: #f8fafc;
  border: 1rpx solid #e2e8f0;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.follow-btn-header::after {
  border: 0;
}

.follow-btn-header.follow-btn-followed {
  background: rgba(239, 68, 68, 0.06);
  border-color: rgba(239, 68, 68, 0.15);
}

.follow-btn-active {
  background: #f1f5f9;
}

.follow-icon {
  font-size: 24rpx;
  line-height: 1;
  color: #94a3b8;
}

.follow-btn-followed .follow-icon {
  color: #ef4444;
}

.card-body {
  margin-top: 10rpx;
}

.tag-row {
  display: flex;
  align-items: center;
  gap: 8rpx;
  flex-wrap: wrap;
}

.tag-chip {
  padding: 8rpx 14rpx;
  color: #475569;
  font-size: 26rpx;
  line-height: 34rpx;
}

.tag-chip-placeholder {
  color: #94a3b8;
}

.privacy-footer {
  margin-top: 20rpx;
  border-radius: 14rpx;
  background: rgba(248, 250, 252, 0.8);
  border: 1rpx solid rgba(203, 213, 225, 0.4);
  padding: 16rpx 18rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10rpx;
}

.privacy-left {
  display: flex;
  align-items: center;
  gap: 10rpx;
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
  font-size: 22rpx;
  line-height: 28rpx;
  font-weight: 500;
}

.verify-btn {
  height: 48rpx;
  padding: 0 20rpx;
  border: 0;
  border-radius: 12rpx;
  background: transparent;
  color: #1a57db;
  font-size: 22rpx;
  line-height: 48rpx;
  font-weight: 600;
}

.verify-btn::after {
  border: 0;
}

.verify-btn-active {
  opacity: 0.72;
}

@media (prefers-color-scheme: dark) {
  .member-card {
    background: #0f172a;
    border-color: rgba(71, 85, 105, 0.2);
    box-shadow: 0 1rpx 3rpx rgba(0, 0, 0, 0.2), 0 4rpx 16rpx rgba(0, 0, 0, 0.15);
  }

  .member-card-active {
    background: #1a1f2e;
    box-shadow: 0 1rpx 2rpx rgba(0, 0, 0, 0.3), 0 2rpx 8rpx rgba(0, 0, 0, 0.2);
  }

  .avatar-image {
    background: linear-gradient(135deg, #334155 0%, #1e293b 100%);
    box-shadow: 0 0 0 3rpx #0f172a, 0 0 0 4rpx rgba(71, 85, 105, 0.3), 0 2rpx 8rpx rgba(0, 0, 0, 0.3);
  }

  .verify-dot {
    box-shadow: 0 0 0 3rpx #0f172a, 0 2rpx 6rpx rgba(0, 0, 0, 0.4);
  }

  .name {
    color: #f1f5f9;
  }

  .verify-tag-primary {
    color: #93c5fd;
    background: rgba(59, 130, 246, 0.12);
  }

  .verify-tag-amber {
    color: #fcd34d;
    background: rgba(251, 191, 36, 0.15);
  }

  .post-count-line {
    color: #64748b;
  }

  .detail-text {
    color: #94a3b8;
  }

  .follow-btn-header {
    background: #1e293b;
    border-color: #334155;
  }

  .follow-btn-active {
    background: #334155;
  }

  .follow-btn-header.follow-btn-followed {
    background: rgba(239, 68, 68, 0.1);
    border-color: rgba(239, 68, 68, 0.2);
  }

  .tag-chip {
    color: #94a3b8;
  }

  .privacy-footer {
    background: rgba(30, 41, 59, 0.4);
    border-color: rgba(71, 85, 105, 0.3);
  }

  .privacy-text {
    color: #94a3b8;
  }

  .lock-head,
  .lock-body {
    border-color: #64748b;
  }

  .verify-btn {
    color: #60a5fa;
  }
}
</style>
