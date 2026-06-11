<template>
  <view class="circle-card" hover-class="circle-card-active" @tap="openCircle">
    <view class="card-header">
      <image
        v-if="displayCoverImage"
        class="circle-cover"
        mode="aspectFill"
        :src="displayCoverImage"
        @error="onCoverError"
      />
      <view v-else class="circle-cover circle-cover-placeholder"></view>

      <view class="header-content">
        <view class="title-row">
          <text class="circle-title">{{ circle.title }}</text>
          <view
            class="interest-action"
            :class="{ 'interest-action-active': isInterested }"
            hover-class="interest-action-hover"
            @tap.stop="$emit('interest', circle)"
          >
            <text class="interest-icon">{{ isInterested ? '♥' : '♡' }}</text>
            <text class="interest-text">{{ isInterested ? '已感兴趣' : '感兴趣' }}</text>
          </view>
        </view>

        <text v-if="circle.industryLabel" class="industry-tag">{{ circle.industryLabel }}</text>

        <view class="stats-row">
          <view class="stat-item">
            <text class="stat-value">{{ circle.members }}</text>
            <text class="stat-label">成员</text>
          </view>
          <view class="stat-divider"></view>
          <view class="stat-item">
            <text class="stat-value">{{ circle.posts }}</text>
            <text class="stat-label">动态</text>
          </view>
        </view>
      </view>
    </view>

    <text v-if="circle.description" class="circle-desc">{{ circle.description }}</text>
  </view>
</template>

<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  circle: {
    type: Object,
    default: () => ({})
  }
})

defineEmits(['interest'])

const normalizeCircleImage = (value) => {
  const normalized = String(value || '').trim()
  if (!normalized) {
    return ''
  }
  if (normalized === 'https://cos.cnptec.site/static/logo.png' || /\/static\/logo\.png(?:[?#].*)?$/i.test(normalized)) {
    return ''
  }
  if (/^(https?:\/\/tmp\/|wxfile:\/\/|file:\/\/|blob:|data:image\/)/i.test(normalized)) {
    return ''
  }
  return normalized
}

const coverImage = ref('')

watch(
  () => props.circle?.coverImage,
  (nextValue) => {
    coverImage.value = normalizeCircleImage(nextValue)
  },
  { immediate: true }
)

const isInterested = computed(() => {
  return Boolean(
    props.circle?.interested ||
    props.circle?.isInterested ||
    props.circle?.is_interested ||
    props.circle?.followed ||
    props.circle?.isFollowed ||
    props.circle?.is_followed
  )
})

const displayCoverImage = computed(() => normalizeCircleImage(coverImage.value))

const onCoverError = () => {
  coverImage.value = ''
}

const openCircle = () => {
  const circleCode = String(props.circle?.circleCode || '').trim()
  if (!circleCode) {
    return
  }
  uni.navigateTo({
    url: `/pages/circles/detail/index?code=${encodeURIComponent(circleCode)}`
  })
}
</script>

<style scoped>
.circle-card {
  background: #ffffff;
  border-radius: 16rpx;
  padding: 24rpx;
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.circle-card-active {
  background: #fafbfc;
}

.card-header {
  display: flex;
  gap: 16rpx;
  align-items: flex-start;
}

.circle-cover {
  width: 120rpx;
  height: 120rpx;
  border-radius: 12rpx;
  flex-shrink: 0;
  background: #f1f5f9;
}

.circle-cover-placeholder {
  background:
    linear-gradient(135deg, rgba(148, 163, 184, 0.12), rgba(226, 232, 240, 0.35)),
    #f8fafc;
}

.header-content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.title-row {
  display: flex;
  align-items: center;
  gap: 8rpx;
}

.circle-title {
  flex: 1;
  min-width: 0;
  color: #0f172a;
  font-size: 28rpx;
  line-height: 1.3;
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.industry-tag {
  display: inline-block;
  align-self: flex-start;
  padding: 4rpx 12rpx;
  border-radius: 6rpx;
  background: rgba(15, 23, 42, 0.04);
  color: #475569;
  font-size: 20rpx;
  line-height: 1.3;
  font-weight: 500;
}

.stats-row {
  display: flex;
  align-items: center;
  gap: 16rpx;
  margin-top: 4rpx;
}

.stat-item {
  display: flex;
  align-items: baseline;
  gap: 4rpx;
}

.stat-value {
  color: #0f172a;
  font-size: 24rpx;
  line-height: 1.3;
  font-weight: 600;
}

.stat-label {
  color: #94a3b8;
  font-size: 20rpx;
  line-height: 1.3;
}

.stat-divider {
  width: 1rpx;
  height: 20rpx;
  background: #e2e8f0;
}

.circle-desc {
  color: #64748b;
  font-size: 24rpx;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  word-break: break-all;
}

.interest-action {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 6rpx;
  padding: 6rpx 12rpx;
  border-radius: 999rpx;
  background: #f8fafc;
  border: 1rpx solid #e2e8f0;
}

.interest-action-hover {
  background: #f1f5f9;
}

.interest-action-active {
  background: rgba(239, 68, 68, 0.06);
  border-color: rgba(239, 68, 68, 0.15);
}

.interest-icon {
  font-size: 20rpx;
  line-height: 1;
  color: #94a3b8;
}

.interest-action-active .interest-icon {
  color: #ef4444;
}

.interest-text {
  color: #64748b;
  font-size: 20rpx;
  line-height: 1.3;
  font-weight: 500;
}

.interest-action-active .interest-text {
  color: #ef4444;
}

@media (prefers-color-scheme: dark) {
  .circle-card {
    background: #0f172a;
    border-color: rgba(255, 255, 255, 0.06);
  }

  .circle-card-active {
    background: #1e293b;
  }

  .circle-cover {
    background: #1e293b;
  }

  .circle-cover-placeholder {
    border-color: #334155;
  }

  .circle-title {
    color: #f1f5f9;
  }

  .industry-tag {
    background: rgba(255, 255, 255, 0.08);
    color: #cbd5e1;
  }

  .stat-value {
    color: #f1f5f9;
  }

  .stat-label {
    color: #94a3b8;
  }

  .stat-divider {
    background: #334155;
  }

  .circle-desc {
    color: #94a3b8;
  }

  .interest-action {
    background: #111827;
    border-color: #334155;
  }

  .interest-action-hover {
    background: #1f2937;
  }

  .interest-text {
    color: #cbd5e1;
  }
}
</style>
