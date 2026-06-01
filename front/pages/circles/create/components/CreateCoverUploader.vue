<template>
  <view class="section-wrap">
    <text class="section-title">圈子封面</text>

    <view class="cover-card" @tap="chooseCover">
      <image class="cover-image" mode="aspectFill" :src="modelValue || defaultCoverImage" />
      <view class="cover-mask">
        <image class="camera-icon" mode="aspectFit" src="/static/me-icons/camera-white.png" />
        <text class="cover-tip">点击更换封面图</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { defaultCoverImage } from '../modules/create-circle-form'

defineProps({
  modelValue: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['update:modelValue'])

const chooseCover = () => {
  uni.chooseImage({
    count: 1,
    sizeType: ['compressed'],
    sourceType: ['album', 'camera'],
    success: (res) => {
      const tempPath = res?.tempFilePaths?.[0]
      if (tempPath) {
        emit('update:modelValue', tempPath)
      }
    }
  })
}
</script>

<style scoped>
.section-wrap {
  padding: 24rpx 32rpx;
  background: #ffffff;
}

.section-title {
  display: block;
  color: #0f172a;
  font-size: 28rpx;
  line-height: 1.3;
  font-weight: 600;
  margin-bottom: 16rpx;
}

.cover-card {
  position: relative;
  width: 100%;
  height: 330rpx;
  border-radius: 16rpx;
  overflow: hidden;
  border: 2rpx dashed #cbd5e1;
  background: #e2e8f0;
}

.cover-image {
  width: 100%;
  height: 100%;
}

.cover-mask {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.camera-icon {
  width: 64rpx;
  height: 64rpx;
}

.cover-tip {
  margin-top: 12rpx;
  color: #ffffff;
  font-size: 26rpx;
  line-height: 1.3;
  font-weight: 500;
}

@media (prefers-color-scheme: dark) {
  .section-wrap {
    background: #0f172a;
  }

  .section-title {
    color: #f1f5f9;
  }

  .cover-card {
    border-color: #334155;
    background: #1e293b;
  }
}
</style>
