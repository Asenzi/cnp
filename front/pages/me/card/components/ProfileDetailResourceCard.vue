<template>
  <view class="resource-card" hover-class="resource-card-active" @tap="$emit('detail', item)">
    <image v-if="item.images && item.images.length" class="resource-cover" :src="item.images[0]" mode="aspectFill" />
    <view class="resource-main">
      <view class="resource-title-row"><text class="resource-title">{{ item.title }}</text><image class="chevron" src="/static/profile-card/arrow.png" mode="aspectFit" /></view>
      <view class="tags-row"><text class="type-tag">{{ item.typeText }}</text><text v-for="label in (item.industryLabels || []).slice(0, 1)" :key="label" class="industry-tag">{{ label }}</text></view>
      <view class="resource-footer"><text class="time-text">{{ item.timeText }}</text><view class="stat"><image src="/static/profile-card/eye.png" mode="aspectFit"/><text>{{ item.readers }}</text></view><view class="stat"><image src="/static/profile-card/star.png" mode="aspectFit"/><text>{{ item.collectCount || 0 }}</text></view></view>
    </view>
  </view>
</template>
<script setup>
defineProps({ item: { type: Object, default: () => ({}) }, showInterest: Boolean })
defineEmits(['detail', 'interest'])
</script>
<style scoped>
.resource-card{display:flex;gap:20rpx;padding:20rpx 0;background:#fff}.resource-card-active{opacity:.8}.resource-cover{width:148rpx;height:120rpx;border-radius:0;flex-shrink:0}.resource-main{flex:1;min-width:0;display:flex;flex-direction:column;justify-content:space-between}.resource-title-row{display:flex;gap:10rpx;align-items:flex-start}.resource-title{flex:1;min-width:0;color:#151a23;font-size:30rpx;line-height:42rpx;font-weight:500;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}.chevron{width:22rpx;height:32rpx;flex-shrink:0}.tags-row{display:flex;gap:10rpx;flex-wrap:wrap;margin:10rpx 0 12rpx}.type-tag,.industry-tag{font-size:28rpx;line-height:42rpx;border-radius:0;padding:1rpx 10rpx}.type-tag{color:#1c5fd6;background:#eaf2ff}.industry-tag{color:#81443b;background:#f9eeeb}.resource-footer{display:flex;align-items:center;gap:14rpx;color:#7d8493;font-size:28rpx;line-height:42rpx}.time-text{flex:1}.stat{display:flex;align-items:center;gap:5rpx}.stat image{width:28rpx;height:28rpx}
</style>
