<template>
  <view class="cropper-page">
    <view
      class="cropper-content"
      @touchstart="onTouchStart"
      @touchmove.stop.prevent="onTouchMove"
      @touchend="onTouchEnd"
    >
      <view class="image-container">
        <image
          class="bg-image"
          :src="imageSrc"
          mode="aspectFit"
          :style="bgImageStyle"
          @load="onImageLoad"
        />

        <view class="crop-window" :style="cropWindowStyle">
          <image
            class="crop-image"
            :src="imageSrc"
            mode="aspectFit"
            :style="cropImageStyle"
          />
        </view>

        <view class="crop-frame" :style="cropFrameStyle">
          <view class="grid-lines">
            <view class="grid-line grid-h" style="top: 33.33%"></view>
            <view class="grid-line grid-h" style="top: 66.66%"></view>
            <view class="grid-line grid-v" style="left: 33.33%"></view>
            <view class="grid-line grid-v" style="left: 66.66%"></view>
          </view>
          <view class="corner corner-tl"></view>
          <view class="corner corner-tr"></view>
          <view class="corner corner-bl"></view>
          <view class="corner corner-br"></view>
        </view>
      </view>
    </view>

    <view class="cropper-footer">
      <view class="tip-wrapper">
        <text class="tip-text">拖动图片或双指缩放调整</text>
      </view>

      <view class="action-bar">
        <view class="action-btn cancel-btn" hover-class="action-hover" @tap="onCancel">
          <text class="action-text">取消</text>
        </view>
        <view class="action-btn confirm-btn" hover-class="action-hover" @tap="onConfirm">
          <text class="action-text">裁剪</text>
        </view>
      </view>
    </view>

    <canvas canvas-id="cropCanvas" class="crop-canvas"></canvas>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'

const CROP_CANVAS_ID = 'cropCanvas'
const CROP_OUTPUT_SIZE = 800
const DEFAULT_RESULT_EVENT = 'resource-publish-image-cropped'

const imageSrc = ref('')
const cropResultEvent = ref(DEFAULT_RESULT_EVENT)
const cropRatio = ref({
  width: 1,
  height: 1
})
const imageInfo = ref(null)
const minScale = ref(0.5)
const maxScale = ref(4)
const updatePending = ref(false)
const imageTransform = ref({
  scale: 1,
  translateX: 0,
  translateY: 0
})
const touchState = ref({
  startDistance: 0,
  startScale: 1,
  startX: 0,
  startY: 0,
  lastX: 0,
  lastY: 0,
  centerX: 0,
  centerY: 0,
  mode: 'none'
})
const screenInfo = ref({
  width: 375,
  height: 667,
  statusBarHeight: 0
})
const cropContentHeight = computed(() => Math.max(screenInfo.value.height - 160, 1))

const cropBoxDimensions = computed(() => {
  const ratio = cropRatio.value.width / cropRatio.value.height
  const availableHeight = Math.max(screenInfo.value.height - 200, 260)
  const maxWidth = screenInfo.value.width * 0.88
  const maxHeight = availableHeight * 0.72
  let width = maxWidth
  let height = width / ratio

  if (height > maxHeight) {
    height = maxHeight
    width = height * ratio
  }

  return {
    width: Math.max(width, 180),
    height: Math.max(height, 180 / Math.max(ratio, 1))
  }
})

const cropBoxPosition = computed(() => {
  const footerHeight = 160
  const availableHeight = screenInfo.value.height - footerHeight
  return {
    left: (screenInfo.value.width - cropBoxDimensions.value.width) / 2,
    top: (availableHeight - cropBoxDimensions.value.height) / 2
  }
})

const imageStyle = computed(() => {
  if (!imageInfo.value) {
    return {}
  }
  const { scale, translateX, translateY } = imageTransform.value
  return {
    width: `${imageInfo.value.width}px`,
    height: `${imageInfo.value.height}px`,
    transform: `translate(-50%, -50%) translate(${translateX}px, ${translateY}px) scale(${scale})`
  }
})

const bgImageStyle = computed(() => ({
  ...imageStyle.value,
  filter: 'brightness(0.32)'
}))

const cropWindowStyle = computed(() => ({
  left: `${cropBoxPosition.value.left}px`,
  top: `${cropBoxPosition.value.top}px`,
  width: `${cropBoxDimensions.value.width}px`,
  height: `${cropBoxDimensions.value.height}px`
}))

const cropImageStyle = computed(() => {
  if (!imageInfo.value) {
    return {}
  }

  const { scale, translateX, translateY } = imageTransform.value
  const screenCenterX = screenInfo.value.width / 2
  const screenCenterY = cropContentHeight.value / 2
  const cropCenterX = cropBoxPosition.value.left + cropBoxDimensions.value.width / 2
  const cropCenterY = cropBoxPosition.value.top + cropBoxDimensions.value.height / 2
  const imgLeft = screenCenterX - cropCenterX + translateX
  const imgTop = screenCenterY - cropCenterY + translateY

  return {
    width: `${imageInfo.value.width}px`,
    height: `${imageInfo.value.height}px`,
    transform: `translate(-50%, -50%) translate(${imgLeft}px, ${imgTop}px) scale(${scale})`
  }
})

const cropFrameStyle = computed(() => ({
  left: `${cropBoxPosition.value.left}px`,
  top: `${cropBoxPosition.value.top}px`,
  width: `${cropBoxDimensions.value.width}px`,
  height: `${cropBoxDimensions.value.height}px`
}))

const clamp = (value, min, max) => Math.min(Math.max(value, min), max)

const getDistance = (touch1, touch2) => {
  const dx = touch1.clientX - touch2.clientX
  const dy = touch1.clientY - touch2.clientY
  return Math.sqrt(dx * dx + dy * dy)
}

const getImageInfo = (src) => new Promise((resolve, reject) => {
  uni.getImageInfo({
    src,
    success: resolve,
    fail: reject
  })
})

const normalizeTransform = (nextTransform) => {
  if (!imageInfo.value) {
    return nextTransform
  }

  const scale = clamp(Number(nextTransform.scale || minScale.value), minScale.value, maxScale.value)
  const imageWidth = imageInfo.value.width * scale
  const imageHeight = imageInfo.value.height * scale
  const screenCenterX = screenInfo.value.width / 2
  const screenCenterY = cropContentHeight.value / 2
  const cropLeft = cropBoxPosition.value.left
  const cropTop = cropBoxPosition.value.top
  const cropRight = cropLeft + cropBoxDimensions.value.width
  const cropBottom = cropTop + cropBoxDimensions.value.height

  const minTranslateX = cropRight - screenCenterX - imageWidth / 2
  const maxTranslateX = cropLeft - screenCenterX + imageWidth / 2
  const minTranslateY = cropBottom - screenCenterY - imageHeight / 2
  const maxTranslateY = cropTop - screenCenterY + imageHeight / 2

  return {
    scale,
    translateX: minTranslateX <= maxTranslateX
      ? clamp(Number(nextTransform.translateX || 0), minTranslateX, maxTranslateX)
      : (minTranslateX + maxTranslateX) / 2,
    translateY: minTranslateY <= maxTranslateY
      ? clamp(Number(nextTransform.translateY || 0), minTranslateY, maxTranslateY)
      : (minTranslateY + maxTranslateY) / 2
  }
}

const commitTransform = (nextTransform) => {
  imageTransform.value = normalizeTransform(nextTransform)
}

const setupImageInfo = (width, height) => {
  const imageWidth = Math.max(Number(width || 0), 1)
  const imageHeight = Math.max(Number(height || 0), 1)
  const minScaleToFit = Math.max(
    cropBoxDimensions.value.width / imageWidth,
    cropBoxDimensions.value.height / imageHeight
  )

  imageInfo.value = {
    width: imageWidth,
    height: imageHeight
  }
  minScale.value = minScaleToFit
  maxScale.value = Math.max(minScaleToFit * 5, minScaleToFit + 0.5)
  commitTransform({
    scale: minScaleToFit * 1.05,
    translateX: 0,
    translateY: 0
  })
}

const onImageLoad = async (event) => {
  const fallbackWidth = Number(event?.detail?.width || 0)
  const fallbackHeight = Number(event?.detail?.height || 0)
  try {
    const info = await getImageInfo(imageSrc.value)
    setupImageInfo(info.width || fallbackWidth, info.height || fallbackHeight)
  } catch {
    setupImageInfo(fallbackWidth, fallbackHeight)
  }
}

const onTouchStart = (event) => {
  if (event.touches.length === 1) {
    touchState.value.mode = 'drag'
    touchState.value.startX = event.touches[0].clientX
    touchState.value.startY = event.touches[0].clientY
    touchState.value.lastX = imageTransform.value.translateX
    touchState.value.lastY = imageTransform.value.translateY
    return
  }

  if (event.touches.length === 2) {
    const distance = getDistance(event.touches[0], event.touches[1])
    touchState.value.mode = 'scale'
    touchState.value.startDistance = distance
    touchState.value.startScale = imageTransform.value.scale
    touchState.value.centerX = (event.touches[0].clientX + event.touches[1].clientX) / 2
    touchState.value.centerY = (event.touches[0].clientY + event.touches[1].clientY) / 2
    touchState.value.lastX = imageTransform.value.translateX
    touchState.value.lastY = imageTransform.value.translateY
  }
}

const handleTouchMove = (event) => {
  if (event.touches.length === 1 && touchState.value.mode === 'drag') {
    commitTransform({
      ...imageTransform.value,
      translateX: touchState.value.lastX + event.touches[0].clientX - touchState.value.startX,
      translateY: touchState.value.lastY + event.touches[0].clientY - touchState.value.startY
    })
    return
  }

  if (event.touches.length === 2 && touchState.value.mode === 'scale') {
    const distance = getDistance(event.touches[0], event.touches[1])
    const startDistance = Math.max(touchState.value.startDistance, 1)
    const nextScale = clamp(
      touchState.value.startScale * (distance / startDistance),
      minScale.value,
      maxScale.value
    )
    const screenCenterX = screenInfo.value.width / 2
    const screenCenterY = cropContentHeight.value / 2
    const scaleDiff = nextScale / touchState.value.startScale - 1

    commitTransform({
      scale: nextScale,
      translateX: touchState.value.lastX - (touchState.value.centerX - screenCenterX) * scaleDiff,
      translateY: touchState.value.lastY - (touchState.value.centerY - screenCenterY) * scaleDiff
    })
    return
  }

  if (event.touches.length === 1 && touchState.value.mode === 'scale') {
    touchState.value.mode = 'drag'
    touchState.value.startX = event.touches[0].clientX
    touchState.value.startY = event.touches[0].clientY
    touchState.value.lastX = imageTransform.value.translateX
    touchState.value.lastY = imageTransform.value.translateY
  }
}

const onTouchMove = (event) => {
  if (updatePending.value) {
    return
  }

  updatePending.value = true
  const scheduleFrame = typeof requestAnimationFrame === 'undefined'
    ? (callback) => setTimeout(callback, 16)
    : requestAnimationFrame
  scheduleFrame(() => {
    handleTouchMove(event)
    updatePending.value = false
  })
}

const onTouchEnd = (event) => {
  if (event.touches.length === 0) {
    touchState.value.mode = 'none'
    return
  }

  if (event.touches.length === 1 && touchState.value.mode === 'scale') {
    touchState.value.mode = 'drag'
    touchState.value.startX = event.touches[0].clientX
    touchState.value.startY = event.touches[0].clientY
    touchState.value.lastX = imageTransform.value.translateX
    touchState.value.lastY = imageTransform.value.translateY
  }
}

const onCancel = () => {
  uni.$emit(cropResultEvent.value, '')
  uni.navigateBack()
}

const cropImage = (src, x, y, width, height) => new Promise((resolve, reject) => {
  const ctx = uni.createCanvasContext(CROP_CANVAS_ID)
  const sourceX = Math.max(Number(x || 0), 0)
  const sourceY = Math.max(Number(y || 0), 0)
  const sourceWidth = Math.max(Number(width || 1), 1)
  const sourceHeight = Math.max(Number(height || 1), 1)
  const ratio = cropRatio.value.width / cropRatio.value.height
  const outputWidth = ratio >= 1 ? CROP_OUTPUT_SIZE : Math.max(Math.round(CROP_OUTPUT_SIZE * ratio), 1)
  const outputHeight = ratio >= 1 ? Math.max(Math.round(CROP_OUTPUT_SIZE / ratio), 1) : CROP_OUTPUT_SIZE

  ctx.clearRect(0, 0, CROP_OUTPUT_SIZE, CROP_OUTPUT_SIZE)
  ctx.drawImage(
    src,
    sourceX,
    sourceY,
    sourceWidth,
    sourceHeight,
    0,
    0,
    outputWidth,
    outputHeight
  )
  ctx.draw(false, () => {
    uni.canvasToTempFilePath({
      x: 0,
      y: 0,
      width: outputWidth,
      height: outputHeight,
      destWidth: outputWidth,
      destHeight: outputHeight,
      canvasId: CROP_CANVAS_ID,
      fileType: 'jpg',
      quality: 0.9,
      success: (result) => resolve(result.tempFilePath),
      fail: reject
    })
  })
})

const onConfirm = async () => {
  if (!imageInfo.value) {
    uni.showToast({ title: '图片未加载', icon: 'none' })
    return
  }

  uni.showLoading({ title: '处理中...', mask: true })

  try {
    const { scale, translateX, translateY } = normalizeTransform(imageTransform.value)
    const imgWidth = imageInfo.value.width
    const imgHeight = imageInfo.value.height
    const screenCenterX = screenInfo.value.width / 2
    const screenCenterY = cropContentHeight.value / 2
    const cropCenterX = cropBoxPosition.value.left + cropBoxDimensions.value.width / 2
    const cropCenterY = cropBoxPosition.value.top + cropBoxDimensions.value.height / 2
    const cropWidth = cropBoxDimensions.value.width / scale
    const cropHeight = cropBoxDimensions.value.height / scale
    const cropX = clamp(
      ((cropCenterX - (screenCenterX + translateX)) / scale + imgWidth / 2) - cropWidth / 2,
      0,
      Math.max(imgWidth - cropWidth, 0)
    )
    const cropY = clamp(
      ((cropCenterY - (screenCenterY + translateY)) / scale + imgHeight / 2) - cropHeight / 2,
      0,
      Math.max(imgHeight - cropHeight, 0)
    )

    const croppedImage = await cropImage(imageSrc.value, cropX, cropY, cropWidth, cropHeight)
    uni.$emit(cropResultEvent.value, croppedImage)
    uni.hideLoading()
    uni.navigateBack()
  } catch (error) {
    uni.hideLoading()
    console.error('裁切失败:', error)
    uni.showToast({ title: '裁切失败', icon: 'none' })
  }
}

onLoad((options = {}) => {
  imageSrc.value = decodeURIComponent(String(options.src || ''))
  cropResultEvent.value = decodeURIComponent(String(options.event || DEFAULT_RESULT_EVENT)) || DEFAULT_RESULT_EVENT
  cropRatio.value = {
    width: Math.max(Number(options.ratioWidth || 1), 1),
    height: Math.max(Number(options.ratioHeight || 1), 1)
  }

  const systemInfo = uni.getSystemInfoSync()
  screenInfo.value = {
    width: systemInfo.windowWidth,
    height: systemInfo.windowHeight,
    statusBarHeight: systemInfo.statusBarHeight || 0
  }
})
</script>

<style scoped>
.cropper-page {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: #000000;
  display: flex;
  flex-direction: column;
}

.cropper-content {
  flex: 1;
  position: relative;
  overflow: hidden;
}

.image-container {
  width: 100%;
  height: 100%;
  position: relative;
  overflow: hidden;
}

.bg-image,
.crop-image {
  position: absolute;
  left: 50%;
  top: 50%;
  transform-origin: center;
  will-change: transform;
}

.bg-image {
  z-index: 1;
}

.crop-window {
  position: absolute;
  overflow: hidden;
  z-index: 5;
  pointer-events: none;
}

.crop-frame {
  position: absolute;
  z-index: 10;
  border: 3px solid #ffffff;
  box-sizing: border-box;
  box-shadow: 0 0 0 9999px rgba(0, 0, 0, 0.46);
  pointer-events: none;
}

.grid-lines {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  opacity: 0.38;
}

.grid-line {
  position: absolute;
  background: #ffffff;
}

.grid-h {
  left: 0;
  right: 0;
  height: 1px;
}

.grid-v {
  top: 0;
  bottom: 0;
  width: 1px;
}

.corner {
  position: absolute;
  width: 24px;
  height: 24px;
  border: 4px solid #ffffff;
}

.corner-tl {
  top: -4px;
  left: -4px;
  border-right: none;
  border-bottom: none;
}

.corner-tr {
  top: -4px;
  right: -4px;
  border-left: none;
  border-bottom: none;
}

.corner-bl {
  bottom: -4px;
  left: -4px;
  border-right: none;
  border-top: none;
}

.corner-br {
  bottom: -4px;
  right: -4px;
  border-left: none;
  border-top: none;
}

.cropper-footer {
  height: 160px;
  display: flex;
  flex-direction: column;
  background: rgba(0, 0, 0, 0.95);
  padding-bottom: env(safe-area-inset-bottom);
}

.tip-wrapper {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px 0;
}

.tip-text {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.72);
}

.action-bar {
  display: flex;
  gap: 12px;
  padding: 0 20px 20px;
}

.action-btn {
  flex: 1;
  height: 50px;
  border-radius: 25px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.cancel-btn {
  background: rgba(255, 255, 255, 0.12);
}

.confirm-btn {
  background: #07c160;
}

.action-hover {
  opacity: 0.78;
}

.action-text {
  color: #ffffff;
  font-size: 17px;
  font-weight: 600;
}

.crop-canvas {
  position: fixed;
  left: -9999px;
  top: -9999px;
  width: 800px;
  height: 800px;
  pointer-events: none;
}
</style>
