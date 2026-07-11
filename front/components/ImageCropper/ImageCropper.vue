<template>
  <view v-if="visible" class="cropper-wrapper">
    <view class="cropper-mask" @tap="onCancel"></view>
    <view class="cropper-container">
      <view class="cropper-header">
        <text class="header-title">裁剪图片</text>
        <text class="header-subtitle">拖动调整裁剪区域为正方形</text>
      </view>

      <view class="cropper-content">
        <view class="image-wrapper" :style="{ width: containerSize + 'px', height: containerSize + 'px' }">
          <image
            class="preview-image"
            :src="src"
            mode="aspectFit"
            :style="imageStyle"
          />

          <view
            class="crop-box"
            :style="cropBoxStyle"
            @touchstart="onTouchStart"
            @touchmove.stop.prevent="onTouchMove"
            @touchend="onTouchEnd"
          >
            <view class="crop-border"></view>
            <view class="crop-corner corner-tl"></view>
            <view class="crop-corner corner-tr"></view>
            <view class="crop-corner corner-bl"></view>
            <view class="crop-corner corner-br"></view>
          </view>
        </view>
      </view>

      <view class="cropper-actions">
        <button class="action-btn cancel-btn" hover-class="action-btn-hover" @tap="onCancel">取消</button>
        <button class="action-btn confirm-btn" hover-class="action-btn-hover" @tap="onConfirm">确定</button>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  src: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['cancel', 'confirm'])

const containerSize = ref(350)
const imageInfo = ref(null)
const cropBox = ref({
  left: 25,
  top: 25,
  size: 300
})
const touchStart = ref(null)
const imageStyle = ref({})

watch(() => props.visible, (val) => {
  if (val && props.src) {
    nextTick(() => {
      loadImage()
    })
  }
})

const loadImage = async () => {
  try {
    const info = await new Promise((resolve, reject) => {
      uni.getImageInfo({
        src: props.src,
        success: resolve,
        fail: reject
      })
    })

    imageInfo.value = info

    // 计算图片显示尺寸
    const scale = Math.min(containerSize.value / info.width, containerSize.value / info.height)
    const displayWidth = info.width * scale
    const displayHeight = info.height * scale

    imageStyle.value = {
      width: displayWidth + 'px',
      height: displayHeight + 'px',
      marginLeft: ((containerSize.value - displayWidth) / 2) + 'px',
      marginTop: ((containerSize.value - displayHeight) / 2) + 'px'
    }

    // 计算初始裁切框（居中，正方形）
    const boxSize = Math.min(displayWidth, displayHeight) * 0.8
    cropBox.value = {
      left: (containerSize.value - boxSize) / 2,
      top: (containerSize.value - boxSize) / 2,
      size: boxSize
    }
  } catch (err) {
    console.error('加载图片失败:', err)
    uni.showToast({ title: '加载图片失败', icon: 'none' })
  }
}

const cropBoxStyle = computed(() => {
  return {
    left: cropBox.value.left + 'px',
    top: cropBox.value.top + 'px',
    width: cropBox.value.size + 'px',
    height: cropBox.value.size + 'px'
  }
})

const onTouchStart = (e) => {
  if (e.touches && e.touches[0]) {
    touchStart.value = {
      x: e.touches[0].clientX,
      y: e.touches[0].clientY,
      boxLeft: cropBox.value.left,
      boxTop: cropBox.value.top
    }
  }
}

const onTouchMove = (e) => {
  if (!touchStart.value || !e.touches || !e.touches[0]) return

  const deltaX = e.touches[0].clientX - touchStart.value.x
  const deltaY = e.touches[0].clientY - touchStart.value.y

  let newLeft = touchStart.value.boxLeft + deltaX
  let newTop = touchStart.value.boxTop + deltaY

  // 限制裁切框不超出容器
  newLeft = Math.max(0, Math.min(newLeft, containerSize.value - cropBox.value.size))
  newTop = Math.max(0, Math.min(newTop, containerSize.value - cropBox.value.size))

  cropBox.value.left = newLeft
  cropBox.value.top = newTop
}

const onTouchEnd = () => {
  touchStart.value = null
}

const onCancel = () => {
  emit('cancel')
}

const onConfirm = async () => {
  if (!imageInfo.value) {
    uni.showToast({ title: '图片信息缺失', icon: 'none' })
    return
  }

  try {
    // 计算图片实际显示尺寸
    const scale = Math.min(containerSize.value / imageInfo.value.width, containerSize.value / imageInfo.value.height)
    const displayWidth = imageInfo.value.width * scale
    const displayHeight = imageInfo.value.height * scale
    const imageOffsetX = (containerSize.value - displayWidth) / 2
    const imageOffsetY = (containerSize.value - displayHeight) / 2

    // 计算裁切区域相对于图片的位置
    const cropLeft = (cropBox.value.left - imageOffsetX) / scale
    const cropTop = (cropBox.value.top - imageOffsetY) / scale
    const cropSize = cropBox.value.size / scale

    // 使用 uni.compressImage 进行裁切（支持裁切参数）
    const result = await new Promise((resolve, reject) => {
      uni.compressImage({
        src: props.src,
        quality: 90,
        width: 800,
        height: 800,
        crop: {
          x: Math.max(0, cropLeft),
          y: Math.max(0, cropTop),
          width: cropSize,
          height: cropSize
        },
        success: resolve,
        fail: reject
      })
    })

    emit('confirm', result.tempFilePath)
  } catch (err) {
    console.error('裁切失败:', err)
    // 如果裁切失败，尝试直接返回原图
    uni.showToast({ title: '将使用原图', icon: 'none' })
    emit('confirm', props.src)
  }
}
</script>

<style scoped>
.cropper-wrapper {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
}

.cropper-mask {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
}

.cropper-container {
  position: relative;
  width: 90%;
  max-width: 400px;
  background: #ffffff;
  border-radius: 16px;
  overflow: hidden;
}

.cropper-header {
  padding: 20px;
  text-align: center;
  border-bottom: 1px solid #f0f0f0;
}

.header-title {
  display: block;
  font-size: 18px;
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 4px;
}

.header-subtitle {
  display: block;
  font-size: 13px;
  color: #8e8e93;
}

.cropper-content {
  padding: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f5f5;
}

.image-wrapper {
  position: relative;
  background: #000000;
  overflow: hidden;
}

.preview-image {
  display: block;
  position: relative;
}

.crop-box {
  position: absolute;
  border: 2px solid #ffffff;
  box-shadow: 0 0 0 9999px rgba(0, 0, 0, 0.5);
  cursor: move;
}

.crop-border {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  border: 1px dashed rgba(255, 255, 255, 0.5);
}

.crop-corner {
  position: absolute;
  width: 20px;
  height: 20px;
  border: 3px solid #ffffff;
}

.corner-tl {
  top: -3px;
  left: -3px;
  border-right: none;
  border-bottom: none;
}

.corner-tr {
  top: -3px;
  right: -3px;
  border-left: none;
  border-bottom: none;
}

.corner-bl {
  bottom: -3px;
  left: -3px;
  border-right: none;
  border-top: none;
}

.corner-br {
  bottom: -3px;
  right: -3px;
  border-left: none;
  border-top: none;
}

.cropper-actions {
  display: flex;
  border-top: 1px solid #f0f0f0;
}

.action-btn {
  flex: 1;
  height: 52px;
  line-height: 52px;
  font-size: 16px;
  border: none;
  background: #ffffff;
  border-radius: 0;
}

.action-btn-hover {
  background: #f5f5f5;
}

.cancel-btn {
  color: #8e8e93;
  border-right: 1px solid #f0f0f0;
}

.confirm-btn {
  color: #007aff;
  font-weight: 600;
}
</style>