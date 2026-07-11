<template>
  <view class="member-card" hover-class="member-card-active" @tap="$emit('detail', member)">
    <image class="member-avatar" mode="aspectFill" :src="member.avatar_url || defaultAvatar" />
    <view class="member-info">
      <view class="member-name-row">
        <text class="member-name">{{ member.nickname || '未命名用户' }}</text>
        <image
          v-if="member.is_verified"
          class="verified-icon"
          mode="aspectFit"
          src="https://cos.cnptec.site/static/icon/certification.png"
        />
      </view>
      <text v-if="memberMetaText" class="member-meta">{{ memberMetaText }}</text>
    </view>
  </view>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  member: {
    type: Object,
    default: () => ({})
  }
})

defineEmits(['detail'])

const defaultAvatar = 'https://cos.cnptec.site/static/logo.png'

const memberMetaText = computed(() => {
  const company = String(props.member?.company || props.member?.company_name || '').trim()
  const jobTitle = String(props.member?.job_title || props.member?.position || '').trim()

  if (company && jobTitle) {
    return `${company} · ${jobTitle}`
  }
  return company || jobTitle || ''
})
</script>

<style scoped>
.member-card {
  background: #ffffff;
  padding: 20rpx 0;
  border-bottom: 1rpx solid #f3f4f6;
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.member-card-active {
  opacity: 0.7;
}

.member-avatar {
  width: 88rpx;
  height: 88rpx;
  border-radius: 8rpx;
  background: #f3f4f6;
  flex-shrink: 0;
}

.member-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 6rpx;
}

.member-name-row {
  display: flex;
  align-items: center;
  gap: 8rpx;
}

.member-name {
  color: #111827;
  font-size: 28rpx;
  line-height: 36rpx;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.verified-icon {
  width: 30rpx;
  height: 30rpx;
  flex-shrink: 0;
}

.member-meta {
  color: #6b7280;
  font-size: 24rpx;
  line-height: 32rpx;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

@media (prefers-color-scheme: dark) {
  .member-card {
    background: #111827;
    border-bottom-color: #1f2937;
  }

  .member-avatar {
    background: #1f2937;
  }

  .member-name {
    color: #f9fafb;
  }

  .member-meta {
    color: #9ca3af;
  }

}
</style>
