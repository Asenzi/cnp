<template>
  <view class="post-card">
    <view class="post-head">
      <text class="post-type-tag" :class="resolvedTypeKey === 'supply' ? 'post-type-supply' : 'post-type-demand'">
        {{ resolvedType }}
      </text>
      <text class="post-time">{{ resolvedTimeText }}</text>
    </view>

    <text class="post-title">{{ resolvedTitle }}</text>
    <text class="post-desc">{{ resolvedDescription }}</text>

    <view class="post-foot">
      <view class="author-row">
        <image class="author-avatar" mode="aspectFill" :src="resolvedAuthorAvatar" />
        <text class="author-name">{{ resolvedAuthorName }}</text>
      </view>

      <view class="detail-link" hover-class="detail-link-active" @tap="emit('detail', post)">
        <text class="detail-link-text">查看详情</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  post: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['detail'])

const resolvedType = computed(() => {
  const mode = String(props.post?.mode || '').trim().toLowerCase()
  if (props.post?.type) {
    return props.post.type
  }
  if (mode === 'resource') {
    return '供应'
  }
  if (mode === 'venue') {
    return '活动'
  }
  return '需求'
})

const resolvedTypeKey = computed(() => {
  const mode = String(props.post?.mode || '').trim().toLowerCase()
  if (props.post?.typeKey) {
    return props.post.typeKey
  }
  return mode === 'resource' ? 'supply' : 'demand'
})

const resolvedTimeText = computed(() => String(props.post?.time_text || props.post?.timeText || '').trim())
const resolvedTitle = computed(() => String(props.post?.title || '').trim())
const resolvedDescription = computed(() => String(props.post?.description || '').trim())
const resolvedAuthorAvatar = computed(() => {
  return String(props.post?.author?.avatar_url || props.post?.authorAvatar || '').trim() || '/static/logo.png'
})
const resolvedAuthorName = computed(() => {
  const nickname = String(props.post?.author?.nickname || '').trim()
  const company = String(props.post?.author?.company_name || '').trim()
  const jobTitle = String(props.post?.author?.job_title || '').trim()
  if (props.post?.authorName) {
    return String(props.post.authorName || '').trim()
  }
  return [nickname, company || jobTitle].filter(Boolean).join(' · ') || nickname || '匿名用户'
})
</script>

<style scoped>
.post-card {
  background: #ffffff;
  border-radius: 16rpx;
  border: 1rpx solid #f1f5f9;
  box-shadow: 0 2rpx 8rpx rgba(15, 23, 42, 0.05);
  padding: 18rpx;
}

.post-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.post-type-tag {
  border-radius: 6rpx;
  padding: 3rpx 10rpx;
  font-size: 16rpx;
  line-height: 22rpx;
  font-weight: 700;
}

.post-type-demand {
  color: #ea580c;
  background: #ffedd5;
}

.post-type-supply {
  color: #16a34a;
  background: #dcfce7;
}

.post-time {
  color: #94a3b8;
  font-size: 18rpx;
  line-height: 26rpx;
}

.post-title {
  display: block;
  margin-top: 10rpx;
  color: #0f172a;
  font-size: 28rpx;
  line-height: 38rpx;
  font-weight: 700;
}

.post-desc {
  display: block;
  margin-top: 8rpx;
  color: #64748b;
  font-size: 22rpx;
  line-height: 32rpx;
}

.post-foot {
  margin-top: 14rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12rpx;
}

.author-row {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 8rpx;
}

.author-avatar {
  width: 44rpx;
  height: 44rpx;
  border-radius: 999rpx;
  background: #e2e8f0;
  flex-shrink: 0;
}

.author-name {
  max-width: 420rpx;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: #64748b;
  font-size: 20rpx;
  line-height: 28rpx;
}

.detail-link {
  padding: 4rpx 0;
}

.detail-link-active {
  opacity: 0.76;
}

.detail-link-text {
  color: #1a57db;
  font-size: 20rpx;
  line-height: 28rpx;
  font-weight: 700;
}

@media (prefers-color-scheme: dark) {
  .post-card {
    background: #0f172a;
    border-color: #1e293b;
    box-shadow: none;
  }

  .post-type-demand {
    color: #fdba74;
    background: rgba(234, 88, 12, 0.18);
  }

  .post-type-supply {
    color: #86efac;
    background: rgba(22, 163, 74, 0.18);
  }

  .post-title {
    color: #f8fafc;
  }

  .post-desc,
  .author-name,
  .post-time {
    color: #94a3b8;
  }
}
</style>
