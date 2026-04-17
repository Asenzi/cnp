<template>
  <view class="section-wrap">
    <text class="section-title">圈子头像</text>

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

const chooseAvatar = () => {
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
  padding: 0 32rpx;
}

.section-title {
  display: block;
  color: #0f172a;
  font-size: 32rpx;
  line-height: 42rpx;
  font-weight: 700;
  margin-bottom: 14rpx;
}

.avatar-card {
  border-radius: 20rpx;
  background: #ffffff;
  border: 1rpx solid #e2e8f0;
  box-shadow: 0 2rpx 10rpx rgba(15, 23, 42, 0.05);
  padding: 20rpx;
  display: flex;
  align-items: center;
  gap: 18rpx;
}

.avatar-image {
  width: 96rpx;
  height: 96rpx;
  border-radius: 50%;
  border: 2rpx solid #dbe2ea;
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
  line-height: 34rpx;
  font-weight: 600;
}

.avatar-tip {
  color: #64748b;
  font-size: 22rpx;
  line-height: 30rpx;
}

.avatar-btn {
  flex-shrink: 0;
  min-width: 100rpx;
  height: 56rpx;
  border-radius: 999rpx;
  padding: 0 20rpx;
  background: #e8f0ff;
  color: #1d4ed8;
  font-size: 24rpx;
  line-height: 56rpx;
  text-align: center;
  font-weight: 600;
}

@media (prefers-color-scheme: dark) {
  .section-title {
    color: #f8fafc;
  }

  .avatar-card {
    background: #0f172a;
    border-color: #334155;
    box-shadow: none;
  }

  .avatar-image {
    border-color: #334155;
    background: #1e293b;
  }

  .avatar-label {
    color: #f8fafc;
  }

  .avatar-tip {
    color: #94a3b8;
  }

  .avatar-btn {
    background: rgba(37, 99, 235, 0.2);
    color: #93c5fd;
  }
}
</style>
