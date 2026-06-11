<template>
  <view class="hero-wrap">
    <view class="hero-row">
      <image class="avatar" :src="profile.avatarUrl" mode="aspectFill" />

      <view class="meta-wrap">
        <view class="name-row">
          <text class="name">{{ profile.name }}</text>
          <image
            v-if="profile.memberEnabled && !memberIconLoadFailed"
            class="member-badge"
            mode="aspectFit"
            :src="memberIconUrl"
            @error="onMemberIconError"
          />
          <view v-else-if="profile.memberEnabled" class="member-badge member-badge-fallback">
            <ProfileSymbol name="member_badge" :size="16" color="#f59e0b" />
          </view>
        </view>

        <text class="meta-line">{{ profile.metaLine }}</text>

        <view class="verify-row">
          <text class="verify-text" :class="profile.isVerified ? 'verify-text-active' : 'verify-text-idle'">
            {{ profile.verifiedText }}
          </text>
        </view>
      </view>

      <button
        v-if="showAction"
        class="message-btn"
        hover-class="message-btn-hover"
        :open-type="actionType === 'share' ? 'share' : ''"
        @tap.stop="onTapAction"
      >
        <image
          class="message-icon"
          :src="actionType === 'share' ? 'https://cos.cnptec.site/static/icon/share.png' : 'https://cos.cnptec.site/static/icon/chat.png'"
          mode="aspectFit"
        />
      </button>
    </view>
  </view>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import ProfileSymbol from './ProfileSymbol.vue'

const props = defineProps({
  profile: {
    type: Object,
    default: () => ({})
  },
  showAction: {
    type: Boolean,
    default: false
  },
  actionType: {
    type: String,
    default: 'message'
  }
})

const LOCAL_MEMBER_ICON_URL = 'https://cos.cnptec.site/static/icon/mennber1.png'

const memberIconLoadFailed = ref(false)
const memberIconUrl = ref(LOCAL_MEMBER_ICON_URL)

const remoteMemberIconUrl = computed(() => {
  return LOCAL_MEMBER_ICON_URL
})

const onMemberIconError = () => {
  if (memberIconUrl.value !== LOCAL_MEMBER_ICON_URL) {
    memberIconUrl.value = LOCAL_MEMBER_ICON_URL
    return
  }
  memberIconLoadFailed.value = true
}

const emit = defineEmits(['message'])

const onTapAction = () => {
  if (props.actionType === 'share') {
    return
  }
  emit('message')
}

watch(
  () => props.profile?.memberEnabled,
  () => {
    memberIconLoadFailed.value = false
    memberIconUrl.value = remoteMemberIconUrl.value || LOCAL_MEMBER_ICON_URL
  },
  { immediate: true }
)

</script>

<style scoped>
.hero-wrap {
  background: #ffffff;
  padding: 40rpx 32rpx;
}

.hero-row {
  display: flex;
  align-items: center;
  gap: 24rpx;
}

.avatar {
  width: 128rpx;
  height: 128rpx;
  border-radius: 64rpx;
  border: 2rpx solid rgba(26, 87, 219, 0.1);
  background: #f3f4f6;
  flex-shrink: 0;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.04);
}

.meta-wrap {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 8rpx;
}

.name-row {
  display: flex;
  align-items: center;
  gap: 8rpx;
  min-width: 0;
}

.name {
  max-width: 100%;
  color: #111827;
  font-size: 36rpx;
  line-height: 48rpx;
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.member-badge {
  width: 32rpx;
  height: 32rpx;
  flex-shrink: 0;
}

.member-badge-fallback {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999rpx;
  background: rgba(245, 158, 11, 0.1);
}

.meta-line {
  color: #6b7280;
  font-size: 26rpx;
  line-height: 36rpx;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.verify-row {
  display: flex;
  align-items: center;
  gap: 8rpx;
}

.verify-text {
  font-size: 24rpx;
  line-height: 32rpx;
  font-weight: 600;
}

.verify-text-active {
  color: #1a57db;
}

.verify-text-idle {
  color: #9ca3af;
}

.message-btn {
  width: 80rpx;
  height: 80rpx;
  padding: 0;
  border: 0;
  border-radius: 20rpx;
  background: rgba(26, 87, 219, 0.08);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.2s ease;
}

.message-icon {
  width: 36rpx;
  height: 36rpx;
  display: block;
}

.message-btn::after {
  border: 0;
}

.message-btn-hover {
  background: rgba(26, 87, 219, 0.12);
  transform: scale(0.96);
}

@media (prefers-color-scheme: dark) {
  .hero-wrap {
    background: rgba(15, 23, 42, 0.82);
  }

  .avatar {
    background: #334155;
    border-color: rgba(26, 87, 219, 0.32);
  }

  .name {
    color: #f8fafc;
  }

  .meta-line {
    color: #94a3b8;
  }

  .message-btn {
    background: rgba(59, 130, 246, 0.18);
  }
}
</style>
