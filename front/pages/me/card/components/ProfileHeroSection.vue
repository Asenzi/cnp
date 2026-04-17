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
          :src="actionType === 'share' ? '/static/icon/share.png' : '/static/icon/chat.png'"
          mode="aspectFit"
        />
      </button>
    </view>
  </view>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { getApiBaseUrl } from '../../../../utils/request'
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

const LOCAL_MEMBER_ICON_URL = '/static/icon/mennber.png'

const memberIconLoadFailed = ref(false)
const memberIconUrl = ref(LOCAL_MEMBER_ICON_URL)

const remoteMemberIconUrl = computed(() => {
  const baseUrl = String(getApiBaseUrl() || '').replace(/\/$/, '')
  if (!baseUrl || !/^https:\/\//i.test(baseUrl)) {
    return ''
  }
  return `${baseUrl}/static/icon/mennber.png`
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
  padding: 32rpx;
}

.hero-row {
  display: flex;
  align-items: center;
  gap: 24rpx;
}

.avatar {
  width: 140rpx;
  height: 140rpx;
  border-radius: 999rpx;
  border: 3rpx solid rgba(26, 87, 219, 0.16);
  background: #e2e8f0;
  flex-shrink: 0;
}

.meta-wrap {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.name-row {
  display: flex;
  align-items: center;
  gap: 10rpx;
  min-width: 0;
}

.name {
  max-width: 100%;
  color: #0f172a;
  font-size: 38rpx;
  line-height: 52rpx;
  font-weight: 700;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.member-badge {
  width: 36rpx;
  height: 36rpx;
  flex-shrink: 0;
}

.member-badge-fallback {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999rpx;
  background: rgba(245, 158, 11, 0.14);
}

.meta-line {
  margin-top: 10rpx;
  color: #64748b;
  font-size: 24rpx;
  line-height: 34rpx;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.verify-row {
  margin-top: 10rpx;
  display: flex;
  align-items: center;
  gap: 8rpx;
}

.verify-text {
  font-size: 22rpx;
  line-height: 30rpx;
  font-weight: 700;
}

.verify-text-active {
  color: #1a57db;
}

.verify-text-idle {
  color: #94a3b8;
}

.message-btn {
  width: 84rpx;
  height: 84rpx;
  padding: 0;
  border: 0;
  border-radius: 24rpx;
  background: rgba(26, 87, 219, 0.08);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.message-icon {
  width: 40rpx;
  height: 40rpx;
  display: block;
}

.message-btn::after {
  border: 0;
}

.message-btn-hover {
  opacity: 0.84;
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
