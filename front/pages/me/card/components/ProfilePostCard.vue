<template>
  <view class="post-card" hover-class="post-card-active" @tap="$emit('detail', item)">
    <view class="meta-row">
      <text class="type-tag" :class="item.type === 'need' ? 'type-need' : item.type === 'venue' ? 'type-venue' : 'type-offer'">
        {{ item.typeText }}
      </text>
      <text class="time-text">{{ item.timeText }}</text>
    </view>

    <text class="title">{{ item.title }}</text>
    <text class="content">{{ item.content }}</text>

    <view v-if="item.images?.length" class="image-grid">
      <image v-for="(img, idx) in item.images" :key="`${item.id}-${idx}`" class="grid-image" :src="img" mode="aspectFill" />
    </view>

    <view class="footer-row">
      <view v-if="item.avatars?.length" class="avatar-stack">
        <view
          v-for="(color, idx) in item.avatars"
          :key="`${item.id}-avatar-${idx}`"
          class="stack-item"
          :style="{ background: color }"
        ></view>
      </view>

      <view v-else class="read-row">
        <ProfileSymbol name="visibility" :size="16" color="#94a3b8" />
        <text class="metric-text">{{ item.readers }} 阅读</text>
      </view>

      <view v-if="item.industryLabels?.length" class="industry-row">
        <text
          v-for="(label, idx) in item.industryLabels.slice(0, 2)"
          :key="`${item.id}-industry-${idx}`"
          class="industry-tag"
        >
          {{ label }}
        </text>
      </view>
    </view>
  </view>
</template>

<script setup>
import ProfileSymbol from './ProfileSymbol.vue'

defineProps({
  item: {
    type: Object,
    default: () => ({})
  }
})

defineEmits(['detail'])
</script>

<style scoped>
.post-card {
  background: #ffffff;
  border-radius: 20rpx;
  border: 1rpx solid #f1f5f9;
  box-shadow: 0 2rpx 8rpx rgba(15, 23, 42, 0.04);
  padding: 24rpx;
}

.post-card-active {
  opacity: 0.9;
}

.meta-row {
  display: flex;
  align-items: center;
  gap: 10rpx;
  margin-bottom: 14rpx;
}

.type-tag {
  padding: 4rpx 12rpx;
  border-radius: 8rpx;
  font-size: 16rpx;
  line-height: 24rpx;
  font-weight: 700;
}

.type-need {
  background: #ffedd5;
  color: #ea580c;
}

.type-offer {
  background: rgba(26, 87, 219, 0.1);
  color: #1a57db;
}

.type-venue {
  background: rgba(5, 150, 105, 0.12);
  color: #047857;
}

.time-text {
  color: #94a3b8;
  font-size: 20rpx;
  line-height: 28rpx;
}

.title {
  display: block;
  color: #0f172a;
  font-size: 30rpx;
  line-height: 40rpx;
  font-weight: 700;
}

.content {
  margin-top: 8rpx;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  color: #64748b;
  font-size: 24rpx;
  line-height: 34rpx;
}

.image-grid {
  margin-top: 14rpx;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8rpx;
}

.grid-image {
  width: 100%;
  height: 180rpx;
  border-radius: 12rpx;
  background: #f1f5f9;
}

.footer-row {
  margin-top: 16rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.avatar-stack {
  display: flex;
  align-items: center;
}

.stack-item {
  width: 44rpx;
  height: 44rpx;
  border-radius: 999rpx;
  border: 4rpx solid #ffffff;
  margin-left: -12rpx;
}

.stack-item:first-child {
  margin-left: 0;
}

.read-row {
  display: flex;
  align-items: center;
  gap: 6rpx;
}

.industry-row {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12rpx;
}

.industry-tag {
  max-width: 156rpx;
  padding: 6rpx 14rpx;
  border-radius: 999rpx;
  background: rgba(26, 87, 219, 0.1);
  color: #1a57db;
  font-size: 20rpx;
  line-height: 28rpx;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.metric-text {
  color: #94a3b8;
  font-size: 20rpx;
  line-height: 28rpx;
}

@media (prefers-color-scheme: dark) {
  .post-card {
    background: #0f172a;
    border-color: #1e293b;
    box-shadow: none;
  }

  .title {
    color: #f8fafc;
  }

  .content {
    color: #94a3b8;
  }

  .grid-image {
    background: #334155;
  }

  .industry-tag {
    background: rgba(96, 165, 250, 0.18);
    color: #bfdbfe;
  }

  .stack-item {
    border-color: #0f172a;
  }
}
</style>
