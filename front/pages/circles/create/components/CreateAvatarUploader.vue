<template>
  <view class="section-wrap">
    <view class="avatar-card" @tap="chooseAvatar">
      <image class="avatar-image" mode="aspectFill" :src="modelValue || defaultCircleAvatar" />
      <view class="avatar-content">
        <text class="avatar-label">点击上传圈子头像</text>
        <text class="avatar-tip">用于圈子列表与详情页头像展示</text>
      </view>
      <view class="avatar-btn">更换</view>
    </view>
  </view>
</template>

<script setup>
import { defaultCircleAvatar } from '../modules/create-circle-form'

defineProps({
  modelValue: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['update:modelValue'])
const CROP_RESULT_EVENT = 'circle-avatar-image-cropped'

const chooseAvatar = () => {
  uni.chooseImage({
    count: 1,
    sizeType: ['compressed'],
    sourceType: ['album', 'camera'],
    success: (res) => {
      const tempPath = res?.tempFilePaths?.[0]
      if (tempPath) {
        uni.$once(CROP_RESULT_EVENT, onCropConfirm)
        uni.navigateTo({
          url: `/pages/cropper/index?src=${encodeURIComponent(tempPath)}&event=${encodeURIComponent(CROP_RESULT_EVENT)}&ratioWidth=1&ratioHeight=1`,
          fail: () => {
            uni.$off(CROP_RESULT_EVENT, onCropConfirm)
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
  padding: 10rpx 32rpx;
  background: #ffffff;
}

.avatar-card {
  border-radius: 12rpx;
  /* background: #f8fafc; */
  /* border: 1rpx solid rgba(15, 23, 42, 0.08); */
  padding: 16rpx;
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.avatar-image {
  width: 88rpx;
  height: 88rpx;
  border-radius: 50%;
  /* border: 2rpx solid #dbe2ea; */
  background: #f1f5f9;
  flex-shrink: 0;
}

.avatar-content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4rpx;
}

.avatar-label {
  color: #0f172a;
  font-size: 26rpx;
  line-height: 1.3;
  font-weight: 500;
}

.avatar-tip {
  color: #64748b;
  font-size: 22rpx;
  line-height: 1.3;
}

.avatar-btn {
  flex-shrink: 0;
  min-width: 92rpx;
  height: 52rpx;
  border-radius: 20rpx;
  padding: 0 18rpx;
  background: rgba(37, 99, 235, 0.08);
  color: #2563eb;
  font-size: 24rpx;
  line-height: 52rpx;
  text-align: center;
  font-weight: 600;
}

@media (prefers-color-scheme: dark) {
  .section-wrap {
    background: #0f172a;
  }

  .avatar-card {
    background: #1e293b;
    border-color: rgba(255, 255, 255, 0.08);
  }

  .avatar-image {
    border-color: #334155;
    background: #1e293b;
  }

  .avatar-label {
    color: #f1f5f9;
  }

  .avatar-tip {
    color: #94a3b8;
  }

  .avatar-btn {
    background: rgba(59, 130, 246, 0.15);
    color: #60a5fa;
  }
}
</style>
