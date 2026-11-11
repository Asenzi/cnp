<template><view class="panel"><view class="facts"><view class="created"><image src="/static/circle-detail-reference/calendar.png"/><view><text class="muted">创建时间</text><text>{{createdDate || '--'}}</text></view></view><view class="creator" @tap="$emit('owner')"><image class="avatar" :src="owner.avatar" mode="aspectFill"/><view><text class="muted">创建者</text><view class="owner-name"><text>{{owner.name}}</text><image v-if="owner.verified" class="verified" src="/static/circle-detail-reference/verified.png"/></view></view></view></view><view class="actions"><button class="secondary" @tap="$emit('interest')"><image src="/static/circle-detail-reference/star.png" mode="aspectFit"/>{{interested?'已收藏':'收藏'}}</button><button class="secondary" open-type="share"><image src="/static/circle-detail-reference/share.png" mode="aspectFit"/>分享</button><button class="primary" :disabled="disabled" @tap="$emit('join')"><image src="/static/circle-detail-reference/join.png" mode="aspectFit"/>{{actionText}}</button></view></view></template>
<script setup>
import { computed } from 'vue'

const props = defineProps({
  detail: { type: Object, default: () => ({}) },
  interested: Boolean,
  disabled: Boolean,
  actionText: { type: String, default: '加入圈子' }
})
defineEmits(['interest', 'join', 'owner'])

// Mini-program components can render before asynchronously linked props arrive.
const owner = computed(() => props.detail?.owner || {})
const createdDate = computed(() => props.detail?.createdDate || '--')
</script>
<style scoped>.panel{margin-top:16rpx;padding:26rpx 24rpx 28rpx;background:#fff;border-radius:24rpx}.facts{display:flex;align-items:stretch;font-size:28rpx;line-height:38rpx;color:#3f4457}.created,.creator{position:relative;display:flex;align-items:center;justify-content:center;gap:12rpx;flex:1 1 0;min-width:0;box-sizing:border-box;padding:0 12rpx}.created>image{width:32rpx;height:32rpx;align-self:flex-start;margin-top:5rpx;flex-shrink:0}.created>view,.creator>view{display:flex;flex-direction:column;gap:4rpx}.creator::before{content:"";position:absolute;left:0;top:50%;transform:translateY(-50%);width:1rpx;height:54rpx;background:#e0e3ec}.creator>view{min-width:0}.owner-name>text{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.avatar{width:64rpx;height:64rpx;border-radius:10rpx;flex-shrink:0}.owner-name{display:flex;align-items:center;gap:8rpx;font-size:30rpx;font-weight:600;color:#101321}.verified{width:24rpx;height:24rpx}.muted{color:#727582;font-size:28rpx;font-weight:400}.actions{display:flex;gap:18rpx;margin-top:32rpx}.actions button{display:flex;align-items:center;justify-content:center;gap:10rpx;height:58rpx;line-height:40rpx;margin:0;padding:0 12rpx;border-radius:14rpx;font-size:28rpx;white-space:nowrap}.actions image{width:30rpx;height:30rpx;flex-shrink:0}.secondary{flex:1;background:#fff;border:1rpx solid #bdcafa;color:#41475d}.primary{flex:1.2;background:#2160ff;color:#fff}.actions button::after{border:0}.primary[disabled]{opacity:.55}</style>