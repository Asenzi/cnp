<template>
  <view class="feed-resource-card" hover-class="feed-resource-card-pressed" @tap="$emit('detail', item)">
    <view class="feed-resource-copy">
      <view class="feed-resource-meta">
        <text class="feed-resource-type" :class="isEvent ? 'feed-resource-type-event' : ''">{{ isEvent ? '活动' : '供需' }}</text>
        <text class="feed-resource-time">{{ displayTime }}</text>
        <slot name="collection-action" />
      </view>
      <text class="feed-resource-title">{{ item.title }}</text>
      <text class="feed-resource-description">{{ item.content }}</text>
      <view class="feed-resource-stats">
        <view class="feed-resource-stat">
          <image class="feed-resource-eye" src="/static/resource-feed/eye.png" mode="aspectFit" />
          <text class="feed-resource-count">{{ readersText }}</text>
        </view>
        <view class="feed-resource-stat feed-resource-collect" :class="item.collected ? 'feed-resource-collected' : ''" @tap.stop="$emit('interest', item)">
          <image class="feed-resource-star" src="/static/resource-feed/star.png" mode="aspectFit" />
          <text class="feed-resource-count">{{ collectionText }}</text>
        </view>
      </view>
    </view>
    <image v-if="coverUrl" class="feed-resource-cover" :src="coverUrl" mode="aspectFill" />
  </view>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({ item: { type: Object, default: () => ({}) } })
defineEmits(['detail', 'interest'])

const isEvent = computed(() => props.item.type === 'venue')
const coverUrl = computed(() => props.item.images?.[0] || props.item.rawPost?.cover_url || '')
const displayTime = computed(() => {
  const raw = String(props.item.rawPost?.created_at || '').trim()
  const match = raw.match(/^(\d{4}-\d{2}-\d{2})[T ](\d{2}:\d{2})/)
  return match ? `${match[1]} ${match[2]}` : String(props.item.timeText || '')
})
const formatCount = value => Math.max(0, Number(value) || 0).toLocaleString('en-US')
const readersText = computed(() => formatCount(props.item.readers))
const collectionText = computed(() => formatCount(props.item.collectCount))
</script>

<style scoped>
.feed-resource-card {
  position: relative;
  display: flex;
  align-items: flex-start;
  box-sizing: border-box;
  min-height: 215rpx;
  padding: 20rpx 50rpx 16.25rpx 27rpx;
  background: #fff;
  border-radius: 25rpx;
  font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei', sans-serif;
  font-size: 28rpx;
  font-weight: 400;
  letter-spacing: 0;
}
.feed-resource-card-pressed { opacity: .85; }
.feed-resource-copy { flex: 1; min-width: 0; }
.feed-resource-meta { display: flex; align-items: center; min-height: 42rpx; margin-left: -3rpx; }
.feed-resource-type { flex-shrink: 0; margin-right: 17rpx; padding: 1rpx 17rpx; border-radius: 8rpx; background: #e1ebfe; color: #1555e7; font-size: 28rpx; line-height: 40rpx; }
.feed-resource-type-event { background: #ffe7e7; color: #c52424; }
.feed-resource-time { min-width: 0; font-size: 28rpx; line-height: 40rpx; color: #9199a7; white-space: nowrap; }
.feed-resource-title { display: block; margin-top: 7rpx; font-size: 30rpx; line-height: 42rpx; font-weight: 600; color: #0b1021; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.feed-resource-description { display: -webkit-box; margin-top: 8rpx; max-height: 80rpx; overflow: hidden; -webkit-line-clamp: 2; -webkit-box-orient: vertical; font-size: 28rpx; line-height: 40rpx; color: #5d6778; word-break: break-all; }
.feed-resource-stats { display: flex; align-items: center; margin-top: 12.75rpx; min-height: 40rpx; }
.feed-resource-stat { display: flex; align-items: center; font-size: 28rpx; line-height: 40rpx; color: #8d94a3; }
.feed-resource-stat + .feed-resource-stat { margin-left: 42rpx; }
.feed-resource-count { display: block; margin-left: 12.25rpx; font-size: 28rpx; line-height: 40rpx; font-weight: 400; letter-spacing: 0; }
.feed-resource-collect { position: relative; }
.feed-resource-collect::after { content: ''; position: absolute; left: -10rpx; right: -16rpx; top: -10rpx; bottom: -10rpx; }
.feed-resource-collected { color: #1555e7; }
.feed-resource-eye { display: block; width: 29rpx; height: 24rpx; flex-shrink: 0; }
.feed-resource-star { display: block; width: 25rpx; height: 25rpx; flex-shrink: 0; }
.feed-resource-cover { width: 220rpx; height: 220rpx; margin-top: 3rpx; margin-left: 25rpx; border-radius: 16rpx; flex-shrink: 0; }
</style>
