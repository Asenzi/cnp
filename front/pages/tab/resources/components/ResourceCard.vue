<template>
  <view class="card" hover-class="card-active" @tap="$emit('detail', post)">
    <view class="author-row">
      <image class="avatar" :src="authorAvatar" mode="aspectFill" />
      <view class="author-main">
        <view class="name-row">
          <text class="name">{{ authorName }}</text>
          <text v-if="industryLabel" class="industry-tag" :class="industryTagClass">{{ industryLabel }}</text>
        </view>
        <text class="meta">{{ authorRole }} · {{ post.time_text || '\u521a\u521a' }}</text>
      </view>
    </view>

    <text class="title">{{ post.title || '\u672a\u547d\u540d\u8d44\u6e90' }}</text>
    <text class="desc">{{ post.description || '' }}</text>

    <view
      v-if="imageList.length"
      class="image-wrap"
      :class="imageList.length > 1 ? 'image-grid' : 'image-single'"
    >
      <image
        v-for="(image, index) in imageList"
        :key="`${post.post_code || post.id}-${index}`"
        class="cover-image"
        mode="aspectFill"
        :src="image"
        @tap.stop="onPreviewImage(index)"
      />
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

defineEmits(['detail'])

const author = computed(() => (props.post?.author && typeof props.post.author === 'object' ? props.post.author : {}))
const authorAvatar = computed(() => String(author.value.avatar_url || '/static/logo.png').trim() || '/static/logo.png')
const authorName = computed(() => String(author.value.nickname || '\u672a\u547d\u540d\u7528\u6237').trim() || '\u672a\u547d\u540d\u7528\u6237')
const authorRole = computed(() => String(author.value.role || '\u5546\u52a1\u4eba\u58eb').trim() || '\u5546\u52a1\u4eba\u58eb')
const industryLabel = computed(() => String(props.post?.industry_label || '').trim())
const imageList = computed(() => {
  return Array.isArray(props.post?.images)
    ? props.post.images.map((item) => String(item || '').trim()).filter(Boolean)
    : []
})

const industryTagClass = computed(() => {
  const industry = industryLabel.value
  if (industry.includes('\u4e92\u8054\u7f51') || industry.includes('\u8f6f\u4ef6')) return 'tag-blue'
  if (industry.includes('\u4f20\u5a92') || industry.includes('\u5e02\u573a')) return 'tag-orange'
  if (industry.includes('\u5236\u9020') || industry.includes('\u5de5\u4e1a')) return 'tag-green'
  return 'tag-gray'
})

const onPreviewImage = (index) => {
  if (!imageList.value.length) {
    return
  }
  uni.previewImage({
    urls: imageList.value,
    current: imageList.value[Math.max(Number(index || 0), 0)] || imageList.value[0]
  })
}
</script>

<style scoped>
.card {
  background: #ffffff;
  border: 1rpx solid #f1f5f9;
  border-radius: 22rpx;
  box-shadow: 0 2rpx 8rpx rgba(15, 23, 42, 0.05);
  padding: 22rpx;
}

.card-active {
  background: #f8fafc;
}

.author-row {
  display: flex;
  align-items: center;
  gap: 12rpx;
  margin-bottom: 12rpx;
}

.avatar {
  width: 80rpx;
  height: 80rpx;
  border-radius: 999rpx;
  border: 1rpx solid #f1f5f9;
  background: #dbeafe;
  flex-shrink: 0;
}

.author-main {
  flex: 1;
  min-width: 0;
}

.name-row {
  display: flex;
  align-items: center;
  gap: 8rpx;
}

.name {
  color: #0f172a;
  font-size: 30rpx;
  line-height: 38rpx;
  font-weight: 700;
}

.industry-tag {
  border-radius: 6rpx;
  padding: 2rpx 9rpx;
  font-size: 20rpx;
  line-height: 24rpx;
  font-weight: 500;
}

.tag-blue {
  color: #1a57db;
  background: rgba(26, 87, 219, 0.1);
}

.tag-orange {
  color: #ea580c;
  background: rgba(251, 146, 60, 0.18);
}

.tag-green {
  color: #15803d;
  background: rgba(74, 222, 128, 0.18);
}

.tag-gray {
  color: #475569;
  background: #e2e8f0;
}

.meta {
  margin-top: 2rpx;
  display: block;
  color: #6b7280;
  font-size: 24rpx;
  line-height: 32rpx;
}

.title {
  display: block;
  color: #111827;
  font-size: 32rpx;
  line-height: 42rpx;
  font-weight: 700;
  margin-bottom: 8rpx;
}

.desc {
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  overflow: hidden;
  color: #475569;
  font-size: 28rpx;
  line-height: 40rpx;
}

.image-wrap {
  margin-top: 16rpx;
}

.image-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8rpx;
}

.cover-image {
  width: 100%;
  border-radius: 12rpx;
  background: #e2e8f0;
  aspect-ratio: 16 / 9;
}

@media (prefers-color-scheme: dark) {
  .card {
    background: #0f172a;
    border-color: #1f2937;
    box-shadow: none;
  }

  .avatar {
    border-color: #334155;
    background: #1e3a8a;
  }

  .name,
  .title {
    color: #f8fafc;
  }

  .meta {
    color: #94a3b8;
  }

  .desc {
    color: #cbd5e1;
  }
}
</style>
