<template>
  <view class="symbol-wrap" :style="symbolStyle">
    <view v-if="name === 'member_badge'" class="icon-member-badge">
      <view class="member-core"></view>
      <view class="member-point member-point-left"></view>
      <view class="member-point member-point-right"></view>
    </view>

    <view v-else-if="name === 'verified'" class="icon-verified">
      <view class="verified-circle"></view>
      <view class="verified-check-a"></view>
      <view class="verified-check-b"></view>
    </view>

    <view v-else-if="name === 'trending_up'" class="icon-trending">
      <view class="trend-line"></view>
      <view class="trend-arrow-a"></view>
      <view class="trend-arrow-b"></view>
    </view>

    <view v-else-if="name === 'thumb_up'" class="icon-thumb">
      <view class="thumb-palm"></view>
      <view class="thumb-finger"></view>
      <view class="thumb-head"></view>
    </view>

    <view v-else-if="name === 'chat_bubble'" class="icon-chat">
      <view class="chat-body"></view>
      <view class="chat-tail"></view>
    </view>

    <view v-else-if="name === 'visibility'" class="icon-eye">
      <view class="eye-outline"></view>
      <view class="eye-dot"></view>
    </view>

    <view v-else-if="name === 'mail'" class="icon-mail">
      <view class="mail-body"></view>
      <view class="mail-flap-a"></view>
      <view class="mail-flap-b"></view>
    </view>

    <view v-else-if="name === 'person_add'" class="icon-person-add">
      <view class="person-head"></view>
      <view class="person-body"></view>
      <view class="plus-h"></view>
      <view class="plus-v"></view>
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
    default: 28
  },
  color: {
    type: String,
    default: '#1a57db'
  }
})

const symbolStyle = computed(() => ({
  width: `${Math.max(Number(props.size || 28), 12)}px`,
  height: `${Math.max(Number(props.size || 28), 12)}px`,
  color: props.color
}))
</script>

<style scoped>
.symbol-wrap {
  position: relative;
  display: inline-block;
  color: #1a57db;
  flex-shrink: 0;
}

.symbol-wrap view {
  position: absolute;
  box-sizing: border-box;
}

.icon-member-badge,
.icon-verified,
.icon-trending,
.icon-thumb,
.icon-chat,
.icon-eye,
.icon-mail,
.icon-person-add {
  inset: 0;
  width: 100%;
  height: 100%;
}

.member-core {
  left: 24%;
  top: 18%;
  width: 52%;
  height: 64%;
  border: 2px solid currentColor;
  border-radius: 10rpx 10rpx 14rpx 14rpx;
  background: rgba(255, 255, 255, 0.12);
}

.member-point {
  top: 10%;
  width: 16%;
  height: 16%;
  border-radius: 999rpx;
  background: currentColor;
}

.member-point-left {
  left: 18%;
}

.member-point-right {
  right: 18%;
}

.verified-circle {
  left: 8%;
  top: 8%;
  width: 84%;
  height: 84%;
  border-radius: 999rpx;
  background: currentColor;
}

.verified-check-a {
  left: 28%;
  top: 52%;
  width: 18%;
  border-top: 2px solid #ffffff;
  transform: rotate(45deg);
}

.verified-check-b {
  left: 42%;
  top: 46%;
  width: 32%;
  border-top: 2px solid #ffffff;
  transform: rotate(-45deg);
}

.trend-line {
  left: 14%;
  top: 58%;
  width: 62%;
  border-top: 2px solid currentColor;
  transform: rotate(-28deg);
}

.trend-arrow-a {
  right: 10%;
  top: 24%;
  width: 20%;
  border-top: 2px solid currentColor;
  transform: rotate(-35deg);
}

.trend-arrow-b {
  right: 10%;
  top: 24%;
  width: 20%;
  border-top: 2px solid currentColor;
  transform: rotate(35deg);
}

.thumb-palm {
  left: 28%;
  top: 34%;
  width: 44%;
  height: 44%;
  border: 2px solid currentColor;
  border-radius: 6rpx;
}

.thumb-finger {
  left: 18%;
  top: 40%;
  width: 14%;
  height: 32%;
  border: 2px solid currentColor;
  border-right: 0;
  border-radius: 8rpx 0 0 8rpx;
}

.thumb-head {
  left: 40%;
  top: 20%;
  width: 20%;
  height: 16%;
  border: 2px solid currentColor;
  border-bottom: 0;
  border-radius: 8rpx 8rpx 0 0;
}

.chat-body {
  left: 10%;
  top: 16%;
  width: 80%;
  height: 62%;
  border: 2px solid currentColor;
  border-radius: 10rpx;
}

.chat-tail {
  left: 26%;
  bottom: 6%;
  width: 18%;
  height: 18%;
  border-left: 2px solid currentColor;
  border-bottom: 2px solid currentColor;
  transform: skewX(-22deg) rotate(-18deg);
}

.eye-outline {
  left: 8%;
  top: 24%;
  width: 84%;
  height: 52%;
  border: 2px solid currentColor;
  border-radius: 999rpx;
}

.eye-dot {
  left: 42%;
  top: 40%;
  width: 18%;
  height: 18%;
  border-radius: 999rpx;
  background: currentColor;
}

.mail-body {
  left: 10%;
  top: 20%;
  width: 80%;
  height: 62%;
  border: 2px solid currentColor;
  border-radius: 6rpx;
}

.mail-flap-a {
  left: 12%;
  top: 22%;
  width: 40%;
  border-top: 2px solid currentColor;
  transform: rotate(24deg);
  transform-origin: left center;
}

.mail-flap-b {
  right: 12%;
  top: 22%;
  width: 40%;
  border-top: 2px solid currentColor;
  transform: rotate(-24deg);
  transform-origin: right center;
}

.person-head {
  left: 10%;
  top: 10%;
  width: 32%;
  height: 32%;
  border: 2px solid currentColor;
  border-radius: 999rpx;
}

.person-body {
  left: 4%;
  bottom: 10%;
  width: 44%;
  height: 30%;
  border: 2px solid currentColor;
  border-bottom: 0;
  border-radius: 999rpx 999rpx 0 0;
}

.plus-h {
  right: 6%;
  top: 42%;
  width: 30%;
  border-top: 2px solid currentColor;
}

.plus-v {
  right: 20%;
  top: 28%;
  height: 28%;
  border-left: 2px solid currentColor;
}
</style>
