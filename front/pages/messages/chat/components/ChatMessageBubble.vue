<template>
  <view class="bubble-row" :class="message.isSelf ? 'bubble-row-self' : ''">
    <image
      v-if="!message.isSelf"
      class="avatar"
      :src="peerAvatar || '/static/logo.png'"
      mode="aspectFill"
    />

    <view class="bubble-main" :class="message.isSelf ? 'bubble-main-self' : ''">
      <text class="name-text">{{ message.isSelf ? selfLabel : peerName }}</text>

      <ChatBusinessCardBubble
        v-if="message.businessCard"
        :card="message.businessCard"
        :self="message.isSelf"
        @longpress="onLongPressMessage"
        @tap-card="$emit('tap-card', message.businessCard)"
      />

      <ChatFileBubble
        v-else-if="message.fileAttachment"
        :file="message.fileAttachment"
        :self="message.isSelf"
        @longpress="onLongPressMessage"
        @tap-file="$emit('tap-file', message.fileAttachment)"
      />

      <ChatLocationBubble
        v-else-if="message.locationAttachment"
        :location="message.locationAttachment"
        :self="message.isSelf"
        @longpress="onLongPressMessage"
        @tap-location="$emit('tap-location', message.locationAttachment)"
      />

      <view
        v-else-if="message.contentType === 'image'"
        class="image-wrap"
        :class="message.isSelf ? 'image-wrap-self' : ''"
        @longpress="onLongPressMessage"
        @tap="$emit('tap-image', message.content)"
      >
        <image class="bubble-image" :src="message.content" mode="widthFix" />
      </view>

      <view
        v-else-if="message.contentType === 'recalled'"
        class="recalled-wrap"
      >
        <text class="recalled-text">{{ message.isSelf ? '\u4f60\u64a4\u56de\u4e86\u4e00\u6761\u6d88\u606f' : '\u5bf9\u65b9\u64a4\u56de\u4e86\u4e00\u6761\u6d88\u606f' }}</text>
      </view>

      <view
        v-else
        class="text-bubble"
        :class="message.isSelf ? 'text-bubble-self' : ''"
        @longpress="onLongPressMessage"
      >
        <text class="bubble-text" :class="message.isSelf ? 'bubble-text-self' : ''">{{ message.content }}</text>
      </view>

      <view v-if="message.isSelf && message.contentType !== 'recalled'" class="state-row">
        <text v-if="message.localState === 'sending'" class="state-text">\u53d1\u9001\u4e2d</text>
        <text v-else-if="message.localState === 'failed'" class="state-text state-text-failed" @tap="$emit('retry', message)">\u53d1\u9001\u5931\u8d25 \u00b7 \u91cd\u8bd5</text>
        <text v-else-if="message.deliveryState === 'read' || message.isRead" class="state-text">\u5df2\u8bfb</text>
        <text v-else-if="message.deliveryState === 'delivered'" class="state-text">\u5df2\u9001\u8fbe</text>
        <text v-else class="state-text">\u5df2\u53d1\u9001</text>
      </view>
    </view>

    <image
      v-if="message.isSelf"
      class="avatar"
      :src="selfAvatar || '/static/logo.png'"
      mode="aspectFill"
    />
  </view>
</template>

<script setup>
import ChatBusinessCardBubble from './ChatBusinessCardBubble.vue'
import ChatFileBubble from './ChatFileBubble.vue'
import ChatLocationBubble from './ChatLocationBubble.vue'

const selfLabel = '\u6211'

const props = defineProps({
  message: {
    type: Object,
    default: () => ({})
  },
  peerName: {
    type: String,
    default: 'Friend'
  },
  peerAvatar: {
    type: String,
    default: '/static/logo.png'
  },
  selfAvatar: {
    type: String,
    default: '/static/logo.png'
  }
})

const emit = defineEmits(['tap-card', 'tap-file', 'tap-location', 'tap-image', 'retry', 'request-revoke'])

const canRevoke = (message) => {
  if (!message || !message.isSelf) {
    return false
  }
  const messageId = String(message.id || '').trim()
  if (!messageId || messageId.startsWith('local-')) {
    return false
  }
  if (String(message.localState || '').trim() === 'sending') {
    return false
  }
  if (String(message.contentType || '').trim() === 'recalled') {
    return false
  }
  return true
}

const onLongPressMessage = () => {
  const message = props.message
  if (!canRevoke(message)) {
    return
  }
  emit('request-revoke', message)
}

</script>

<style scoped>
.bubble-row {
  display: flex;
  align-items: flex-start;
  gap: 16rpx;
  margin-bottom: 24rpx;
}

.bubble-row-self {
  justify-content: flex-end;
}

.avatar {
  width: 80rpx;
  height: 80rpx;
  border-radius: 999rpx;
  background: #dbe4f2;
  flex-shrink: 0;
}

.bubble-main {
  max-width: 75%;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 8rpx;
}

.bubble-main-self {
  align-items: flex-end;
}

.name-text {
  margin-left: 8rpx;
  color: #7b8798;
  font-size: 22rpx;
  line-height: 30rpx;
}

.text-bubble {
  background: #f1f5f9;
  color: #111827;
  border-radius: 24rpx;
  border-top-left-radius: 8rpx;
  padding: 18rpx 22rpx;
}

.text-bubble-self {
  background: #1a57db;
  border-top-left-radius: 24rpx;
  border-top-right-radius: 8rpx;
}

.bubble-text {
  color: #0f172a;
  font-size: 27rpx;
  line-height: 38rpx;
  word-break: break-all;
}

.bubble-text-self {
  color: #ffffff;
}

.image-wrap {
  max-width: 430rpx;
  background: #f1f5f9;
  border-radius: 24rpx;
  border-top-left-radius: 8rpx;
  overflow: hidden;
}

.image-wrap-self {
  border-top-left-radius: 24rpx;
  border-top-right-radius: 8rpx;
}

.bubble-image {
  width: 430rpx;
  max-width: 430rpx;
  display: block;
}

.recalled-wrap {
  max-width: 430rpx;
  padding: 10rpx 16rpx;
}

.recalled-text {
  color: #94a3b8;
  font-size: 22rpx;
  line-height: 30rpx;
}

.state-row {
  margin-top: 2rpx;
}

.state-text {
  color: #94a3b8;
  font-size: 20rpx;
  line-height: 28rpx;
}

.state-text-failed {
  color: #ef4444;
}

@media (prefers-color-scheme: dark) {
  .avatar {
    background: #334155;
  }

  .name-text {
    color: #94a3b8;
  }

  .text-bubble {
    background: #1f2937;
  }

  .text-bubble-self {
    background: #2563eb;
  }

  .bubble-text {
    color: #f8fafc;
  }

  .image-wrap {
    background: #1f2937;
  }

  .recalled-text {
    color: #64748b;
  }
}
</style>
