<template>
  <view class="detail-design-page">
    <scroll-view class="scroll-container" scroll-y :show-scrollbar="false">
      <editor
        id="editor"
        class="rich-editor"
        :placeholder="editorPlaceholder"
        :show-img-size="false"
        :show-img-toolbar="false"
        :show-img-resize="false"
        @ready="onEditorReady"
        @input="onEditorInput"
      />
    </scroll-view>

    <view class="bottom-bar">
      <view class="char-count">
        <text class="count-text">{{ contentLength }}/5000</text>
      </view>
      <view class="button-group">
        <button class="save-btn" hover-class="save-btn-hover" @tap="onSave">
          保存并返回
        </button>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onLoad, onReady } from '@dcloudio/uni-app'

const detailContent = ref('')
const contentLength = ref(0)
const editorPlaceholder = '请输入活动详情页内容...\n\n例如：\n活动介绍\n活动流程\n注意事项\n等等'
let editorCtx = null
let openerEventChannel = null

const onEditorReady = () => {
  uni.createSelectorQuery()
    .select('#editor')
    .context((res) => {
      editorCtx = res.context

      // 如果有传入的内容，设置到编辑器
      if (detailContent.value) {
        editorCtx.setContents({
          html: detailContent.value
        })
      }
    })
    .exec()
}

const onEditorInput = (e) => {
  // 更新字符计数
  if (e.detail && e.detail.html) {
    const text = e.detail.html.replace(/<[^>]+>/g, '')
    contentLength.value = text.length
  }
}

const onSave = () => {
  if (editorCtx) {
    editorCtx.getContents({
      success: (res) => {
        const htmlContent = res.html || ''

        console.log('========== 保存详情页内容 ==========')
        console.log('htmlContent:', htmlContent)
        console.log('htmlContent length:', htmlContent.length)
        console.log('==================================')

        // 尝试多种方式传递数据
        if (openerEventChannel) {
          openerEventChannel.emit('detailContentUpdated', {
            content: htmlContent
          })
          console.log('已通过 openerEventChannel 触发事件')
        } else {
          console.warn('openerEventChannel 不存在，尝试使用其他方式')

          // 方式2: 使用全局事件
          uni.$emit('detailContentUpdated', {
            content: htmlContent
          })
          console.log('已通过 uni.$emit 触发事件')
        }

        // 延迟返回，确保事件有时间传递
        setTimeout(() => {
          uni.navigateBack()
        }, 100)
      }
    })
  } else {
    console.warn('editorCtx 不存在，直接返回')
    uni.navigateBack()
  }
}

onLoad(() => {
  // onLoad 中不做任何操作，等待 onReady
})

onReady(() => {
  // 在 onReady 中获取 EventChannel，确保页面完全加载
  if (typeof uni.getOpenerEventChannel === 'function') {
    openerEventChannel = uni.getOpenerEventChannel()

    console.log('========== onReady 获取 EventChannel ==========')
    console.log('openerEventChannel:', openerEventChannel)
    console.log('==================================')

    // 接收传入的详情内容
    openerEventChannel.on('detailContent', (content) => {
      console.log('========== 接收到详情内容 ==========')
      console.log('content type:', typeof content)
      console.log('content:', content)
      console.log('==================================')

      if (typeof content === 'string') {
        detailContent.value = content

        // 如果编辑器已经准备好，立即设置内容
        if (editorCtx) {
          editorCtx.setContents({
            html: content
          })
        }
      }
    })
  } else {
    console.warn('uni.getOpenerEventChannel 不可用')
  }
})
</script>

<style scoped>
.detail-design-page {
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
  padding: 0 24rpx;
  box-sizing: border-box;
}

.rich-editor {
  width: 100%;
  min-height: 100%;
  background: #ffffff;
  box-sizing: border-box;
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

.button-group {
  display: flex;
  gap: 16rpx;
}

.save-btn {
  flex: 1;
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
  .detail-design-page {
    background: #0f172a;
  }

  .rich-editor {
    background: #1e293b;
    box-shadow: 0 2rpx 16rpx rgba(0, 0, 0, 0.3);
  }

  .bottom-bar {
    background: #1e293b;
    border-top-color: #334155;
  }
}
</style>
