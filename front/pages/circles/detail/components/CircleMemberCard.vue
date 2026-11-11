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
    <image class="member-arrow" src="/static/circle-detail-reference/chevron.png" mode="aspectFit"/>
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

<style scoped>.member-card{display:flex;align-items:center;gap:20rpx;padding:18rpx 0;border-bottom:1rpx solid #e7eaf2}.member-avatar{width:70rpx;height:68rpx;border-radius:12rpx;flex-shrink:0}.member-info{flex:1;min-width:0}.member-name-row{display:flex;align-items:center;gap:10rpx}.member-name{font-size:30rpx;line-height:42rpx;font-weight:600;color:#101321}.verified-icon{width:26rpx;height:26rpx}.member-meta{display:block;font-size:28rpx;line-height:40rpx;color:#70737f}.member-arrow{width:15rpx;height:24rpx}</style>