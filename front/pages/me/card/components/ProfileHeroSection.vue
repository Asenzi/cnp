<template>
  <view class="hero-wrap">
    <view class="hero-row">
      <image class="avatar" :src="profile.avatarUrl" mode="aspectFill" />

      <view class="meta-wrap">
        <view class="name-row">
          <text class="name">{{ profile.name }}</text>
          <view v-if="identityBadges.length" class="badge-row">
            <image
              v-for="badge in identityBadges"
              :key="badge.key"
              class="identity-badge"
              mode="aspectFit"
              :src="badge.icon"
            />
          </view>
        </view>

        <text v-if="profile.metaLine" class="meta-line">{{ profile.metaLine }}</text>
        <text v-if="profile.locationLine" class="location-line">{{ profile.locationLine }}</text>
      </view>

      <!-- <button
        v-if="showAction"
        class="message-btn"
        hover-class="message-btn-hover"
        :open-type="actionType === 'share' && isSelf ? 'share' : ''"
        @tap.stop="onTapAction"
      >
        <image
          class="message-icon"
          :src="actionType === 'share' ? 'https://cos.cnptec.site/static/icon/share.png' : 'https://cos.cnptec.site/static/icon/chat.png'"
          mode="aspectFit"
        />
      </button> -->
    </view>
  </view>
</template>

<script setup>
import { computed } from 'vue'

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
  },
  isSelf: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['message', 'share'])

const identityBadges = computed(() => {
  return Array.isArray(props.profile?.badges)
    ? props.profile.badges.filter((badge) => badge?.key && badge?.icon)
    : []
})

const onTapAction = () => {
  if (props.actionType === 'share') {
    // 如果是自己的名片，使用微信原生分享（open-type="share"）
    // 如果是别人的名片，触发 share 事件显示菜单
    if (!props.isSelf) {
      emit('share')
    }
    // isSelf=true 时，由 open-type="share" 自动触发微信分享
    return
  }
  emit('message')
}

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
  max-width: 290rpx;
  color: #111827;
  font-size: 36rpx;
  line-height: 48rpx;
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.badge-row {
  display: flex;
  align-items: center;
  gap: 8rpx;
  flex-shrink: 0;
}

.identity-badge {
  width: 32rpx;
  height: 32rpx;
  flex-shrink: 0;
}

.meta-line,
.location-line {
  color: #6b7280;
  font-size: 26rpx;
  line-height: 36rpx;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
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

  .meta-line,
  .location-line {
    color: #94a3b8;
  }

  .message-btn {
    background: rgba(59, 130, 246, 0.18);
  }
}
</style>
