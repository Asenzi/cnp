<template>
  <view class="directory-card" hover-class="directory-card-pressed" @tap="openCircle">
    <image v-if="circle.coverImage && !coverFailed" class="directory-cover" :src="circle.coverImage" mode="aspectFill" @error="coverFailed = true" />
    <view v-else class="directory-cover directory-cover-empty"></view>
    <view class="directory-main">
      <view class="directory-heading"><text class="directory-title">{{ circle.title }}</text><slot name="collection-action"><view class="directory-views"><image src="/static/circle-directory/eye.png" mode="aspectFit"/><text>{{ circle.views ?? '0' }}</text></view></slot></view>
      <view v-if="circle.industryLabel" class="directory-industry"><image :src="industryIcon" mode="aspectFit"/><text>{{ circle.industryLabel }}</text></view>
      <view class="directory-stats">
        <view class="directory-stat"><image src="/static/circle-directory/members.png" mode="aspectFit"/><text class="directory-number">{{ circle.members }}</text><text class="directory-label">成员</text></view>
        <view class="directory-stat directory-resource-stat"><image src="/static/circle-directory/resources.png" mode="aspectFit"/><text class="directory-number">{{ circle.posts }}</text><text class="directory-label">资源（含活动）</text></view>
      </view>
    </view>
  </view>
</template>
<script setup>
import { computed, ref, watch } from 'vue'
const props = defineProps({ circle: { type: Object, default: () => ({}) } })
const coverFailed = ref(false)
watch(() => props.circle.coverImage, () => { coverFailed.value = false })
const industryIcon = computed(() => {
  const label = String(props.circle.industryLabel || '')
  const icon = /教育|培训/.test(label) ? 'education' : /互联网|AI|软件|科技/.test(label) ? 'computer' : /金融/.test(label) ? 'finance' : /电商|零售/.test(label) ? 'shopping' : 'business'
  return `/static/circle-directory/${icon}.png`
})
const openCircle = () => {
  const code = String(props.circle.circleCode || '').trim()
  if (code) uni.navigateTo({ url: `/pages/circles/detail/index?code=${encodeURIComponent(code)}` })
}
</script>
<style scoped>
.directory-card{display:flex;align-items:center;padding:30rpx 24rpx;min-height:202rpx;box-sizing:border-box;background:#fff;border-radius:12rpx;box-shadow:0 10rpx 26rpx rgba(89,87,145,.07)}
.directory-card-pressed{opacity:.85}
.directory-cover{width:143rpx;height:143rpx;border-radius:18rpx;flex-shrink:0}
.directory-cover-empty{background:#f4f5fa}
.directory-main{flex:1;min-width:0;margin-left:24rpx;margin-top:-3rpx}
.directory-heading{display:flex;align-items:center;min-width:0}
.directory-title{flex:1;min-width:0;font-size:30rpx;line-height:40rpx;font-weight:600;color:#171a30;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.directory-views{display:flex;align-items:center;flex-shrink:0;margin-left:12rpx;color:#7b7da4;font-size:26rpx;line-height:36rpx}
.directory-views image{width:28rpx;height:24rpx;margin-right:8rpx}
.directory-industry{display:inline-flex;align-items:center;max-width:100%;padding:2rpx 13rpx;margin-top:8rpx;border-radius:11rpx;background:#eeedf8;color:#41466a;font-size:26rpx;line-height:34rpx;box-sizing:border-box}
.directory-industry image{width:28rpx;height:26rpx;margin-right:9rpx;flex-shrink:0}
.directory-industry text{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.directory-stats{display:flex;align-items:center;flex-wrap:wrap;row-gap:6rpx;margin-top:10rpx}
.directory-stat{display:flex;align-items:center;white-space:nowrap}
.directory-stat image{width:30rpx;height:30rpx;margin-right:9rpx;flex-shrink:0}
.directory-resource-stat{margin-left:28rpx}
.directory-number{font-size:28rpx;line-height:36rpx;color:#202238;font-weight:400}
.directory-label{font-size:26rpx;line-height:36rpx;color:#73758c;margin-left:5rpx}
</style>
