<template>
  <view class="notice-wrap">
    <view class="notice-head">
      <text class="notice-title">圈子公告</text>
      <text class="more-link" @tap="toggleNotice">{{ noticeExpanded ? '收起' : '查看详情' }}</text>
    </view>
    <text class="notice-text" :class="{ 'notice-collapsed': !noticeExpanded }">{{ notice }}</text>
  </view>
</template>

<script setup>
import { ref } from 'vue'

defineProps({
  notice: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['more'])

const noticeExpanded = ref(false)

const toggleNotice = () => {
  noticeExpanded.value = !noticeExpanded.value
  if (noticeExpanded.value) {
    emit('more')
  }
}
</script>

<style scoped>
.notice-wrap {
  margin: 0 32rpx;
  padding: 20rpx 16rpx;
  background: #f0f9ff;
  border-radius: 8rpx;
}

.notice-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12rpx;
}

.notice-title {
  color: #111827;
  font-size: 28rpx;
  line-height: 36rpx;
  font-weight: 600;
}

.more-link {
  color: #2563eb;
  font-size: 24rpx;
  line-height: 32rpx;
}

.notice-text {
  display: block;
  color: #4b5563;
  font-size: 26rpx;
  line-height: 40rpx;
}

.notice-collapsed {
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 4;
  overflow: hidden;
  text-overflow: ellipsis;
}

@media (prefers-color-scheme: dark) {
  .notice-wrap {
    background: rgba(37, 99, 235, 0.1);
  }

  .notice-title {
    color: #f9fafb;
  }

  .notice-text {
    color: #d1d5db;
  }
}
</style>
