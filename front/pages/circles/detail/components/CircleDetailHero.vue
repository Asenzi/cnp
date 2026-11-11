<template><view class="hero"><image class="banner" mode="aspectFill" :src="detail.bannerImage"/><view class="info"><view class="heading"><image class="logo" mode="aspectFill" :src="detail.logoImage"/><view class="heading-copy"><view class="title-row"><text class="title">{{detail.title}}</text><view class="paid"><image v-if="detail.levelTag === '付费圈'" src="/static/circle-detail-reference/crown.png" mode="aspectFit"/><text>{{detail.levelTag}}</text></view></view><view class="meta"><view><image src="/static/circle-detail-reference/category.png" mode="aspectFit"/><text>{{detail.category || '未分类'}}</text></view><text class="circle-price">{{ Number(detail.price?.current || 0) > 0 ? '¥' + Number(detail.price.current).toFixed(2) : '免费' }}</text></view></view></view><view class="description-wrap"><text class="description" :class="{'collapsed':!descriptionExpanded}">{{detail.description}}</text><text v-if="shouldShowExpandBtn" class="expand" @tap="toggleDescription">{{descriptionExpanded?'收起':'展开'}}</text></view></view></view></template>
<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  detail: {
    type: Object,
    default: () => ({})
  }
})

const descriptionExpanded = ref(false)

const shouldShowExpandBtn = computed(() => {
  const text = String(props.detail?.description || '')
  return text.length > 60
})

const toggleDescription = () => {
  if (shouldShowExpandBtn.value) {
    descriptionExpanded.value = !descriptionExpanded.value
  }
}
</script>
<style scoped>.banner{display:block;width:100%;height:270rpx;border-radius:0}.info{position:relative;margin-top:0;padding:22rpx 24rpx;background:#fff;border-radius:0}.heading{display:flex;gap:20rpx}.logo{width:108rpx;height:108rpx;border-radius:14rpx;flex-shrink:0}.heading-copy{flex:1;min-width:0}.title-row{display:flex;align-items:center;justify-content:space-between;gap:12rpx}.title{font-size:30rpx;font-weight:600;line-height:44rpx}.paid{display:flex;align-items:center;gap:8rpx;border-radius:30rpx;background:#ffead9;color:#733c1b;padding:6rpx 14rpx;font-size:28rpx;white-space:nowrap}.paid image{width:29rpx;height:26rpx}.meta{display:flex;flex-wrap:wrap;gap:12rpx;margin-top:16rpx;color:#626779;font-size:28rpx;line-height:38rpx}.meta view{display:flex;align-items:center;gap:8rpx}.meta image{width:25rpx;height:25rpx;flex-shrink:0}.description-wrap{margin-top:16rpx}.description{display:block;font-size:28rpx;line-height:40rpx;color:#5c6070}.collapsed{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}.expand{display:block;text-align:right;font-size:28rpx;color:#2160ff;line-height:38rpx}.circle-price{font-size:30rpx;font-weight:700;line-height:38rpx;color:#ff3333;margin-left:auto;white-space:nowrap}
</style>