<template>
  <view class="enterprise-page">
    <view class="page-shell">
      <scroll-view class="main-scroll" scroll-y :show-scrollbar="false">
        <view class="main-content">
          <view class="section-head">
            <text class="section-title">基本信息</text>
            <text class="section-desc">请填写您目前供职的真实企业及职位信息</text>
          </view>

          <view class="form-list">
            <view class="field-item">
              <text class="field-label">企业名称</text>
              <input
                v-model="companyName"
                class="field-input"
                maxlength="128"
                :disabled="isReadOnly"
                placeholder="请输入营业执照上的完整名称"
                placeholder-class="field-placeholder"
              />
            </view>

            <view class="field-item">
              <text class="field-label">职位</text>
              <input
                v-model="jobTitle"
                class="field-input"
                maxlength="64"
                :disabled="isReadOnly"
                placeholder="请输入您的当前职位"
                placeholder-class="field-placeholder"
              />
            </view>
          </view>

          <view class="section-head section-head-gap">
            <text class="section-title">资质证明</text>
            <text class="section-desc">请上传清晰的营业执照扫描件或照片</text>
          </view>

          <view
            class="upload-panel"
            :class="{ 'upload-panel-readonly': isReadOnly }"
            hover-class="upload-panel-hover"
            @tap="onPickLicense"
          >
            <view class="upload-content">
              <view class="upload-icon-wrap">
                <image class="upload-icon" mode="aspectFit" src="/static/me-icons/upload-primary.png" />
              </view>
              <text class="upload-title">{{ uploading ? '上传中...' : '点击上传营业执照' }}</text>
              <text class="upload-subtitle">支持 JPG, PNG, PDF (最大 10MB)</text>
            </view>

            <view class="sample-wrap">
              <view class="sample-preview">
                <image
                  class="sample-image"
                  mode="aspectFill"
                  src="https://lh3.googleusercontent.com/aida-public/AB6AXuAUWBwjXrbBEFP2QeoQyfrLn1Qe5HEWcjEqoNyvkK-gmFNVSnB5WnNUYMxXiqsq1XMK7gZ7j15g-Ech04iiEGLsNHhodhnoYgyvb8Ub5N5q-Vs1ESv82fqm0zg1RmbDhboN-25IxKCBvn_7qkfjjdFv40Di14TCHICcatWm-uu5k-YPKZnqctxcgNjdHGygsCw0MgevClIIASzTXUz8FIn_kvgsefVW82BLqe1Y_DS8mZhxzwi1t5-f9XmMrqlpLSYdkqUs_GbHkaHW"
                />
                <view class="sample-mask">
                  <text class="sample-tag">示例图</text>
                </view>
              </view>
            </view>
          </view>

          <view v-if="licenseName" class="license-file">
            <image class="license-file-icon" mode="aspectFit" src="/static/me-icons/image-primary.png" />
            <view class="license-file-meta">
              <text class="license-file-name">{{ licenseName }}</text>
              <text class="license-file-size">{{ licenseSizeText }}</text>
            </view>
          </view>

          <view v-if="rejectReason" class="reject-row">
            <text class="reject-text">驳回原因：{{ rejectReason }}</text>
          </view>

          <view class="tips-row">
            <image class="tips-icon" mode="aspectFit" src="/static/me-icons/shield-person-primary.png" />
            <view class="tips-text-wrap">
              <text class="tips-text">
                您的个人信息仅用于企业认证核实，平台将严格保护您的隐私安全。认证申请通常会在
                <text class="tips-highlight">1-3 个工作日</text> 内完成审核，请保持关注。
              </text>
            </view>
          </view>
        </view>
      </scroll-view>

      <view class="footer-bar">
        <view
          class="submit-btn"
          :class="{ 'submit-btn-disabled': isReadOnly || submitting }"
          hover-class="submit-btn-hover"
          @tap="onSubmit"
        >
          <text class="submit-text">{{ submitText }}</text>
          <text class="submit-arrow">></text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import {
  getMyVerificationOverview,
  submitEnterpriseVerification,
  uploadEnterpriseLicense
} from '../../../../api/verification'

const VERIFICATION_STATUS = {
  NOT_SUBMITTED: 'not_submitted',
  PENDING: 'pending',
  APPROVED: 'approved',
  REJECTED: 'rejected'
}

const loading = ref(false)
const submitting = ref(false)
const uploading = ref(false)

const currentStatus = ref(VERIFICATION_STATUS.NOT_SUBMITTED)
const rejectReason = ref('')

const companyName = ref('')
const jobTitle = ref('')
const licenseUrl = ref('')
const licenseName = ref('')
const licenseSize = ref(0)

const isReadOnly = computed(
  () => currentStatus.value === VERIFICATION_STATUS.PENDING || currentStatus.value === VERIFICATION_STATUS.APPROVED
)

const submitText = computed(() => {
  if (submitting.value) {
    return '提交中'
  }
  if (currentStatus.value === VERIFICATION_STATUS.PENDING) {
    return '审核中'
  }
  if (currentStatus.value === VERIFICATION_STATUS.APPROVED) {
    return '已通过'
  }
  return '提交申请'
})

const licenseSizeText = computed(() => {
  if (!licenseSize.value) {
    return ''
  }
  const mb = licenseSize.value / (1024 * 1024)
  if (mb >= 1) {
    return `${mb.toFixed(1)} MB`
  }
  const kb = Math.max(1, Math.round(licenseSize.value / 1024))
  return `${kb} KB`
})

const showToast = (title) => {
  uni.showToast({
    title,
    icon: 'none'
  })
}

const loadEnterpriseStatus = async () => {
  if (loading.value) {
    return
  }

  loading.value = true
  try {
    const overview = await getMyVerificationOverview()
    const items = Array.isArray(overview?.items) ? overview.items : []
    const enterprise = items.find((item) => item?.type === 'enterprise')

    currentStatus.value = enterprise?.status || VERIFICATION_STATUS.NOT_SUBMITTED
    rejectReason.value = enterprise?.reject_reason || ''
  } catch (err) {
    if (err?.statusCode === 401) {
      showToast('请先登录')
      setTimeout(() => {
        uni.navigateTo({
          url: '/pages/auth/login/index'
        })
      }, 200)
      return
    }
    showToast(err?.message || '加载认证状态失败')
  } finally {
    loading.value = false
  }
}

const onPickLicense = () => {
  if (isReadOnly.value || uploading.value) {
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

      uploading.value = true
      try {
        const uploaded = await uploadEnterpriseLicense(file.path, file.name || '营业执照')
        licenseUrl.value = String(uploaded?.url || '')
        licenseName.value = String(uploaded?.name || file.name || '营业执照')
        licenseSize.value = Number(uploaded?.size || file.size || 0)
        showToast('营业执照上传成功')
      } catch (err) {
        showToast(err?.message || '上传失败，请重试')
      } finally {
        uploading.value = false
      }
    }
  })
}

const onSubmit = async () => {
  if (isReadOnly.value || submitting.value) {
    return
  }

  if (!String(companyName.value || '').trim()) {
    showToast('请输入企业名称')
    return
  }
  if (!String(jobTitle.value || '').trim()) {
    showToast('请输入职位')
    return
  }
  if (!String(licenseUrl.value || '').trim()) {
    showToast('请上传营业执照')
    return
  }

  submitting.value = true
  try {
    await submitEnterpriseVerification({
      company_name: String(companyName.value || '').trim(),
      job_title: String(jobTitle.value || '').trim(),
      license_file_url: String(licenseUrl.value || '').trim()
    })
    showToast('企业认证资料已提交审核')
    setTimeout(() => {
      uni.redirectTo({
        url: '/pages/me/auth/result/index?type=enterprise'
      })
    }, 260)
  } catch (err) {
    showToast(err?.message || '提交失败，请稍后重试')
  } finally {
    submitting.value = false
  }
}

onShow(() => {
  loadEnterpriseStatus()
})
</script>

<style scoped>
.enterprise-page {
  min-height: 100vh;
  background: #f6f6f8;
}

.page-shell {
  position: relative;
  min-height: 100vh;
  max-width: 750rpx;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  background: #f6f6f8;
}

.main-scroll {
  flex: 1;
  padding-bottom: 180rpx;
}

.main-content {
  padding: 24rpx 24rpx 0;
  box-sizing: border-box;
}

.section-head {
  margin-bottom: 26rpx;
}

.section-head-gap {
  margin-top: 52rpx;
}

.section-title {
  display: block;
  margin-bottom: 8rpx;
  font-size: 40rpx;
  line-height: 1.25;
  font-weight: 700;
  color: #0f172a;
}

.section-desc {
  display: block;
  font-size: 24rpx;
  line-height: 1.6;
  color: #64748b;
}

.form-list {
  display: flex;
  flex-direction: column;
  gap: 24rpx;
}

.field-item {
  display: flex;
  flex-direction: column;
}

.field-label {
  padding-bottom: 12rpx;
  font-size: 24rpx;
  font-weight: 600;
  color: #334155;
}

.field-input {
  display: block;
  width: 100%;
  height: 88rpx;
  padding: 0 24rpx;
  border: 1rpx solid #e2e8f0;
  border-radius: 20rpx;
  background: #ffffff;
  font-size: 30rpx;
  color: #0f172a;
  box-sizing: border-box;
}

.field-input:focus {
  border-color: #1a57db;
  box-shadow: 0 0 0 1rpx #1a57db;
}

.field-placeholder {
  color: #94a3b8;
}

.upload-panel {
  width: 100%;
  border: 2rpx dashed #e2e8f0;
  border-radius: 24rpx;
  background: #ffffff;
  overflow: hidden;
  box-sizing: border-box;
}

.upload-panel-hover {
  border-color: rgba(26, 87, 219, 0.5);
}

.upload-panel-readonly {
  opacity: 0.7;
}

.upload-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 32rpx 24rpx 16rpx;
  box-sizing: border-box;
}

.upload-icon-wrap {
  width: 96rpx;
  height: 96rpx;
  border-radius: 999rpx;
  background: rgba(26, 87, 219, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16rpx;
}

.upload-icon {
  width: 56rpx;
  height: 56rpx;
}

.upload-title {
  font-size: 30rpx;
  font-weight: 700;
  color: #0f172a;
  margin-bottom: 6rpx;
}

.upload-subtitle {
  font-size: 22rpx;
  color: #94a3b8;
}

.sample-wrap {
  margin-top: 12rpx;
  padding: 0 30rpx 26rpx;
}

.sample-preview {
  position: relative;
  height: 180rpx;
  border-radius: 12rpx;
  border: 1rpx solid #f1f5f9;
  background: #f8fafc;
  overflow: hidden;
  opacity: 0.4;
}

.sample-image {
  width: 100%;
  height: 100%;
}

.sample-mask {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.sample-tag {
  padding: 4rpx 14rpx;
  border-radius: 8rpx;
  background: rgba(255, 255, 255, 0.9);
  font-size: 18rpx;
  font-weight: 700;
  letter-spacing: 1rpx;
  color: #0f172a;
}

.license-file {
  margin-top: 20rpx;
  display: flex;
  align-items: center;
  gap: 14rpx;
  padding: 16rpx 18rpx;
  border-radius: 14rpx;
  border: 1rpx solid rgba(26, 87, 219, 0.2);
  background: rgba(26, 87, 219, 0.05);
}

.license-file-icon {
  width: 36rpx;
  height: 36rpx;
}

.license-file-meta {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2rpx;
}

.license-file-name {
  font-size: 24rpx;
  font-weight: 600;
  color: #0f172a;
}

.license-file-size {
  font-size: 20rpx;
  color: #64748b;
}

.reject-row {
  margin-top: 14rpx;
}

.reject-text {
  font-size: 22rpx;
  color: #dc2626;
  line-height: 1.5;
}

.tips-row {
  margin-top: 32rpx;
  display: flex;
  gap: 10rpx;
}

.tips-icon {
  width: 34rpx;
  height: 34rpx;
  flex-shrink: 0;
  margin-top: 2rpx;
}

.tips-text-wrap {
  flex: 1;
}

.tips-text {
  font-size: 22rpx;
  line-height: 1.7;
  color: #64748b;
}

.tips-highlight {
  color: #1a57db;
  font-weight: 700;
}

.footer-bar {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  max-width: 750rpx;
  margin: 0 auto;
  padding: 16rpx 24rpx calc(16rpx + env(safe-area-inset-bottom));
  border-top: 1rpx solid #f1f5f9;
  backdrop-filter: blur(12rpx);
  background: rgba(255, 255, 255, 0.82);
  box-sizing: border-box;
}

.submit-btn {
  width: 100%;
  height: 88rpx;
  border-radius: 20rpx;
  background: #1a57db;
  box-shadow: 0 12rpx 26rpx rgba(26, 87, 219, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8rpx;
  box-sizing: border-box;
}

.submit-btn-hover {
  background: rgba(26, 87, 219, 0.9);
}

.submit-btn-disabled {
  background: #94a3b8;
  box-shadow: none;
}

.submit-text {
  font-size: 30rpx;
  font-weight: 700;
  color: #ffffff;
}

.submit-arrow {
  font-size: 28rpx;
  color: #ffffff;
  font-weight: 700;
}

@media (prefers-color-scheme: dark) {
  .enterprise-page,
  .page-shell {
    background: #111621;
  }

  .section-title,
  .upload-title,
  .field-label,
  .license-file-name {
    color: #f1f5f9;
  }

  .section-desc,
  .tips-text,
  .upload-subtitle,
  .license-file-size {
    color: #94a3b8;
  }

  .field-input,
  .upload-panel {
    border-color: #334155;
    background: rgba(15, 23, 42, 0.6);
    color: #f1f5f9;
  }

  .field-placeholder {
    color: #64748b;
  }

  .sample-preview {
    border-color: #334155;
    background: #0f172a;
  }

  .sample-tag {
    background: rgba(15, 23, 42, 0.75);
    color: #e2e8f0;
  }

  .license-file {
    border-color: rgba(26, 87, 219, 0.3);
    background: rgba(26, 87, 219, 0.12);
  }

  .footer-bar {
    border-top-color: #334155;
    background: rgba(17, 22, 33, 0.85);
  }
}
</style>

