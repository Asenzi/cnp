<template>
  <view>
    <image class="banner-image" mode="aspectFill" :src="detail.bannerImage" />

    <view class="info-wrap">
      <view class="top-row">
        <image class="logo-image" mode="aspectFill" :src="detail.logoImage" />
        <view class="title-wrap">
          <text class="title">{{ detail.title }}</text>
          <view class="meta-row">
            <text class="level-tag">{{ detail.levelTag }}</text>
            <text class="meta-text">{{ detail.membersText }} · {{ detail.postsText }}</text>
          </view>
        </view>
      </view>

      <view class="description-wrap" @tap="toggleDescription">
        <text class="description" :class="{ 'description-collapsed': !descriptionExpanded }">{{ detail.description }}</text>
        <text v-if="shouldShowExpandBtn" class="expand-btn">{{ descriptionExpanded ? '收起' : '展开' }}</text>
      </view>
    </view>
  </view>
</template>

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

<style scoped>
.banner-image {
  width: 100%;
  height: 280rpx;
  background: #e5e7eb;
}

.info-wrap {
  background: #ffffff;
  padding: 20rpx 32rpx 24rpx;
}

.top-row {
  display: flex;
  align-items: flex-start;
  gap: 16rpx;
}

.logo-image {
  width: 120rpx;
  height: 120rpx;
  border-radius: 8rpx;
  background: #f3f4f6;
}

.title-wrap {
  flex: 1;
  min-width: 0;
  padding-top: 4rpx;
}

.title {
  display: block;
  color: #111827;
  font-size: 32rpx;
  line-height: 40rpx;
  font-weight: 600;
}

.meta-row {
  margin-top: 8rpx;
  display: flex;
  align-items: center;
  gap: 8rpx;
  flex-wrap: wrap;
}

.level-tag {
  color: #2563eb;
  background: #eff6ff;
  border-radius: 4rpx;
  font-size: 20rpx;
  line-height: 28rpx;
  padding: 0 8rpx;
}

.meta-text {
  color: #6b7280;
  font-size: 24rpx;
  line-height: 32rpx;
}

.description-wrap {
  margin-top: 16rpx;
  position: relative;
}

.description {
  display: block;
  color: #4b5563;
  font-size: 26rpx;
  line-height: 40rpx;
}

.description-collapsed {
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 4;
  overflow: hidden;
  text-overflow: ellipsis;
}

.expand-btn {
  display: inline-block;
  margin-top: 8rpx;
  color: #2563eb;
  font-size: 26rpx;
  line-height: 36rpx;
}

@media (prefers-color-scheme: dark) {
  .banner-image {
    background: #1f2937;
  }

  .info-wrap {
    background: #111827;
  }

  .logo-image {
    background: #1f2937;
  }

  .title {
    color: #f9fafb;
  }

  .level-tag {
    background: rgba(37, 99, 235, 0.2);
  }

  .meta-text {
    color: #9ca3af;
  }

  .description {
    color: #d1d5db;
  }
}
</style>
