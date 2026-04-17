<template>
  <view class="submit-page">
    <view class="page-shell">
      <view class="content-body">
        <view class="upload-section">
          <view class="upload-inner">
            <view
              class="card-upload"
              :class="{ 'card-upload-disabled': isReadonly }"
              hover-class="card-upload-hover"
              :style="uploadCardStyle"
              @tap="onPickCardFile"
            >
              <view class="upload-overlay">
                <view class="camera-dot">
                  <image class="camera-icon" mode="aspectFit" src="/static/me-icons/camera-white.png" />
                </view>
                <text class="overlay-title">拍照/上传名片</text>
                <text class="overlay-subtitle">支持 JPG, PNG, PDF 格式</text>
              </view>
            </view>

            <view class="upload-tip-row">
              <image class="tip-icon" mode="aspectFit" src="/static/me-icons/shield-person-primary.png" />
              <text class="upload-tip-text">名片认证助您在圈子里快速获得信任</text>
            </view>

            <view
              class="reupload-btn"
              :class="{ 'reupload-btn-disabled': isReadonly || uploadingCard }"
              hover-class="reupload-btn-hover"
              @tap="onPickCardFile"
            >
              <image class="reupload-icon" mode="aspectFit" src="/static/me-icons/upload-primary.png" />
              <text class="reupload-text">{{ uploadingCard ? '上传中...' : '重新上传' }}</text>
            </view>
          </view>
        </view>

        <view class="fields-section">
          <view class="section-title-row">
            <view class="title-bar"></view>
            <text class="section-title">名片信息 (可编辑)</text>
          </view>

          <view class="field-list">
            <view class="field-item">
              <text class="field-label">姓名</text>
              <view class="input-wrap">
                <input
                  v-model="form.card_holder_name"
                  class="field-input"
                  :disabled="isReadonly"
                  maxlength="32"
                  placeholder="请输入姓名"
                  placeholder-class="field-placeholder"
                />
                <image class="edit-icon" mode="aspectFit" src="/static/me-icons/edit-gray.png" />
              </view>
            </view>

            <view class="field-item">
              <text class="field-label">公司名称</text>
              <view class="input-wrap">
                <input
                  v-model="form.company_name"
                  class="field-input"
                  :disabled="isReadonly"
                  maxlength="128"
                  placeholder="请输入公司名称"
                  placeholder-class="field-placeholder"
                />
                <image class="edit-icon" mode="aspectFit" src="/static/me-icons/edit-gray.png" />
              </view>
            </view>

            <view class="field-item">
              <text class="field-label">职位</text>
              <view class="input-wrap">
                <input
                  v-model="form.card_title"
                  class="field-input"
                  :disabled="isReadonly"
                  maxlength="64"
                  placeholder="请输入职位"
                  placeholder-class="field-placeholder"
                />
                <image class="edit-icon" mode="aspectFit" src="/static/me-icons/edit-gray.png" />
              </view>
            </view>
          </view>

          <view class="tips-card">
            <text class="tips-title">提示：</text>
            <text class="tips-text">1. 请确保名片文字清晰可见，避免反光或模糊。</text>
            <text class="tips-text">2. 认证信息将用于个人主页展示，通过后可点亮认证标识。</text>
          </view>

          <view v-if="currentItem.reject_reason" class="reject-row">
            <text class="reject-text">驳回原因：{{ currentItem.reject_reason }}</text>
          </view>
        </view>
      </view>

      <view class="footer-bar">
        <view
          class="submit-btn"
          :class="{ 'submit-btn-disabled': isReadonly || submitting }"
          hover-class="submit-btn-hover"
          @tap="onSubmit"
        >
          <text class="submit-btn-text">{{ submitButtonText }}</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { uploadCurrentUserCardFile } from '../../../../api/user'
import { getMyVerificationOverview, submitBusinessCardVerification } from '../../../../api/verification'
import { VERIFICATION_STATUS, VERIFICATION_TYPE, normalizeOverviewItems } from '../modules/verification-types'

const DEFAULT_CARD_BG =
  'https://lh3.googleusercontent.com/aida-public/AB6AXuDJ0q1UkInanMvUuYd78H41YiEJagGdtPQGVMUHv6GP4Z6gR1R3RSQ8TBZ3dPXiud95nuesYVOa-BJm2b7Pqw6vdm0IqCfKEsCc-gxiMzCXuJhK2WWbcGMG_tutY7jD8TnI2eKC9upoSNu9heJkr_tPSEZiYogTfzG1IMdhAhL63yjNmlYNzwQMfy4I3UZvUssHM8EbdnC8BktKg_nrITJ0wC1tBxyDxhtwfP8pUc3YC7bWoacK3KW6H1tjZhkLF98aWuKwP9RBMB6z'

const loading = ref(false)
const submitting = ref(false)
const uploadingCard = ref(false)

const itemMap = ref(normalizeOverviewItems([]))
const cardPreviewUrl = ref('')

const form = ref({
  card_holder_name: '',
  company_name: '',
  card_title: '',
  card_file_url: ''
})

const currentItem = computed(() =>
  itemMap.value?.[VERIFICATION_TYPE.BUSINESS_CARD] || {
    status: VERIFICATION_STATUS.NOT_SUBMITTED,
    reject_reason: ''
  }
)

const currentStatus = computed(() => currentItem.value.status || VERIFICATION_STATUS.NOT_SUBMITTED)

const isReadonly = computed(
  () => currentStatus.value === VERIFICATION_STATUS.PENDING || currentStatus.value === VERIFICATION_STATUS.APPROVED
)

const submitButtonText = computed(() => {
  if (submitting.value) {
    return '提交中...'
  }
  if (currentStatus.value === VERIFICATION_STATUS.APPROVED) {
    return '已通过认证'
  }
  if (currentStatus.value === VERIFICATION_STATUS.PENDING) {
    return '审核中'
  }
  return '确认提交'
})

const uploadCardStyle = computed(() => ({
  backgroundImage: `url("${cardPreviewUrl.value || DEFAULT_CARD_BG}")`,
  backgroundSize: 'cover',
  backgroundPosition: 'center'
}))

const showToast = (title) => {
  uni.showToast({ title, icon: 'none' })
}

const loadOverview = async () => {
  if (loading.value) {
    return
  }

  loading.value = true
  try {
    const overview = await getMyVerificationOverview()
    itemMap.value = normalizeOverviewItems(overview?.items || [])
  } catch (err) {
    if (err?.statusCode === 401) {
      showToast('请先登录')
      setTimeout(() => {
        uni.navigateTo({ url: '/pages/auth/login/index' })
      }, 200)
      return
    }
    showToast(err?.message || '加载认证状态失败')
  } finally {
    loading.value = false
  }
}

const onPickCardFile = () => {
  if (isReadonly.value || uploadingCard.value) {
    return
  }

  uni.chooseMessageFile({
    count: 1,
    type: 'file',
    extension: ['jpg', 'jpeg', 'png', 'pdf'],
    success: async (res) => {
      const file = res?.tempFiles?.[0]
      if (!file?.path) {
        return
      }

      uploadingCard.value = true
      try {
        const uploaded = await uploadCurrentUserCardFile(file.path, file.name || '名片文件')
        form.value.card_file_url = String(uploaded?.url || '')

        const lowerName = String(file.name || file.path || '').toLowerCase()
        const isImage = /\.(jpg|jpeg|png)$/i.test(lowerName)
        cardPreviewUrl.value = isImage ? file.path : ''

        showToast('名片上传成功')
      } catch (err) {
        showToast(err?.message || '上传失败，请重试')
      } finally {
        uploadingCard.value = false
      }
    }
  })
}

const onSubmit = async () => {
  if (isReadonly.value || submitting.value) {
    return
  }

  const cardHolderName = String(form.value.card_holder_name || '').trim()
  if (!cardHolderName) {
    showToast('请输入姓名')
    return
  }

  const cardFileUrl = String(form.value.card_file_url || '').trim()
  if (!cardFileUrl) {
    showToast('请先上传名片')
    return
  }

  submitting.value = true
  try {
    await submitBusinessCardVerification({
      card_holder_name: cardHolderName.slice(0, 32),
      company_name: String(form.value.company_name || '').trim().slice(0, 128) || null,
      card_title: String(form.value.card_title || '').trim().slice(0, 64) || null,
      card_file_url: cardFileUrl.slice(0, 255)
    })
    showToast('名片认证资料已提交审核')
    setTimeout(() => {
      uni.redirectTo({
        url: '/pages/me/auth/result/index?type=business_card'
      })
    }, 240)
  } catch (err) {
    showToast(err?.message || '提交失败，请稍后重试')
  } finally {
    submitting.value = false
  }
}

onLoad((query) => {
  const type = String(query?.type || '').trim()
  if (type === VERIFICATION_TYPE.REAL_NAME) {
    uni.redirectTo({ url: '/pages/me/auth/realname/index' })
    return
  }
  if (type === VERIFICATION_TYPE.ENTERPRISE) {
    uni.redirectTo({ url: '/pages/me/auth/enterprise/index' })
    return
  }
  loadOverview()
})
</script>

<style scoped>
.submit-page {
  min-height: 100vh;
  background: #f6f6f8;
}

.page-shell {
  position: relative;
  min-height: 100vh;
  width: 100%;
  max-width: 448px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  background: #f6f6f8;
  overflow-x: hidden;
  box-shadow: 0 10px 28px rgba(15, 23, 42, 0.08);
  box-sizing: border-box;
}

.content-body {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.upload-section {
  display: flex;
  flex-direction: column;
  padding: 24px 14px;
  background: #ffffff;
  margin-bottom: 8px;
  box-sizing: border-box;
}

.upload-inner {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 18px;
}

.card-upload {
  position: relative;
  width: 100%;
  max-width: 320px;
  aspect-ratio: 1.58 / 1;
  border-radius: 10px;
  border: 2px dashed #cbd5e1;
  background-color: #f8fafc;
  overflow: hidden;
  transition: all 0.2s ease;
  box-sizing: border-box;
}

.card-upload-hover {
  border-color: rgba(26, 87, 219, 0.5);
}

.card-upload-disabled {
  opacity: 0.7;
}

.upload-overlay {
  position: absolute;
  inset: 0;
  background: rgba(15, 23, 42, 0.4);
  backdrop-filter: blur(2px);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #ffffff;
}

.camera-dot {
  width: 46px;
  height: 46px;
  border-radius: 999px;
  background: #1a57db;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 10px;
  box-shadow: 0 6px 16px rgba(26, 87, 219, 0.28);
}

.camera-icon {
  width: 22px;
  height: 22px;
}

.overlay-title {
  font-size: 16px;
  font-weight: 700;
  line-height: 1.3;
}

.overlay-subtitle {
  margin-top: 2px;
  font-size: 11px;
  opacity: 0.9;
}

.upload-tip-row {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 6px;
  text-align: center;
}

.tip-icon {
  width: 16px;
  height: 16px;
}

.upload-tip-text {
  color: #64748b;
  font-size: 13px;
  line-height: 1.5;
}

.reupload-btn {
  min-width: 124px;
  height: 38px;
  padding: 0 18px;
  border-radius: 999px;
  background: rgba(26, 87, 219, 0.1);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  box-sizing: border-box;
}

.reupload-btn-hover {
  background: rgba(26, 87, 219, 0.2);
}

.reupload-btn-disabled {
  opacity: 0.7;
}

.reupload-icon {
  width: 16px;
  height: 16px;
}

.reupload-text {
  color: #1a57db;
  font-size: 13px;
  font-weight: 700;
}

.fields-section {
  display: flex;
  flex-direction: column;
  padding: 12px 14px 88px;
  box-sizing: border-box;
}

.section-title-row {
  display: flex;
  align-items: center;
  padding: 0 4px 12px;
}

.title-bar {
  width: 3px;
  height: 14px;
  background: #1a57db;
  border-radius: 999px;
  margin-right: 6px;
}

.section-title {
  color: #0f172a;
  font-size: 15px;
  font-weight: 700;
}

.field-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.field-item {
  display: flex;
  flex-direction: column;
  width: 100%;
}

.field-label {
  color: #64748b;
  font-size: 13px;
  font-weight: 500;
  padding: 0 4px 5px;
}

.input-wrap {
  position: relative;
}

.field-input {
  width: 100%;
  height: 50px;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  background: #ffffff;
  padding: 0 42px 0 14px;
  line-height: 50px;
  color: #0f172a;
  font-size: 15px;
  font-weight: 500;
  box-sizing: border-box;
}

.field-input:focus {
  border-color: #1a57db;
  box-shadow: 0 0 0 2px rgba(26, 87, 219, 0.2);
}

.field-placeholder {
  color: #94a3b8;
  line-height: 50px;
}

.edit-icon {
  position: absolute;
  right: 14px;
  top: 50%;
  transform: translateY(-50%);
  width: 16px;
  height: 16px;
  opacity: 0.75;
}

.tips-card {
  margin-top: 24px;
  padding: 14px;
  border-radius: 10px;
  background: rgba(26, 87, 219, 0.05);
  border: 1px solid rgba(26, 87, 219, 0.1);
  box-sizing: border-box;
}

.tips-title {
  display: block;
  margin-bottom: 3px;
  color: #1a57db;
  font-size: 11px;
  font-weight: 700;
}

.tips-text {
  display: block;
  color: #475569;
  font-size: 11px;
  line-height: 1.6;
}

.reject-row {
  margin-top: 10px;
}

.reject-text {
  color: #dc2626;
  font-size: 11px;
  line-height: 1.6;
}

.footer-bar {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  width: 100%;
  max-width: 448px;
  margin: 0 auto;
  padding: 12px 14px;
  border-top: 1px solid #e2e8f0;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(8px);
  box-sizing: border-box;
}

.submit-btn {
  width: 100%;
  height: 44px;
  border-radius: 10px;
  background: #1a57db;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8px 16px rgba(26, 87, 219, 0.2);
}

.submit-btn-hover {
  background: rgba(26, 87, 219, 0.9);
}

.submit-btn-disabled {
  background: #94a3b8;
  box-shadow: none;
}

.submit-btn-text {
  color: #ffffff;
  font-size: 15px;
  font-weight: 700;
}

@media (prefers-color-scheme: dark) {
  .submit-page,
  .page-shell {
    background: #111621;
  }

  .upload-section {
    background: #0f172a;
    border-bottom-color: #1e293b;
  }

  .section-title,
  .field-input {
    color: #f1f5f9;
  }

  .field-label,
  .upload-tip-text,
  .tips-text {
    color: #94a3b8;
  }

  .field-input {
    background: rgba(15, 23, 42, 0.7);
    border-color: #334155;
  }

  .field-placeholder {
    color: #64748b;
  }

  .tips-card {
    background: rgba(26, 87, 219, 0.12);
    border-color: rgba(26, 87, 219, 0.2);
  }

  .footer-bar {
    background: rgba(15, 23, 42, 0.82);
    border-top-color: #1e293b;
  }
}
</style>

