<template>
  <view class="resource-card" hover-class="resource-card-active" @tap="$emit('detail', item)">
    <view class="card-header">
      <view class="header-left">
        <text class="type-badge" :class="`type-${item.type}`">{{ item.typeText }}</text>
        <text class="time-text">{{ item.timeText }}</text>
      </view>

      <!-- <view v-if="showInterest" class="interest-action" :class="{ 'interest-active': isInterested }"
        hover-class="interest-hover" @tap.stop="$emit('interest', item)">
        <text class="interest-icon">{{ isInterested ? '♥' : '♡' }}</text>
      </view> -->
    </view>

    <text class="resource-title">{{ item.title }}</text>
    <text v-if="item.content" class="resource-desc">{{ item.content }}</text>

    <view v-if="item.images?.length" class="image-grid" :class="`grid-${Math.min(item.images.length, 3)}`">
      <image v-for="(img, idx) in item.images.slice(0, 3)" :key="`${item.id}-${idx}`" class="grid-image" :src="img"
        mode="aspectFill" />
    </view>

    <view class="card-footer">
      <view v-if="item.industryLabels?.length" class="tags-row">
        <text v-for="(label, idx) in item.industryLabels.slice(0, 2)" :key="`${item.id}-tag-${idx}`"
          class="industry-tag">
          {{ label }}
        </text>
      </view>

      <view v-if="!item.avatars?.length" class="stats-row">
        <text class="stat-text">{{ item.readers }} 阅读</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  item: {
    type: Object,
    default: () => ({})
  },
  showInterest: {
    type: Boolean,
    default: false
  }
})

defineEmits(['detail', 'interest'])

const isInterested = computed(() => {
  return Boolean(
    props.item?.interested ||
    props.item?.isInterested ||
    props.item?.is_interested ||
    props.item?.collected ||
    props.item?.is_collected ||
    props.item?.liked ||
    props.item?.followed ||
    props.item?.isFollowed ||
    props.item?.is_followed
  )
})
</script>

<style scoped>
.resource-card {
  background: #ffffff;
  border-radius: 16rpx;
  padding: 24rpx;
  display: flex;
  flex-direction: column;
  gap: 12rpx;
  /* border: 1rpx solid rgba(15, 23, 42, 0.06); */
}

.resource-card-active {
  background: #f8f8f8;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12rpx;
}

.header-left {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.type-badge {
  flex-shrink: 0;
  padding: 4rpx 12rpx;
  border-radius: 6rpx;
  font-size: 20rpx;
  line-height: 1.3;
  font-weight: 600;
}

.type-need {
  background: rgba(251, 191, 36, 0.08);
  color: #d97706;
}

.type-offer {
  background: rgba(37, 99, 235, 0.08);
  color: #2563eb;
}

.type-venue {
  background: rgba(16, 185, 129, 0.08);
  color: #059669;
}

.time-text {
  color: #94a3b8;
  font-size: 22rpx;
  line-height: 1.3;
}

.interest-action {
  flex-shrink: 0;
  width: 48rpx;
  height: 48rpx;
  border-radius: 12rpx;
  background: #f8fafc;
  border: 1rpx solid #e2e8f0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.interest-hover {
  background: #f1f5f9;
}

.interest-active {
  background: rgba(236, 72, 153, 0.08);
  border-color: rgba(236, 72, 153, 0.2);
}

.interest-icon {
  font-size: 24rpx;
  line-height: 1;
  color: #94a3b8;
}

.interest-active .interest-icon {
  color: #ec4899;
}

.resource-title {
  color: #0f172a;
  font-size: 28rpx;
  line-height: 1.4;
  font-weight: 600;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  word-break: break-all;
}

.resource-desc {
  color: #64748b;
  font-size: 24rpx;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  word-break: break-all;
}

.image-grid {
  display: grid;
  gap: 8rpx;
  margin-top: 4rpx;
}

.grid-1 {
  grid-template-columns: repeat(3, 1fr);
}

.grid-2 {
  grid-template-columns: repeat(2, 1fr);
}

.grid-3 {
  grid-template-columns: repeat(3, 1fr);
}

.grid-image {
  width: 100%;
  height: 100%;
  border-radius: 0;
  background: #f1f5f9;
  aspect-ratio: 1 / 1;
}

.card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12rpx;
  margin-top: 4rpx;
}

.tags-row {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 8rpx;
}

.industry-tag {
  flex-shrink: 0;
  max-width: 160rpx;
  padding: 4rpx 12rpx;
  border-radius: 6rpx;
  background: rgba(15, 23, 42, 0.04);
  color: #475569;
  font-size: 20rpx;
  line-height: 1.3;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.stats-row {
  flex-shrink: 0;
}

.stat-text {
  color: #94a3b8;
  font-size: 20rpx;
  line-height: 1.3;
}

@media (prefers-color-scheme: dark) {
  .resource-card {
    background: #0f172a;
    border-color: rgba(255, 255, 255, 0.06);
  }

  .resource-card-active {
    background: #1e293b;
  }

  .type-need {
    background: rgba(251, 191, 36, 0.12);
    color: #fbbf24;
  }

  .type-offer {
    background: rgba(59, 130, 246, 0.12);
    color: #60a5fa;
  }

  .type-venue {
    background: rgba(16, 185, 129, 0.12);
    color: #34d399;
  }

  .time-text {
    color: #64748b;
  }

  .interest-action {
    background: #1e293b;
    border-color: #334155;
  }

  .interest-hover {
    background: #334155;
  }

  .interest-active {
    background: rgba(236, 72, 153, 0.14);
    border-color: rgba(236, 72, 153, 0.28);
  }

  .resource-title {
    color: #f1f5f9;
  }

  .resource-desc {
    color: #94a3b8;
  }

  .grid-image {
    background: #1e293b;
  }

  .industry-tag {
    background: rgba(255, 255, 255, 0.04);
    color: #94a3b8;
  }

  .stat-text {
    color: #64748b;
  }
}
</style>
