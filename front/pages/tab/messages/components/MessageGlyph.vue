<template>
  <view class="glyph-wrap" :style="glyphStyle">
    <view v-if="name === 'search'" class="icon-search">
      <view class="search-ring"></view>
      <view class="search-tail"></view>
    </view>

    <view v-else-if="name === 'person_add'" class="icon-person-add">
      <view class="person-head"></view>
      <view class="person-body"></view>
      <view class="plus-h"></view>
      <view class="plus-v"></view>
    </view>

    <view v-else-if="name === 'notifications'" class="icon-bell">
      <view class="bell-head"></view>
      <view class="bell-clapper"></view>
      <view class="bell-base"></view>
    </view>

    <view v-else-if="name === 'chevron_right'" class="icon-chevron"></view>
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
    default: '#94a3b8'
  }
})

const glyphStyle = computed(() => ({
  width: `${Math.max(Number(props.size || 20), 10)}px`,
  height: `${Math.max(Number(props.size || 20), 10)}px`,
  color: props.color
}))
</script>

<style scoped>
.glyph-wrap {
  position: relative;
  display: inline-block;
  color: #94a3b8;
  flex-shrink: 0;
}

.glyph-wrap view {
  position: absolute;
  box-sizing: border-box;
}

.icon-search,
.icon-person-add,
.icon-bell {
  inset: 0;
}

.search-ring {
  left: 10%;
  top: 10%;
  width: 64%;
  height: 64%;
  border: 2px solid currentColor;
  border-radius: 999rpx;
}

.search-tail {
  right: 4%;
  bottom: 8%;
  width: 34%;
  border-top: 2px solid currentColor;
  transform: rotate(42deg);
  transform-origin: right center;
}

.person-head {
  left: 6%;
  top: 6%;
  width: 36%;
  height: 36%;
  border: 2px solid currentColor;
  border-radius: 999rpx;
}

.person-body {
  left: 2%;
  bottom: 8%;
  width: 48%;
  height: 30%;
  border: 2px solid currentColor;
  border-bottom: 0;
  border-radius: 999rpx 999rpx 0 0;
}

.plus-h {
  right: 4%;
  top: 48%;
  width: 36%;
  border-top: 2px solid currentColor;
}

.plus-v {
  right: 20%;
  top: 32%;
  height: 34%;
  border-left: 2px solid currentColor;
}

.bell-head {
  left: 14%;
  top: 8%;
  width: 72%;
  height: 68%;
  border: 2px solid currentColor;
  border-bottom: 0;
  border-radius: 999rpx 999rpx 10rpx 10rpx;
}

.bell-clapper {
  left: 42%;
  bottom: 18%;
  width: 16%;
  height: 16%;
  border-radius: 999rpx;
  background: currentColor;
}

.bell-base {
  left: 24%;
  bottom: 8%;
  width: 52%;
  border-top: 2px solid currentColor;
}

.icon-chevron {
  left: 34%;
  top: 24%;
  width: 38%;
  height: 38%;
  border-right: 2px solid currentColor;
  border-top: 2px solid currentColor;
  transform: rotate(45deg);
}
</style>
