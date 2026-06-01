<template>
  <view class="address-editor-page">
    <scroll-view class="scroll-container" scroll-y :show-scrollbar="false">
      <textarea
        class="address-textarea"
        :value="addressContent"
        maxlength="500"
        placeholder="请输入详细地址...&#10;&#10;例如：&#10;XX大厦XX楼XX室&#10;或其他详细位置描述"
        placeholder-class="placeholder-text"
        :show-confirm-bar="false"
        auto-height
        @input="onInput"
      />
    </scroll-view>

    <view class="bottom-bar">
      <view class="char-count">
        <text class="count-text">{{ addressContent.length }}/500</text>
      </view>
      <button class="save-btn" hover-class="save-btn-hover" @tap="onSave">
        保存并返回
      </button>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'

const addressContent = ref('')
let openerEventChannel = null

const onInput = (event) => {
  addressContent.value = String(event?.detail?.value || '')
}

const onSave = () => {
  if (openerEventChannel) {
    openerEventChannel.emit('addressContentUpdated', {
      content: addressContent.value
    })
  }
  uni.navigateBack()
}

onLoad(() => {
  if (typeof uni.getOpenerEventChannel === 'function') {
    openerEventChannel = uni.getOpenerEventChannel()

    // 接收传入的地址内容
    openerEventChannel.on('addressContent', (content) => {
      if (typeof content === 'string') {
        addressContent.value = content
      }
    })
  }
})
</script>

<style scoped>
.address-editor-page {
  height: 100vh;
  width: 100vw;
  background: #f6f6f8;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.scroll-container {
  flex: 1;
  width: 100%;
  height: 0;
  padding: 24rpx;
  box-sizing: border-box;
}

.address-textarea {
  width: 100%;
  min-height: 400rpx;
  padding: 24rpx;
  background: #ffffff;
  border-radius: 16rpx;
  box-shadow: 0 2rpx 16rpx rgba(15, 23, 42, 0.06);
  color: #0f172a;
  font-size: 28rpx;
  line-height: 44rpx;
  box-sizing: border-box;
}

.placeholder-text {
  color: #94a3b8;
}

.bottom-bar {
  flex-shrink: 0;
  padding: 16rpx 24rpx;
  padding-bottom: calc(16rpx + env(safe-area-inset-bottom));
  background: #ffffff;
  border-top: 1rpx solid #e2e8f0;
  box-shadow: 0 -4rpx 16rpx rgba(15, 23, 42, 0.04);
}

.char-count {
  margin-bottom: 12rpx;
  text-align: right;
}

.count-text {
  color: #94a3b8;
  font-size: 22rpx;
  line-height: 30rpx;
}

.save-btn {
  width: 100%;
  height: 96rpx;
  border-radius: 16rpx;
  background: linear-gradient(135deg, #1a57db 0%, #1e40af 100%);
  color: #ffffff;
  font-size: 28rpx;
  line-height: 96rpx;
  font-weight: 600;
  text-align: center;
  border: 0;
}

.save-btn-hover {
  opacity: 0.85;
}

@media (prefers-color-scheme: dark) {
  .address-editor-page {
    background: #0f172a;
  }

  .address-textarea {
    background: #1e293b;
    box-shadow: 0 2rpx 16rpx rgba(0, 0, 0, 0.3);
    color: #f1f5f9;
  }

  .bottom-bar {
    background: #1e293b;
    border-top-color: #334155;
  }
}
</style>
