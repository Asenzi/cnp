<template>
  <view class="realname-page">
    <view class="page-shell">
      <scroll-view class="main-scroll" scroll-y :show-scrollbar="false">
        <view class="main-content">
          <view class="form-wrap">
            <view class="field-item">
              <text class="field-label">真实姓名</text>
              <input
                v-model="realName"
                class="field-input"
                maxlength="32"
                :disabled="isApproved || loading"
                placeholder="请输入您的真实姓名"
                placeholder-class="field-placeholder"
              />
            </view>

            <view class="field-item">
              <text class="field-label">身份证号</text>
              <input
                v-model="idNumber"
                class="field-input"
                maxlength="18"
                :disabled="isApproved || loading"
                placeholder="请输入18位身份证号码"
                placeholder-class="field-placeholder"
              />
            </view>

            <view class="field-item">
              <text class="field-label">微信号</text>
              <input
                v-model="wechatId"
                class="field-input"
                maxlength="50"
                :disabled="hasContactInfo || loading"
                placeholder="请输入您的微信号"
                placeholder-class="field-placeholder"
              />
              <text v-if="hasContactInfo" class="field-hint">联系方式提交后不可修改</text>
            </view>

            <view class="field-item">
              <text class="field-label">手机号</text>
              <input
                v-model="phoneNumber"
                class="field-input"
                type="number"
                maxlength="11"
                :disabled="hasContactInfo || loading"
                placeholder="请输入您的手机号"
                placeholder-class="field-placeholder"
              />
              <text v-if="hasContactInfo" class="field-hint">联系方式提交后不可修改</text>
            </view>
          </view>

          <view class="status-card">
            <view class="status-head">
              <text class="status-title">当前状态</text>
              <text class="status-tag" :class="statusTagClass">{{ statusText }}</text>
            </view>
            <text class="status-desc">{{ statusDesc }}</text>
            <view v-if="verificationProvider" class="meta-row">
              <text class="meta-label">认证通道</text>
              <text class="meta-value">{{ verificationProviderText }}</text>
            </view>
            <view v-if="maskedIdNumber" class="meta-row">
              <text class="meta-label">实名证件</text>
              <text class="meta-value">{{ maskedIdNumber }}</text>
            </view>
          </view>

          <view v-if="hasPendingSession" class="action-card">
            <text class="action-title">继续完成核身</text>
            <text class="action-desc">
              已为您创建核身会话。完成腾讯云实人核身后，回到本页点击“我已完成核身”即可更新认证结果。
            </text>
            <view class="tip-list">
              <text class="tip-item">1. 请确保姓名与身份证号填写一致。</text>
              <text class="tip-item">2. 仅当腾讯云核身成功时，平台才会完成实名认证。</text>
              <text class="tip-item">3. 若同一身份已被其他账号绑定，系统会直接拒绝。</text>
            </view>
          </view>

          <view v-if="rejectReason" class="reject-wrap">
            <text class="reject-text">失败原因：{{ rejectReason }}</text>
          </view>
        </view>
      </scroll-view>

      <view class="footer-bar">
        <view
          class="submit-btn"
          :class="{ 'submit-btn-disabled': isPrimaryDisabled }"
          hover-class="submit-btn-hover"
          @tap="onPrimaryAction"
        >
          <text class="submit-text">{{ primaryButtonText }}</text>
        </view>

        <view
          v-if="showSecondaryButton"
          class="secondary-btn"
          hover-class="secondary-btn-hover"
          @tap="openVerificationPage"
        >
          <text class="secondary-text">继续前往腾讯云核身</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import {
  finishTencentRealNameVerification,
  getRealNameVerificationDetail,
  startTencentRealNameVerification
} from '../../../../api/verification'

const VERIFICATION_STATUS = {
  NOT_SUBMITTED: 'not_submitted',
  PENDING: 'pending',
  APPROVED: 'approved',
  REJECTED: 'rejected'
}

const STORAGE_KEYS = {
  token: 'realname_tencent_pending_biz_token',
  redirectUrl: 'realname_tencent_pending_redirect_url'
}

const loading = ref(false)
const starting = ref(false)
const finishing = ref(false)

const currentStatus = ref(VERIFICATION_STATUS.NOT_SUBMITTED)
const rejectReason = ref('')
const verificationProvider = ref('')
const verifiedSource = ref('')

const realName = ref('')
const idNumber = ref('')
const wechatId = ref('')
const phoneNumber = ref('')
const maskedIdNumber = ref('')
const pendingBizToken = ref('')
const pendingRedirectUrl = ref('')

const isApproved = computed(() => currentStatus.value === VERIFICATION_STATUS.APPROVED)
const hasContactInfo = computed(() => {
  return Boolean(
    (wechatId.value && String(wechatId.value).trim()) ||
    (phoneNumber.value && String(phoneNumber.value).trim())
  ) && currentStatus.value !== VERIFICATION_STATUS.NOT_SUBMITTED
})
const hasPendingSession = computed(() => Boolean(pendingBizToken.value) && !isApproved.value)
const showSecondaryButton = computed(() => hasPendingSession.value && Boolean(pendingRedirectUrl.value))

const statusText = computed(() => {
  if (currentStatus.value === VERIFICATION_STATUS.APPROVED) {
    return '已认证'
  }
  if (currentStatus.value === VERIFICATION_STATUS.PENDING) {
    return '核身进行中'
  }
  if (currentStatus.value === VERIFICATION_STATUS.REJECTED) {
    return '认证失败'
  }
  return '未开始'
})

const statusTagClass = computed(() => {
  if (currentStatus.value === VERIFICATION_STATUS.APPROVED) {
    return 'status-tag-success'
  }
  if (currentStatus.value === VERIFICATION_STATUS.PENDING) {
    return 'status-tag-pending'
  }
  if (currentStatus.value === VERIFICATION_STATUS.REJECTED) {
    return 'status-tag-danger'
  }
  return 'status-tag-default'
})

const statusDesc = computed(() => {
  if (currentStatus.value === VERIFICATION_STATUS.APPROVED) {
    return '您的实名认证已经完成，可以正常使用实名相关能力。'
  }
  if (hasPendingSession.value) {
    return '请先在腾讯云页面完成人脸/活体核身，完成后返回这里更新结果。'
  }
  if (currentStatus.value === VERIFICATION_STATUS.REJECTED) {
    return '请核对身份信息后重新发起腾讯云实名认证。'
  }
  return '填写身份信息后，系统会拉起腾讯云实人核身流程。'
})

const verificationProviderText = computed(() => {
  if (verificationProvider.value === 'tencent_cloud') {
    return '腾讯云实人核身'
  }
  return verificationProvider.value || '--'
})

const primaryButtonText = computed(() => {
  if (starting.value) {
    return '正在创建会话...'
  }
  if (finishing.value) {
    return '正在查询结果...'
  }
  if (isApproved.value) {
    return '已完成实名认证'
  }
  if (hasPendingSession.value) {
    return '我已完成核身'
  }
  return '开始实名认证'
})

const isPrimaryDisabled = computed(() => loading.value || starting.value || finishing.value || isApproved.value)

const showToast = (title) => {
  uni.showToast({
    title,
    icon: 'none'
  })
}

const persistPendingSession = ({ providerBizToken = '', redirectUrl = '' } = {}) => {
  pendingBizToken.value = String(providerBizToken || '').trim()
  pendingRedirectUrl.value = String(redirectUrl || '').trim()
  if (pendingBizToken.value) {
    uni.setStorageSync(STORAGE_KEYS.token, pendingBizToken.value)
  } else {
    uni.removeStorageSync(STORAGE_KEYS.token)
  }
  if (pendingRedirectUrl.value) {
    uni.setStorageSync(STORAGE_KEYS.redirectUrl, pendingRedirectUrl.value)
  } else {
    uni.removeStorageSync(STORAGE_KEYS.redirectUrl)
  }
}

const restorePendingSession = () => {
  pendingBizToken.value = String(uni.getStorageSync(STORAGE_KEYS.token) || '').trim()
  pendingRedirectUrl.value = String(uni.getStorageSync(STORAGE_KEYS.redirectUrl) || '').trim()
}

const clearPendingSession = () => {
  persistPendingSession({
    providerBizToken: '',
    redirectUrl: ''
  })
}

const openVerificationPage = () => {
  const targetUrl = String(pendingRedirectUrl.value || '').trim()
  if (!targetUrl) {
    showToast('当前没有可继续的核身会话')
    return
  }
  uni.navigateTo({
    url: `/pages/common/webview/index?title=${encodeURIComponent('腾讯云实名认证')}&url=${encodeURIComponent(targetUrl)}`
  })
}

const validateIdentityInput = () => {
  const normalizedName = String(realName.value || '').trim()
  if (!normalizedName) {
    return '请输入真实姓名'
  }
  const normalizedId = String(idNumber.value || '').trim().toUpperCase()
  if (!/^\d{17}[\dX]$|^\d{15}$/.test(normalizedId)) {
    return '身份证号码格式不正确'
  }
  const normalizedWechat = String(wechatId.value || '').trim()
  if (!normalizedWechat) {
    return '请输入微信号'
  }
  const normalizedPhone = String(phoneNumber.value || '').trim()
  if (!normalizedPhone) {
    return '请输入手机号'
  }
  if (!/^1[3-9]\d{9}$/.test(normalizedPhone)) {
    return '手机号格式不正确'
  }
  return ''
}

const loadRealNameDetail = async () => {
  if (loading.value) {
    return
  }

  loading.value = true
  try {
    const detail = await getRealNameVerificationDetail()
    currentStatus.value = detail?.status || VERIFICATION_STATUS.NOT_SUBMITTED
    rejectReason.value = detail?.reject_reason || ''
    verificationProvider.value = String(detail?.verification_provider || '').trim()
    verifiedSource.value = String(detail?.verified_source || '').trim()
    realName.value = String(detail?.real_name || '').trim()
    maskedIdNumber.value = String(detail?.id_number_masked || '').trim()
    idNumber.value = isApproved.value
      ? maskedIdNumber.value
      : String(detail?.id_number || '').trim()
    wechatId.value = String(detail?.wechat_id || '').trim()
    phoneNumber.value = String(detail?.phone_number || '').trim()

    if (isApproved.value) {
      clearPendingSession()
    } else {
      restorePendingSession()
    }
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

const startVerification = async () => {
  const validateMessage = validateIdentityInput()
  if (validateMessage) {
    showToast(validateMessage)
    return
  }

  starting.value = true
  try {
    const data = await startTencentRealNameVerification({
      real_name: String(realName.value || '').trim(),
      id_number: String(idNumber.value || '').trim().toUpperCase(),
      wechat_id: String(wechatId.value || '').trim(),
      phone_number: String(phoneNumber.value || '').trim()
    })

    // 二要素验证是同步的，直接完成认证
    currentStatus.value = VERIFICATION_STATUS.PENDING
    verificationProvider.value = String(data?.provider || 'tencent_cloud').trim()
    maskedIdNumber.value = String(data?.id_number_masked || '').trim()
    persistPendingSession({
      providerBizToken: String(data?.provider_biz_token || '').trim(),
      redirectUrl: ''  // 二要素验证不需要跳转
    })

    // 直接调用完成接口
    showToast('正在验证身份信息...')
    setTimeout(() => {
      finishVerification()
    }, 500)
  } catch (err) {
    showToast(err?.message || '实名认证发起失败')
  } finally {
    starting.value = false
  }
}

const finishVerification = async () => {
  if (!pendingBizToken.value) {
    showToast('请先发起实名认证')
    return
  }

  finishing.value = true
  try {
    const data = await finishTencentRealNameVerification({
      provider_biz_token: pendingBizToken.value
    })
    currentStatus.value = data?.status || VERIFICATION_STATUS.PENDING
    maskedIdNumber.value = String(data?.id_number_masked || '').trim()
    realName.value = String(data?.real_name || '').trim()
    verificationProvider.value = String(data?.provider || 'tencent_cloud').trim()
    if (data?.is_verified) {
      clearPendingSession()
      showToast('实名认证已完成')
      setTimeout(() => {
        uni.redirectTo({
          url: '/pages/me/auth/result/index?type=real_name&status=approved'
        })
      }, 220)
      return
    }
    showToast('实名认证未通过，请重新发起')
    await loadRealNameDetail()
  } catch (err) {
    showToast(err?.message || '认证结果查询失败')
  } finally {
    finishing.value = false
  }
}

const onPrimaryAction = () => {
  if (isPrimaryDisabled.value) {
    return
  }
  if (hasPendingSession.value) {
    finishVerification()
    return
  }
  startVerification()
}

onShow(() => {
  loadRealNameDetail()
})
</script>

<style scoped>
.realname-page {
  min-height: 100vh;
  background: #f6f6f8;
}

.page-shell {
  min-height: 100vh;
  width: 100%;
  max-width: 448px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  background: #ffffff;
}

.main-scroll {
  flex: 1;
  padding-bottom: 160rpx;
  box-sizing: border-box;
}

.main-content {
  padding: 32rpx;
  box-sizing: border-box;
}

.status-card,
.action-card {
  padding: 28rpx;
  border-radius: 20rpx;
  box-sizing: border-box;
}

.form-wrap {
  display: flex;
  flex-direction: column;
  gap: 24rpx;
  margin-top: 0;
}

.field-item {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.field-label {
  color: #0f172a;
  font-size: 28rpx;
  font-weight: 600;
}

.field-input {
  height: 88rpx;
  border-radius: 20rpx;
  background: #f8fafc;
  border: 2rpx solid #e2e8f0;
  padding: 0 24rpx;
  color: #0f172a;
  font-size: 28rpx;
  box-sizing: border-box;
}

.field-placeholder {
  color: #94a3b8;
}

.field-hint {
  color: #f59e0b;
  font-size: 22rpx;
  line-height: 1.5;
  margin-top: -8rpx;
}

.status-card,
.action-card {
  margin-top: 32rpx;
  background: #f8fafc;
  border: 2rpx solid #e2e8f0;
}

.status-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20rpx;
}

.status-title,
.action-title {
  color: #0f172a;
  font-size: 30rpx;
  font-weight: 700;
}

.status-tag {
  min-width: 120rpx;
  height: 52rpx;
  padding: 0 20rpx;
  border-radius: 999rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22rpx;
  font-weight: 700;
  box-sizing: border-box;
}

.status-tag-default {
  color: #475569;
  background: #e2e8f0;
}

.status-tag-pending {
  color: #1d4ed8;
  background: rgba(37, 99, 235, 0.12);
}

.status-tag-success {
  color: #047857;
  background: rgba(16, 185, 129, 0.14);
}

.status-tag-danger {
  color: #b91c1c;
  background: rgba(239, 68, 68, 0.14);
}

.status-desc,
.action-desc {
  display: block;
  margin-top: 16rpx;
  color: #64748b;
  font-size: 26rpx;
  line-height: 1.6;
}

.meta-row {
  margin-top: 20rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20rpx;
}

.meta-label {
  color: #64748b;
  font-size: 24rpx;
}

.meta-value {
  color: #0f172a;
  font-size: 24rpx;
  font-weight: 600;
}

.tip-list {
  margin-top: 20rpx;
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.tip-item {
  color: #475569;
  font-size: 24rpx;
  line-height: 1.6;
}

.reject-wrap {
  margin-top: 32rpx;
  padding: 24rpx 28rpx;
  border-radius: 20rpx;
  background: rgba(239, 68, 68, 0.08);
  border: 2rpx solid rgba(239, 68, 68, 0.16);
}

.reject-text {
  color: #b91c1c;
  font-size: 24rpx;
  line-height: 1.6;
}

.footer-bar {
  padding: 24rpx 32rpx calc(24rpx + env(safe-area-inset-bottom));
  border-top: 2rpx solid #e2e8f0;
  background: rgba(255, 255, 255, 0.94);
  backdrop-filter: blur(8px);
}

.submit-btn,
.secondary-btn {
  width: 100%;
  border-radius: 20rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
}

.submit-btn {
  height: 88rpx;
  background: #1a57db;
  box-shadow: 0 8rpx 20rpx rgba(26, 87, 219, 0.18);
}

.submit-btn-hover {
  background: rgba(26, 87, 219, 0.9);
}

.submit-btn-disabled {
  background: #cbd5e1;
  box-shadow: none;
}

.submit-text {
  color: #ffffff;
  font-size: 30rpx;
  font-weight: 700;
}

.secondary-btn {
  height: 80rpx;
  margin-top: 20rpx;
  border: 2rpx solid #cbd5e1;
  background: #ffffff;
}

.secondary-btn-hover {
  background: #f8fafc;
}

.secondary-text {
  color: #0f172a;
  font-size: 28rpx;
  font-weight: 600;
}
</style>
