<template>
  <view class="glyph-wrap" :style="glyphStyle">
    <view v-if="name === 'smile'" class="icon-smile">
      <view class="smile-ring"></view>
      <view class="smile-eye left"></view>
      <view class="smile-eye right"></view>
      <view class="smile-mouth"></view>
    </view>

    <view v-else-if="name === 'plus-circle'" class="icon-plus-circle">
      <view class="circle-ring"></view>
      <view class="plus-h"></view>
      <view class="plus-v"></view>
    </view>

    <view v-else-if="name === 'send'" class="icon-send">
      <view class="send-triangle"></view>
      <view class="send-tail"></view>
    </view>

    <view v-else-if="name === 'card'" class="icon-card">
      <view class="card-frame"></view>
      <view class="card-head"></view>
      <view class="card-line"></view>
    </view>

    <view v-else-if="name === 'image'" class="icon-image">
      <view class="image-frame"></view>
      <view class="image-sun"></view>
      <view class="image-mount"></view>
    </view>

    <view v-else-if="name === 'file'" class="icon-file">
      <view class="file-frame"></view>
      <view class="file-fold"></view>
      <view class="file-line"></view>
    </view>

    <view v-else-if="name === 'location'" class="icon-location">
      <view class="location-pin"></view>
      <view class="location-core"></view>
    </view>
  </view>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  name: {
    type: String,
    default: ''
  },
  size: {
    type: Number,
    default: 20
  },
  color: {
    type: String,
    default: '#64748b'
  }
})

const glyphStyle = computed(() => {
  const safeSize = Math.max(Number(props.size || 20), 12)
  return {
    width: `${safeSize}px`,
    height: `${safeSize}px`,
    color: props.color
  }
})
</script>

<style scoped>
.glyph-wrap {
  position: relative;
  display: inline-block;
  color: #64748b;
  flex-shrink: 0;
}

.glyph-wrap view {
  position: absolute;
  box-sizing: border-box;
}

.icon-smile,
.icon-plus-circle,
.icon-send,
.icon-card,
.icon-image,
.icon-file,
.icon-location {
  inset: 0;
}

.smile-ring {
  left: 8%;
  top: 8%;
  width: 84%;
  height: 84%;
  border: 2px solid currentColor;
  border-radius: 999rpx;
}

.smile-eye {
  top: 34%;
  width: 8%;
  height: 8%;
  border-radius: 999rpx;
  background: currentColor;
}

.smile-eye.left {
  left: 32%;
}

.smile-eye.right {
  right: 32%;
}

.smile-mouth {
  left: 30%;
  top: 56%;
  width: 40%;
  height: 18%;
  border-bottom: 2px solid currentColor;
  border-radius: 0 0 999rpx 999rpx;
}

.circle-ring {
  left: 8%;
  top: 8%;
  width: 84%;
  height: 84%;
  border: 2px solid currentColor;
  border-radius: 999rpx;
}

.plus-h {
  left: 28%;
  top: 48%;
  width: 44%;
  border-top: 2px solid currentColor;
}

.plus-v {
  left: 48%;
  top: 28%;
  height: 44%;
  border-left: 2px solid currentColor;
}

.send-triangle {
  left: 16%;
  top: 18%;
  width: 62%;
  height: 62%;
  border-top: 2px solid currentColor;
  border-right: 2px solid currentColor;
  transform: skew(-15deg) rotate(45deg);
}

.send-tail {
  left: 22%;
  top: 60%;
  width: 30%;
  border-top: 2px solid currentColor;
  transform: rotate(12deg);
}

.card-frame {
  left: 10%;
  top: 16%;
  width: 80%;
  height: 68%;
  border: 2px solid currentColor;
  border-radius: 4px;
}

.card-head {
  left: 24%;
  top: 32%;
  width: 18%;
  height: 18%;
  border: 2px solid currentColor;
  border-radius: 999rpx;
}

.card-line {
  right: 22%;
  top: 36%;
  width: 26%;
  border-top: 2px solid currentColor;
  box-shadow: 0 7px 0 currentColor, 0 14px 0 currentColor;
}

.image-frame {
  left: 10%;
  top: 16%;
  width: 80%;
  height: 68%;
  border: 2px solid currentColor;
  border-radius: 4px;
}

.image-sun {
  right: 20%;
  top: 28%;
  width: 14%;
  height: 14%;
  border-radius: 999rpx;
  background: currentColor;
}

.image-mount {
  left: 20%;
  top: 54%;
  width: 52%;
  height: 24%;
  border-left: 2px solid currentColor;
  border-bottom: 2px solid currentColor;
  transform: skewX(-35deg) rotate(-5deg);
}

.file-frame {
  left: 16%;
  top: 10%;
  width: 64%;
  height: 78%;
  border: 2px solid currentColor;
  border-radius: 4px;
}

.file-fold {
  right: 20%;
  top: 10%;
  width: 18%;
  height: 18%;
  border-top: 2px solid currentColor;
  border-right: 2px solid currentColor;
}

.file-line {
  left: 28%;
  top: 42%;
  width: 34%;
  border-top: 2px solid currentColor;
  box-shadow: 0 7px 0 currentColor, 0 14px 0 currentColor;
}

.location-pin {
  left: 26%;
  top: 10%;
  width: 48%;
  height: 68%;
  border: 2px solid currentColor;
  border-radius: 999rpx 999rpx 999rpx 999rpx;
  transform: rotate(45deg);
}

.location-core {
  left: 42%;
  top: 36%;
  width: 16%;
  height: 16%;
  border-radius: 999rpx;
  background: currentColor;
}
</style>
