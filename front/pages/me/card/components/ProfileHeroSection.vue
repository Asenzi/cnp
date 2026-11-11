<template>
  <view class="hero-wrap">
    <image class="hero-skyline" src="https://cos.cnptec.site/static/profile-card/skyline-full-v2-20261026.png" mode="widthFix" />
    <view class="hero-row">
      <image class="avatar" :src="profile.avatarUrl" mode="aspectFill" />
      <view class="meta-wrap">
        <view class="name-row">
          <text class="name">{{ profile.name }}</text>
          <image v-for="badge in profile.badges || []" :key="badge.key" class="identity-badge" :src="badge.icon" mode="aspectFit" />
        </view>
        <text class="meta-line">{{ profile.companyName || '暂未填写公司' }}</text>
        <text class="meta-line">{{ profile.jobTitle || '暂未填写职位' }}</text>
      </view>
    </view>
    <view v-if="profile.tags && profile.tags.length" class="tag-row">
      <text v-for="tag in profile.tags" :key="tag" class="profile-tag">{{ tag }}</text>
    </view>
    <view class="hero-actions">
      <button class="hero-button" :disabled="collecting" @tap="$emit('collect')">
        <image class="action-icon" src="/static/profile-card/collect.png" mode="aspectFit" />
        <text>{{ collected ? '已收藏' : '收藏' }}</text>
      </button>
      <button class="hero-button" open-type="share" @tap="$emit('share')">
        <image class="action-icon" src="/static/profile-card/share.png" mode="aspectFit" /><text>分享</text>
      </button>
      <button class="hero-button contact-button" @tap="$emit('contact')">
        <image class="wechat-icon" src="/static/profile-card/wechat.png" mode="aspectFit" /><text>联系</text>
      </button>
    </view>
  </view>
</template>
<script setup>
defineProps({ profile: { type: Object, default: () => ({}) }, collected: Boolean, collecting: Boolean })
defineEmits(['collect', 'share', 'contact'])
</script>
<style scoped>
.hero-wrap{position:relative;overflow:hidden;padding:24rpx 32rpx 22rpx;background:#fff;border-radius:0;box-shadow:0 8rpx 24rpx rgba(27,44,70,.04)}
.hero-skyline{position:absolute;left:0;top:0;width:100%;height:auto;display:block}
.hero-row,.tag-row,.hero-actions{position:relative;display:flex;align-items:center}
.hero-row{gap:24rpx;min-height:164rpx}.avatar{width:164rpx;height:164rpx;border:7rpx solid #fff;border-radius:50%;box-sizing:border-box;flex-shrink:0}
.meta-wrap{flex:1;min-width:0}.name-row{display:flex;align-items:center;gap:12rpx;margin-bottom:5rpx}.name{font-size:42rpx;font-weight:600;line-height:52rpx;color:#111925;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:290rpx}.identity-badge{width:36rpx;height:32rpx;flex-shrink:0}.meta-line{display:block;font-size:28rpx;line-height:40rpx;color:#182132;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.tag-row{gap:12rpx;margin-top:14rpx;flex-wrap:wrap}.profile-tag{padding:3rpx 14rpx;background:rgba(232,232,234,.8);border-radius:12rpx;font-size:22rpx;line-height:30rpx;color:#172133}
.hero-actions{gap:24rpx;margin-top:32rpx}.hero-button{margin:0;padding:0;flex:1;min-width:0;height:74rpx;display:flex;align-items:center;justify-content:center;gap:10rpx;background:#fff;border:1rpx solid #e2e5eb;border-radius:22rpx;box-shadow:0 3rpx 7rpx rgba(32,47,67,.05);font-size:26rpx;line-height:36rpx;font-weight:500;color:#111925}.hero-button::after{border:0}.action-icon{width:36rpx;height:36rpx}.contact-button{background:#1e3047;color:#fff;border-color:#142338}.wechat-icon{width:42rpx;height:40rpx}
</style>
