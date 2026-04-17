<template>
  <view class="contact-wrap">
    <view class="contact-card">
      <view class="contact-head">
        <text class="contact-title">联系方式</text>
        <text v-if="hasVisibleContact" class="contact-badge">可联系</text>
      </view>

      <template v-if="hasVisibleContact">
        <view v-if="contact.displayPhone" class="contact-row" @tap="copyValue(contact.displayPhone, '展示手机号已复制')">
          <view class="contact-main">
            <image class="contact-icon" mode="aspectFit" src="/static/me-icons/contact-page-primary.png" />
            <view class="contact-meta">
              <text class="contact-label">展示手机号</text>
              <text class="contact-value">{{ contact.displayPhone }}</text>
            </view>
          </view>
          <text class="contact-action">复制</text>
        </view>

        <view v-if="contact.displayWechat" class="contact-row" @tap="copyValue(contact.displayWechat, '展示微信号已复制')">
          <view class="contact-main">
            <image class="contact-icon" mode="aspectFit" src="/static/me-icons/contact-purple.png" />
            <view class="contact-meta">
              <text class="contact-label">展示微信号</text>
              <text class="contact-value">{{ contact.displayWechat }}</text>
            </view>
          </view>
          <text class="contact-action">复制</text>
        </view>
      </template>

      <view v-else class="contact-locked">
        <text class="contact-locked-title">{{ lockedTitle }}</text>
        <text class="contact-locked-desc">{{ lockedDesc }}</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  contact: {
    type: Object,
    default: () => ({})
  }
})

const hasVisibleContact = computed(() => {
  return Boolean(
    props.contact?.contactVisible && (props.contact?.displayPhone || props.contact?.displayWechat)
  )
})

const lockedTitle = computed(() => {
  return String(props.contact?.contactLockedReason || '').trim() || '暂时无法查看联系方式'
})

const lockedDesc = computed(() => {
  if (props.contact?.isSelf) {
    return '填写展示手机号和展示微信号后，别人才能在你的名片页看到这些联系方式。'
  }
  if (!props.contact?.targetContactEnabled || !props.contact?.targetHasContact) {
    return '对方公开并完善展示联系方式后，你才能在这里看到。'
  }
  return '先完善自己的展示手机号和微信号，并完成实名认证、开通会员后，再查看他人的联系方式。'
})

const copyValue = (value, successTitle) => {
  const normalized = String(value || '').trim()
  if (!normalized) {
    return
  }
  uni.setClipboardData({
    data: normalized,
    success: () => {
      uni.showToast({
        title: successTitle,
        icon: 'none'
      })
    }
  })
}
</script>

<style scoped>
.contact-wrap {
  background: #ffffff;
  padding: 0 32rpx 24rpx;
}

.contact-card {
  border-radius: 24rpx;
  background: #f8fafc;
  padding: 24rpx;
  display: flex;
  flex-direction: column;
  gap: 18rpx;
}

.contact-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
}

.contact-title {
  color: #0f172a;
  font-size: 28rpx;
  line-height: 36rpx;
  font-weight: 700;
}

.contact-badge {
  border-radius: 999rpx;
  background: rgba(16, 185, 129, 0.12);
  color: #059669;
  padding: 4rpx 16rpx;
  font-size: 20rpx;
  line-height: 28rpx;
  font-weight: 700;
}

.contact-row {
  border-radius: 20rpx;
  background: #ffffff;
  padding: 22rpx 24rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
}

.contact-main {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 18rpx;
}

.contact-icon {
  width: 40rpx;
  height: 40rpx;
  flex-shrink: 0;
}

.contact-meta {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.contact-label {
  color: #64748b;
  font-size: 22rpx;
  line-height: 30rpx;
}

.contact-value {
  color: #0f172a;
  font-size: 28rpx;
  line-height: 38rpx;
  font-weight: 700;
  word-break: break-all;
}

.contact-action {
  color: #1a57db;
  font-size: 24rpx;
  line-height: 32rpx;
  font-weight: 700;
  flex-shrink: 0;
}

.contact-locked {
  border-radius: 20rpx;
  background: #ffffff;
  padding: 24rpx;
  display: flex;
  flex-direction: column;
  gap: 10rpx;
}

.contact-locked-title {
  color: #0f172a;
  font-size: 26rpx;
  line-height: 36rpx;
  font-weight: 700;
}

.contact-locked-desc {
  color: #64748b;
  font-size: 22rpx;
  line-height: 34rpx;
}

@media (prefers-color-scheme: dark) {
  .contact-wrap {
    background: rgba(15, 23, 42, 0.82);
  }

  .contact-card,
  .contact-row,
  .contact-locked {
    background: rgba(30, 41, 59, 0.55);
  }

  .contact-title,
  .contact-value,
  .contact-locked-title {
    color: #f8fafc;
  }

  .contact-label,
  .contact-locked-desc {
    color: #cbd5e1;
  }
}
</style>
