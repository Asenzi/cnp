<template>
  <view class="help-page">
    <!-- 导航栏 -->
    <view class="navbar" :style="{ paddingTop: statusBarHeight + 'px' }">
      <view class="navbar-back" @tap="goBack">
        <image class="back-icon" src="/static/me-icons/arrow-back-dark.png" mode="aspectFit" />
      </view>
      <text class="navbar-title">帮助与反馈</text>
      <view class="navbar-placeholder"></view>
    </view>

    <scroll-view class="page-scroll" scroll-y :show-scrollbar="false">
      <view class="page-body">
        <view class="faq-card">
          <view class="section-head">
            <text class="section-title section-title-small">常见问题</text>
          </view>
          <view
            v-for="(item, index) in faqItems"
            :key="item.title"
            class="faq-row"
            :class="{ 'faq-row-border': index < faqItems.length - 1 }"
            hover-class="row-active"
            @tap="openFaq(item)"
          >
            <text class="faq-title">{{ item.title }}</text>
            <image class="chevron" src="/static/me-icons/chevron-light.png" mode="aspectFit" />
          </view>
        </view>

        <view class="feedback-section">
          <text class="section-title">意见反馈</text>
          <view class="form-card">
            <view class="field-block">
              <text class="field-label">反馈类型</text>
              <picker mode="selector" :range="feedbackTypeLabels" :value="feedbackTypeIndex" @change="onTypeChange">
                <view class="select-field">
                  <text class="select-text" :class="{ 'select-placeholder': feedbackTypeIndex < 0 }">
                    {{ selectedFeedbackTypeLabel || '请选择反馈类型' }}
                  </text>
                  <image class="select-icon" src="/static/me-icons/expand-more-slate.png" mode="aspectFit" />
                </view>
              </picker>
            </view>

            <view class="field-block">
              <text class="field-label">问题描述</text>
              <textarea
                v-model="description"
                class="textarea-field"
                maxlength="500"
                placeholder="请详细描述您遇到的问题或改进建议..."
                placeholder-class="placeholder"
              />
            </view>

            <view class="field-block">
              <text class="field-label">上传截图（选填）</text>
              <view class="image-row">
                <view
                  v-if="images.length < maxImages"
                  class="upload-tile"
                  hover-class="upload-tile-active"
                  @tap="chooseImages"
                >
                  <image class="upload-icon" src="/static/me-icons/image-primary.png" mode="aspectFit" />
                  <text class="upload-text">添加图片</text>
                </view>
                <view v-for="(image, index) in images" :key="image.id" class="preview-wrap">
                  <image class="preview-image" :src="image.previewUrl" mode="aspectFill" />
                  <view class="remove-btn" @tap.stop="removeImage(index)">
                    <text class="remove-text">×</text>
                  </view>
                </view>
              </view>
            </view>

            <view class="field-block">
              <text class="field-label">联系方式</text>
              <input
                v-model="contact"
                class="input-field"
                placeholder="手机号或邮箱，方便我们联系您"
                placeholder-class="placeholder"
              />
            </view>

            <button
              class="submit-btn"
              :loading="isSubmitting"
              :disabled="isSubmitting"
              hover-class="submit-btn-active"
              @tap="submitFeedback"
            >
              {{ isSubmitting ? '提交中...' : '提交反馈' }}
            </button>
          </view>
        </view>

        <view class="support-list">
          <!-- <button class="support-card support-card-primary" open-type="contact" hover-class="support-card-active">
            <view class="support-left">
              <view class="support-icon support-icon-primary">
                <image class="support-icon-img support-icon-invert" src="/static/me-icons/help-gray.png" mode="aspectFit" />
              </view>
              <view class="support-copy">
                <text class="support-title support-title-primary">在线客服</text>
                <text class="support-desc support-desc-primary">专业客服为您实时解答问题</text>
              </view>
            </view>
            <text class="support-arrow support-arrow-primary">→</text>
          </button> -->

          <view class="support-card" hover-class="support-card-active" @tap="copySupportEmail">
            <view class="support-left">
              <view class="support-icon">
                <image class="support-icon-img" src="/static/me-icons/contact-page-primary.png" mode="aspectFit" />
              </view>
              <view class="support-copy">
                <text class="support-title">复制邮箱</text>
                <text class="support-desc">{{ supportEmail }}</text>
              </view>
            </view>
            <text class="support-arrow">→</text>
          </view>
        </view>
      </view>
    </scroll-view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { submitHelpFeedback, uploadHelpFeedbackImage } from '../../../api/feedback'

const { statusBarHeight = 0 } = uni.getSystemInfoSync()

const supportEmail = 'support@quanmailian.com'
const maxImages = 3
const sourcePage = 'pages/me/help-feedback/index'

const feedbackTypeIndex = ref(-1)
const description = ref('')
const contact = ref('')
const images = ref([])
const isSubmitting = ref(false)

const feedbackTypes = [
  { label: '账号相关', value: 'account' },
  { label: '支付充值', value: 'payment' },
  { label: '圈子 / 活动', value: 'circles' },
  { label: '实名认证', value: 'verification' },
  { label: '其他问题', value: 'other' }
]

const faqItems = [
  {
    title: '如何修改实名认证信息？',
    answer: '实名认证信息提交后会进入审核流程。如需修改，请前往实名认证页面重新提交资料，或联系在线客服协助处理。'
  },
  {
    title: '圈子成员上限是多少？',
    answer: '圈子成员上限会根据圈子类型、运营状态和平台规则调整。创建者可以在圈子管理页查看当前可容纳人数。'
  },
  {
    title: '充值未到账如何处理？',
    answer: '请先确认支付是否成功。如果支付成功但余额未更新，可保留支付截图并提交反馈，我们会尽快核对。'
  },
  {
    title: '为什么我被限制在圈子里发言？',
    answer: '可能是圈子管理员设置了发言规则，或账号触发了平台风控。你可以联系圈主或提交反馈申诉。'
  }
]

const feedbackTypeLabels = computed(() => feedbackTypes.map((item) => item.label))

const selectedFeedbackTypeLabel = computed(() => {
  const item = feedbackTypes[feedbackTypeIndex.value]
  return item?.label || ''
})

const onTypeChange = (event) => {
  feedbackTypeIndex.value = Number(event?.detail?.value ?? -1)
}

const openFaq = (item) => {
  uni.showModal({
    title: item.title,
    content: item.answer,
    showCancel: false,
    confirmText: '知道了'
  })
}

const chooseImages = () => {
  if (isSubmitting.value) {
    return
  }
  const remaining = maxImages - images.value.length
  if (remaining <= 0) {
    return
  }
  uni.chooseImage({
    count: remaining,
    sizeType: ['compressed'],
    sourceType: ['album', 'camera'],
    success: (res) => {
      const nextImages = Array.isArray(res?.tempFilePaths) ? res.tempFilePaths : []
      const newItems = nextImages.map((path) => buildLocalImageItem(path))
      images.value = [...images.value, ...newItems].slice(0, maxImages)
    }
  })
}

const removeImage = (index) => {
  images.value = images.value.filter((_, itemIndex) => itemIndex !== index)
}

const goBack = () => {
  uni.navigateBack()
}

const copySupportEmail = () => {
  uni.setClipboardData({
    data: supportEmail,
    success: () => {
      uni.showToast({
        title: '邮箱已复制',
        icon: 'none'
      })
    }
  })
}

const buildLocalImageItem = (path) => ({
  id: `${Date.now()}_${Math.random().toString(16).slice(2, 8)}`,
  previewUrl: String(path || '').trim(),
  localPath: String(path || '').trim(),
  path: '',
  url: '',
  name: '',
  size: 0
})

const getFileNameFromPath = (filePath) => {
  const normalized = String(filePath || '').trim()
  if (!normalized) {
    return 'feedback-image'
  }
  const segments = normalized.split(/[\\/]/)
  return segments[segments.length - 1] || 'feedback-image'
}

const isValidContact = (value) => {
  const normalized = String(value || '').trim()
  if (!normalized) {
    return true
  }
  return /^1\d{10}$/.test(normalized) || /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(normalized)
}

const ensureUploadedImages = async () => {
  const normalizedImages = []

  for (const item of images.value) {
    if (item.path) {
      normalizedImages.push({
        path: item.path,
        name: item.name || getFileNameFromPath(item.previewUrl),
        size: Number(item.size || 0) || 0
      })
      continue
    }

    const uploadResult = await uploadHelpFeedbackImage(item.localPath, getFileNameFromPath(item.localPath))
    const uploadedItem = {
      ...item,
      path: String(uploadResult?.path || '').trim(),
      url: String(uploadResult?.url || '').trim(),
      name: String(uploadResult?.name || '').trim(),
      size: Number(uploadResult?.size || 0) || 0
    }

    normalizedImages.push({
      path: uploadedItem.path,
      name: uploadedItem.name || getFileNameFromPath(item.localPath),
      size: uploadedItem.size
    })
    images.value = images.value.map((image) => (image.id === item.id ? uploadedItem : image))
  }

  return normalizedImages
}

const resetForm = () => {
  feedbackTypeIndex.value = -1
  description.value = ''
  contact.value = ''
  images.value = []
}

const submitFeedback = async () => {
  if (isSubmitting.value) {
    return
  }

  if (feedbackTypeIndex.value < 0) {
    uni.showToast({
      title: '请选择反馈类型',
      icon: 'none'
    })
    return
  }

  if (!description.value.trim()) {
    uni.showToast({
      title: '请填写问题描述',
      icon: 'none'
    })
    return
  }

  if (!isValidContact(contact.value)) {
    uni.showToast({
      title: '请填写正确的手机号或邮箱',
      icon: 'none'
    })
    return
  }

  isSubmitting.value = true
  uni.showLoading({
    title: images.value.length ? '上传并提交中' : '提交中',
    mask: true
  })

  try {
    const uploadedImages = await ensureUploadedImages()
    const result = await submitHelpFeedback({
      feedback_type: feedbackTypes[feedbackTypeIndex.value].value,
      description: description.value.trim(),
      contact: contact.value.trim(),
      images: uploadedImages,
      source_page: sourcePage
    })

    uni.hideLoading()
    resetForm()
    uni.showModal({
      title: '反馈已提交',
      content: result?.ticket_no
        ? `我们已收到你的反馈，会尽快处理。\n反馈编号：${result.ticket_no}`
        : '我们已收到你的反馈，会尽快处理。',
      showCancel: false,
      confirmText: '知道了'
    })
  } catch (error) {
    uni.hideLoading()
    uni.showToast({
      title: error?.message || '提交失败，请稍后重试',
      icon: 'none'
    })
  } finally {
    isSubmitting.value = false
  }
}
</script>

<style scoped>
.help-page {
  min-height: 100vh;
  background: #f6f6f8;
}

/* 导航栏 */
.navbar {
  position: sticky;
  top: 0;
  z-index: 100;
  background: #ffffff;
  border-bottom: 1rpx solid #e7ecf3;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 88rpx;
  padding-left: 16rpx;
  padding-right: 32rpx;
}

.navbar-back {
  width: 72rpx;
  height: 72rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.back-icon {
  width: 40rpx;
  height: 40rpx;
}

.navbar-title {
  flex: 1;
  text-align: center;
  font-size: 32rpx;
  font-weight: 600;
  color: #172033;
}

.navbar-placeholder {
  width: 72rpx;
}

.page-scroll {
  height: calc(100vh - 88rpx);
}

.page-body {
  padding: 28rpx 32rpx calc(48rpx + env(safe-area-inset-bottom));
  display: flex;
  flex-direction: column;
  gap: 40rpx;
}

.faq-card,
.form-card,
.support-card {
  border-radius: 16rpx;
  background: #ffffff;
  overflow: hidden;
}

.section-head {
  height: 72rpx;
  padding: 0 32rpx;
  background: #f8f9fc;
  display: flex;
  align-items: center;
}

.section-title {
  display: block;
  color: #172033;
  font-size: 28rpx;
  line-height: 36rpx;
  font-weight: 600;
}

.section-title-small {
  font-size: 26rpx;
  line-height: 34rpx;
}

.faq-row {
  min-height: 92rpx;
  padding: 0 32rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24rpx;
}

.faq-row-border {
  border-bottom: 1rpx solid #f1f5f9;
}

.faq-title {
  flex: 1;
  min-width: 0;
  color: #334155;
  font-size: 26rpx;
  line-height: 36rpx;
}

.chevron {
  width: 24rpx;
  height: 24rpx;
  flex-shrink: 0;
}

.row-active,
.support-card-active {
  opacity: 0.82;
}

.feedback-section {
  display: flex;
  flex-direction: column;
  gap: 24rpx;
}

.form-card {
  padding: 30rpx;
  display: flex;
  flex-direction: column;
  gap: 30rpx;
}

.field-block {
  display: flex;
  flex-direction: column;
  gap: 14rpx;
}

.field-label {
  color: #66758a;
  font-size: 24rpx;
  line-height: 32rpx;
  font-weight: 600;
}

.select-field,
.input-field,
.textarea-field {
  width: 100%;
  box-sizing: border-box;
  border-radius: 12rpx;
  background: #f6f8fc;
  color: #172033;
  font-size: 28rpx;
}

.select-field {
  min-height: 84rpx;
  padding: 0 24rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
}

.select-text {
  color: #172033;
  font-size: 28rpx;
}

.select-placeholder {
  color: #94a3b8;
}

.select-icon {
  width: 28rpx;
  height: 28rpx;
  flex-shrink: 0;
}

.input-field {
  height: 84rpx;
  padding: 0 24rpx;
}

.textarea-field {
  height: 192rpx;
  padding: 22rpx 24rpx;
  line-height: 38rpx;
}

.image-row {
  display: flex;
  align-items: center;
  gap: 20rpx;
  flex-wrap: wrap;
}

.upload-tile,
.preview-wrap {
  position: relative;
  width: 144rpx;
  height: 144rpx;
  border-radius: 16rpx;
}

.upload-tile {
  border: 2rpx dashed #dbe3ef;
  background: #f8fafc;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8rpx;
}

.upload-tile-active {
  border-color: rgba(26, 87, 219, 0.42);
  opacity: 0.86;
}

.upload-icon {
  width: 42rpx;
  height: 42rpx;
  opacity: 0.72;
}

.upload-text {
  color: #94a3b8;
  font-size: 20rpx;
  line-height: 28rpx;
}

.preview-image {
  width: 144rpx;
  height: 144rpx;
  border-radius: 16rpx;
  background: #e2e8f0;
}

.remove-btn {
  position: absolute;
  right: -12rpx;
  top: -12rpx;
  width: 36rpx;
  height: 36rpx;
  border-radius: 999rpx;
  background: #e11d48;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 6rpx 14rpx rgba(225, 29, 72, 0.24);
}

.remove-text {
  color: #ffffff;
  font-size: 28rpx;
  line-height: 32rpx;
}

.submit-btn {
  margin: 4rpx 0 0;
  height: 88rpx;
  line-height: 88rpx;
  border-radius: 12rpx;
  border: 0;
  background: #2563eb;
  color: #ffffff;
  font-size: 28rpx;
  font-weight: 600;
}

.submit-btn::after,
.support-card::after {
  border: 0;
}

.submit-btn-active {
  opacity: 0.88;
  transform: translateY(1rpx);
}

.support-list {
  display: flex;
  flex-direction: column;
  gap: 24rpx;
}

.support-card {
  margin: 0;
  min-height: 144rpx;
  padding: 24rpx 30rpx;
  border: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  text-align: left;
}

.support-card-primary {
  background: rgba(26, 87, 219, 0.07);
}

.support-left {
  display: flex;
  align-items: center;
  gap: 24rpx;
}

.support-icon {
  width: 88rpx;
  height: 88rpx;
  border-radius: 999rpx;
  background: #f1f5f9;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.support-icon-primary {
  background: #1a57db;
  box-shadow: 0 12rpx 22rpx rgba(26, 87, 219, 0.28);
}

.support-icon-img {
  width: 42rpx;
  height: 42rpx;
}

.support-icon-invert {
  filter: brightness(0) invert(1);
}

.support-copy {
  display: flex;
  flex-direction: column;
  gap: 6rpx;
}

.support-title {
  color: #172033;
  font-size: 28rpx;
  line-height: 36rpx;
  font-weight: 600;
}

.support-desc {
  color: #66758a;
  font-size: 24rpx;
  line-height: 32rpx;
}

.support-title-primary {
  color: #2563eb;
}

.support-desc-primary {
  color: rgba(37, 99, 235, 0.68);
}

.support-arrow {
  color: #cbd5e1;
  font-size: 40rpx;
  line-height: 40rpx;
  font-weight: 500;
}

.support-arrow-primary {
  color: #2563eb;
}

/* 深色模式 */
@media (prefers-color-scheme: dark) {
  .help-page {
    background: #0a0a0a;
  }

  .navbar {
    background: #1a1a1a;
    border-bottom-color: #2a2a2a;
  }

  .navbar-title {
    color: #ffffff;
  }

  .faq-card,
  .form-card,
  .support-card {
    background: #1a1a1a;
  }

  .section-head {
    background: #0f0f0f;
  }

  .section-title {
    color: #ffffff;
  }

  .faq-title {
    color: #b0b0b0;
  }

  .faq-row-border {
    border-bottom-color: #2a2a2a;
  }

  .field-label {
    color: #8a8a8a;
  }

  .select-field,
  .input-field,
  .textarea-field {
    background: #0f0f0f;
    color: #ffffff;
  }

  .select-placeholder {
    color: #666666;
  }

  .support-icon {
    background: #2a2a2a;
  }

  .support-title {
    color: #ffffff;
  }

  .support-desc {
    color: #8a8a8a;
  }

  .support-arrow {
    color: #666666;
  }
}

</style>
