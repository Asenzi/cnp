<template>
  <view class="bio-wrap">
    <view class="section-heading"><text>个人简介</text></view>
    <view v-for="row in rows" :key="row.key" class="bio-row">
      <image class="bio-icon" :src="'/static/profile-card/' + row.icon + '.png'" mode="aspectFit" />
      <view class="bio-copy"><text class="bio-label">{{ row.label }}</text><text class="bio-text">{{ row.value || '暂未填写' }}</text></view>
    </view>
  </view>
</template>
<script setup>
import { computed } from 'vue'
const props = defineProps({ bio: { type: String, default: '' }, details: { type: Object, default: () => ({}) } })
const rows = computed(() => [
  { key: 'location', icon: 'location', label: '我来自', value: props.details.location },
  { key: 'occupation', icon: 'work', label: '我是做什么的', value: props.details.occupation || props.bio },
  { key: 'service', icon: 'people', label: '我为谁提供什么', value: props.details.service },
  { key: 'problem', icon: 'growth', label: '解决什么问题', value: props.details.problem },
  { key: 'value', icon: 'value', label: '带来什么价值', value: props.details.value },
  { key: 'hobbies', icon: 'heart', label: '我的爱好', value: props.details.hobbies }
])
</script>
<style scoped>
.bio-wrap{background:#fff;border-radius:0;padding:22rpx 34rpx 20rpx;box-shadow:0 8rpx 24rpx rgba(27,44,70,.04)}
.section-heading{font-size:28rpx;line-height:40rpx;font-weight:600;color:#111925;margin-bottom:18rpx}.section-heading text{display:inline-block;padding-bottom:8rpx;border-bottom:3rpx solid #172133}
.bio-row{display:flex;align-items:flex-start;gap:24rpx;margin-top:22rpx}.bio-icon{width:38rpx;height:38rpx;margin-top:2rpx;flex-shrink:0}.bio-copy{flex:1;min-width:0}.bio-label{display:block;font-size:30rpx;line-height:42rpx;font-weight:600;color:#161d29}.bio-text{display:block;margin-top:4rpx;white-space:pre-wrap;overflow-wrap:break-word;font-size:28rpx;line-height:42rpx;color:#596274}
</style>
