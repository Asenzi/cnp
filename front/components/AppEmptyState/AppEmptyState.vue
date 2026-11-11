<template>
  <view class="app-empty-state">
    <image class="app-empty-icon" src="/static/icon/data-block.png" mode="aspectFit" />
    <text class="app-empty-title"><slot name="title">暂无匹配内容</slot></text>
    <text v-if="$slots.description" class="app-empty-description"><slot name="description" /></text>
    <slot />
  </view>
</template>
<style scoped>
.app-empty-state{min-height:320rpx;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:20rpx;padding:120rpx 32rpx 80rpx;background:transparent}
.app-empty-icon{width:200rpx;height:200rpx;margin-bottom:12rpx;flex-shrink:0}
.app-empty-title{color:#1e293b;font-size:32rpx;line-height:44rpx;font-weight:600;margin-top:8rpx;text-align:center}
.app-empty-description{color:#64748b;font-size:26rpx;line-height:36rpx;text-align:center}
</style>
