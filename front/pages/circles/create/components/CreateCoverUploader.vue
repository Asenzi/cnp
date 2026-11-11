<template>
  <view class="section-wrap">
    <text class="section-title">{{ title }}</text>

    <view class="cover-card" :style="cardStyle" @tap="chooseCover">
      <image class="cover-image" mode="aspectFill" :src="modelValue || defaultCoverImage" />
      <view class="cover-mask">
        <image class="camera-icon" mode="aspectFit" src="https://cos.cnptec.site/static/me-icons/camera-white.png" />
        <text class="cover-tip">{{ tip }}</text>
        <text v-if="subtip" class="cover-subtip">{{ subtip }}</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed } from 'vue'
import { defaultCoverImage } from '../modules/create-circle-form'

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  title: {
    type: String,
    default: '圈子封面'
  },
  tip: {
    type: String,
    default: '点击更换封面图'
  },
  subtip: {
    type: String,
    default: ''
  },
  ratioWidth: {
    type: Number,
    default: 2
  },
  ratioHeight: {
    type: Number,
    default: 1
  },
  cropEvent: {
    type: String,
    default: 'circle-cover-image-cropped'
  }
})

const emit = defineEmits(['update:modelValue'])
const cardStyle = computed(() => {
  if (Number(props.ratioWidth) === 4 && Number(props.ratioHeight) === 3) {
    return { height: '515rpx' }
  }
  return {}
})

const chooseCover = () => {
  uni.chooseImage({
    count: 1,
    sizeType: ['compressed'],
    sourceType: ['album', 'camera'],
    success: (res) => {
      const tempPath = res?.tempFilePaths?.[0]
      if (tempPath) {
        uni.$once(props.cropEvent, onCropConfirm)
        uni.navigateTo({
          url: `/pages/cropper/index?src=${encodeURIComponent(tempPath)}&event=${encodeURIComponent(props.cropEvent)}&ratioWidth=${props.ratioWidth}&ratioHeight=${props.ratioHeight}`,
          fail: () => {
            uni.$off(props.cropEvent, onCropConfirm)
            uni.showToast({ title: '打开图片裁切失败', icon: 'none' })
          }
        })
      }
    }
  })
}

const onCropConfirm = (croppedPath) => {
  if (croppedPath) {
    emit('update:modelValue', croppedPath)
  }
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
  /* border: 2rpx dashed #cbd5e1; */
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

.cover-subtip {
  margin-top: 6rpx;
  color: rgba(255, 255, 255, 0.82);
  font-size: 22rpx;
  line-height: 1.3;
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
