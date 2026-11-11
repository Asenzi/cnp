<template>
  <view class="resource-detail-view">
    <view class="resource-copy">
      <text class="resource-heading">{{ post.title }}</text>
      <view class="resource-paragraphs"><text v-for="(paragraph, index) in paragraphs" :key="index" class="resource-paragraph">{{ paragraph }}</text></view>
    </view>
    <view class="resource-author" @tap="$emit('profile')">
      <image class="resource-avatar" :src="avatar" mode="aspectFill" />
      <view class="resource-author-copy"><text class="resource-author-name">{{ authorName }}</text><text class="resource-author-role">{{ authorDescription }}</text></view>
      <image class="resource-author-arrow" src="/static/resource-detail/arrow.png" mode="aspectFit" />
    </view>
    <view class="resource-date"><image src="/static/resource-detail/clock.png" mode="aspectFit" /><text>发布于 {{ publishedAt }}</text></view>
    <view class="resource-actions">
      <button class="resource-small-action" open-type="share" @tap="$emit('share')"><image src="/static/resource-detail/share.png" mode="aspectFit" /><text>分享</text></button>
      <button class="resource-small-action" @tap="$emit('collect')"><image src="/static/resource-detail/bookmark.png" mode="aspectFit" /><text>{{ collected ? '已收藏' : '收藏' }}</text></button>
      <button class="resource-profile-action" @tap="$emit('profile')">查看人脉</button>
    </view>
  </view>
</template>
<script setup>
import { computed } from 'vue'
const props = defineProps({ post: { type: Object, default: () => ({}) }, collected: Boolean })
defineEmits(['profile', 'share', 'collect'])
const paragraphs = computed(() => String(props.post.description || '').split(/\n+/).map(line => line.trim()).filter(Boolean))
const avatar = computed(() => props.post.author?.avatar_url || 'https://cos.cnptec.site/static/logo.png')
const authorName = computed(() => props.post.author?.nickname || '未命名用户')
const authorDescription = computed(() => {
  const author = props.post.author || {}
  return [author.job_title || author.role || author.company_name, author.city_name || author.city].filter(Boolean).join(' · ')
})
const publishedAt = computed(() => {
  const raw = String(props.post.created_at || '').trim()
  const match = raw.match(/^(\d{4}-\d{2}-\d{2})[T ](\d{2}:\d{2})/)
  return match ? `${match[1]} ${match[2]}` : (raw || '--')
})
</script>
<style scoped>
.resource-detail-view{min-height:calc(100vh - 88px);background:#f5f6f8;padding-bottom:calc(130rpx + env(safe-area-inset-bottom));box-sizing:border-box}
.resource-copy{padding:30.77rpx 30.77rpx 34.62rpx;background:#fff}
.resource-heading{display:block;font-size:38.46rpx;line-height:53.85rpx;font-weight:600;color:#171717}
.resource-paragraphs{margin-top:23.08rpx}
.resource-paragraph{display:block;white-space:pre-wrap;word-break:break-word;font-size:30.77rpx;line-height:46.15rpx;color:#414141}
.resource-paragraph+.resource-paragraph{margin-top:19.23rpx}
.resource-author{margin-top:0;padding:26.92rpx 30.77rpx;display:flex;align-items:center;background:#fff;border-bottom:1rpx solid #f0f1f3}
.resource-avatar{width:84.62rpx;height:84.62rpx;border-radius:50%;flex-shrink:0}
.resource-author-copy{margin-left:23.08rpx;flex:1;min-width:0}
.resource-author-name{display:block;font-size:30.77rpx;line-height:42.31rpx;font-weight:600;color:#171717}
.resource-author-role{display:block;font-size:25rpx;line-height:36.54rpx;color:#8b90a0;overflow:hidden;white-space:nowrap;text-overflow:ellipsis}
.resource-author-arrow{width:23.08rpx;height:30.77rpx;margin-left:15.38rpx}
.resource-date{display:flex;align-items:center;padding:0 30.77rpx;height:100rpx;box-sizing:border-box;background:#fff;color:#8b90a0;font-size:25rpx;line-height:38.46rpx}
.resource-date image{width:26.92rpx;height:26.92rpx;margin-right:15.38rpx}
.resource-actions{position:fixed;left:0;right:0;bottom:0;z-index:80;display:flex;align-items:flex-start;padding:50rpx 30.77rpx env(safe-area-inset-bottom);background:#fff}
.resource-small-action{width:69.23rpx;margin:0 34.62rpx 0 0;padding:0;border:0;background:transparent;display:flex;flex-direction:column;align-items:center;justify-content:center;flex-shrink:0;color:#888;font-size:19.23rpx;line-height:26.92rpx}
.resource-small-action image{width:46.15rpx;height:46.15rpx;margin-bottom:3.85rpx}
.resource-small-action::after,.resource-profile-action::after{border:0}
.resource-profile-action{flex:1;margin:0;padding:0;height:76.92rpx;line-height:76.92rpx;border:0;border-radius:40rpx;background:#2563eb;color:#fff;font-size:28.85rpx;font-weight:600}
</style>
