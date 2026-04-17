<template>
  <view class="login-page" :class="layoutClass">
    <view class="page-shell">
      <view class="decor-circle decor-top"></view>
      <view class="decor-circle decor-bottom"></view>

      <view class="content-wrap">
        <view class="capsule-space" :style="capsuleSpaceStyle"></view>

        <view class="content-main">
          <view class="brand-section">
            <view class="brand-logo">
              <view class="hub-icon">
                <view class="hub-line hub-line-left"></view>
                <view class="hub-line hub-line-right"></view>
                <view class="hub-dot hub-dot-top"></view>
                <view class="hub-dot hub-dot-left"></view>
                <view class="hub-dot hub-dot-right"></view>
              </view>
            </view>
            <text class="brand-title">欢迎来到圈脉链</text>
            <text class="brand-subtitle">构建更高效的商业脉络</text>
            <view v-if="inviteCode" class="invite-tip">
              <text class="invite-tip-text">已绑定邀请ID {{ inviteCode }}</text>
            </view>
          </view>

          <view class="form-wrap">
            <view class="mode-switch">
              <view
                class="mode-item"
                :class="{ 'mode-item-active': loginMode === 'sms' }"
                @tap="switchMode('sms')"
              >
                验证码登录
              </view>
              <view
                class="mode-item"
                :class="{ 'mode-item-active': loginMode === 'password' }"
                @tap="switchMode('password')"
              >
                密码登录
              </view>
            </view>

            <view class="field-block">
              <text class="field-label">手机号</text>
              <view class="phone-row">
                <view class="country-code-box">
                  <text class="country-code-text">+86</text>
                </view>
                <view class="field-input-wrap">
                  <input
                    v-model="phone"
                    class="field-input"
                    type="number"
                    maxlength="11"
                    placeholder="请输入手机号"
                    placeholder-class="field-placeholder"
                  />
                </view>
              </view>
            </view>

            <view class="field-block">
              <text class="field-label">{{ loginMode === 'sms' ? '验证码' : '密码' }}</text>
              <view v-if="loginMode === 'sms'" class="sms-row">
                <view class="field-input-wrap sms-input-wrap">
                  <input
                    v-model="smsCode"
                    class="field-input"
                    type="number"
                    maxlength="6"
                    placeholder="请输入验证码"
                    placeholder-class="field-placeholder"
                  />
                </view>
                <button
                  class="code-btn"
                  :class="{ 'code-btn-disabled': codeDisabled }"
                  :disabled="codeDisabled"
                  hover-class="code-btn-active"
                  @tap="onGetCode"
                >
                  {{ codeButtonText }}
                </button>
              </view>
              <view v-else class="field-input-wrap">
                <input
                  v-model="password"
                  class="field-input"
                  type="text"
                  password
                  maxlength="32"
                  placeholder="请输入密码"
                  placeholder-class="field-placeholder"
                />
              </view>
            </view>

            <view class="action-wrap">
              <button
                class="login-btn"
                :class="{ 'login-btn-loading': loginLoading }"
                :disabled="loginLoading"
                hover-class="login-btn-active"
                @tap="onSubmitLogin"
              >
                {{ loginLoading ? '登录中...' : '立即登录' }}
              </button>

              <view class="divider-wrap">
                <view class="divider-line"></view>
                <text class="divider-text">其他登录方式</text>
                <view class="divider-line"></view>
              </view>

              <button
                class="wechat-btn"
                :class="{ 'wechat-btn-disabled': wechatLoading }"
                :disabled="wechatLoading"
                hover-class="wechat-btn-active"
                @tap="onWechatLogin"
              >
                <view class="wechat-icon">
                  <view class="wechat-bubble bubble-main">
                    <view class="wechat-dot dot-1"></view>
                    <view class="wechat-dot dot-2"></view>
                    <view class="wechat-dot dot-3"></view>
                  </view>
                  <view class="wechat-bubble bubble-sub">
                    <view class="wechat-dot dot-4"></view>
                    <view class="wechat-dot dot-5"></view>
                  </view>
                </view>
                <text class="wechat-btn-text">{{ wechatLoading ? '微信登录中...' : '微信一键登录' }}</text>
              </button>
            </view>
          </view>

          <view class="agreement-wrap">
            <view class="agreement-check" :class="{ 'agreement-check-on': agreed }" @tap="toggleAgree">
              <view v-if="agreed" class="agreement-mark"></view>
            </view>
            <text class="agreement-text">
              同意圈脉链的
              <text class="agreement-link" @tap="openDoc('用户协议')">《用户协议》</text>
              和
              <text class="agreement-link" @tap="openDoc('隐私政策')">《隐私政策》</text>
              ，并授权我们使用您的基本信息为您提供服务。
            </text>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, onUnmounted, ref, watch } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { loginByPassword, loginBySmsCode, loginByWechatMiniapp, sendSmsCode } from '../../../api/auth'
import { getMiniappLoginCode, getWechatDeviceId } from '../../../utils/wechat-auth'

const { statusBarHeight = 0, windowHeight = 0 } = uni.getSystemInfoSync()
const capsuleSpaceStyle = `padding-top:${statusBarHeight}px;`
const layoutClass = windowHeight > 0 && windowHeight <= 700 ? 'layout-mini' : windowHeight <= 780 ? 'layout-compact' : 'layout-normal'

const loginMode = ref('sms')
const phone = ref('')
const smsCode = ref('')
const password = ref('')
const inviteCode = ref('')
const agreed = ref(false)
const sendingCode = ref(false)
const loginLoading = ref(false)
const wechatLoading = ref(false)
const countdown = ref(0)

let countdownTimer = null

const PHONE_REGEX = /^1\d{10}$/
const CODE_REGEX = /^\d{4,8}$/
const PASSWORD_REGEX = /^.{6,32}$/
const COUNTDOWN_SECONDS = 60
const INVITE_CODE_STORAGE_KEY = '__INVITE_CODE__'

const codeDisabled = computed(() => sendingCode.value || countdown.value > 0)
const codeButtonText = computed(() => {
  if (sendingCode.value) {
    return '发送中...'
  }
  if (countdown.value > 0) {
    return `${countdown.value}s后重试`
  }
  return '获取验证码'
})

const normalizePhone = (value) => String(value || '').replace(/\D/g, '').slice(0, 11)
const normalizeCode = (value) => String(value || '').replace(/\D/g, '').slice(0, 8)
const normalizePassword = (value) => String(value || '').slice(0, 32)
const normalizeInviteCode = (value) => String(value || '').trim().slice(0, 32)

watch(phone, (value) => {
  const nextValue = normalizePhone(value)
  if (nextValue !== value) {
    phone.value = nextValue
  }
})

watch(smsCode, (value) => {
  const nextValue = normalizeCode(value)
  if (nextValue !== value) {
    smsCode.value = nextValue
  }
})

watch(password, (value) => {
  const nextValue = normalizePassword(value)
  if (nextValue !== value) {
    password.value = nextValue
  }
})

const switchMode = (mode) => {
  if (mode !== 'sms' && mode !== 'password') {
    return
  }
  loginMode.value = mode
}

const showToast = (title) => {
  uni.showToast({
    title,
    icon: 'none'
  })
}

const ensureAgreement = () => {
  if (agreed.value) {
    return true
  }
  showToast('请先勾选用户协议与隐私政策')
  return false
}

const persistLogin = (result) => {
  uni.setStorageSync('token', result?.access_token || '')
  uni.setStorageSync('isLoggedIn', true)
  uni.setStorageSync('userInfo', result?.user_info || {})
  uni.removeStorageSync(INVITE_CODE_STORAGE_KEY)
}

const finishLoginSuccess = (toastText = '登录成功') => {
  showToast(toastText)
  setTimeout(() => {
    uni.switchTab({
      url: '/pages/tab/me/index'
    })
  }, 250)
}

const startCountdown = () => {
  if (countdownTimer) {
    clearInterval(countdownTimer)
    countdownTimer = null
  }

  countdown.value = COUNTDOWN_SECONDS
  countdownTimer = setInterval(() => {
    countdown.value -= 1
    if (countdown.value <= 0) {
      clearInterval(countdownTimer)
      countdownTimer = null
      countdown.value = 0
    }
  }, 1000)
}

const toggleAgree = () => {
  agreed.value = !agreed.value
}

const syncInviteCode = (value) => {
  const normalized = normalizeInviteCode(value)
  inviteCode.value = normalized
  if (normalized) {
    uni.setStorageSync(INVITE_CODE_STORAGE_KEY, normalized)
    return
  }
  uni.removeStorageSync(INVITE_CODE_STORAGE_KEY)
}

const onGetCode = async () => {
  if (codeDisabled.value) {
    return
  }

  const currentPhone = normalizePhone(phone.value)
  phone.value = currentPhone

  if (!PHONE_REGEX.test(currentPhone)) {
    showToast('请输入正确的手机号')
    return
  }

  sendingCode.value = true
  try {
    const result = await sendSmsCode(currentPhone)
    startCountdown()

    if (result?.debug_code) {
      smsCode.value = result.debug_code
      showToast(`验证码已发送: ${result.debug_code}`)
      return
    }
    showToast('验证码已发送')
  } catch (err) {
    showToast(err?.message || '发送失败，请稍后重试')
  } finally {
    sendingCode.value = false
  }
}

const onSubmitLogin = async () => {
  if (loginLoading.value) {
    return
  }

  const currentPhone = normalizePhone(phone.value)
  const currentCode = normalizeCode(smsCode.value)
  const currentPassword = normalizePassword(password.value)
  phone.value = currentPhone
  smsCode.value = currentCode
  password.value = currentPassword

  if (!PHONE_REGEX.test(currentPhone)) {
    showToast('请输入正确的手机号')
    return
  }

  if (!ensureAgreement()) {
    return
  }

  loginLoading.value = true
  try {
    let result
    if (loginMode.value === 'sms') {
      if (!CODE_REGEX.test(currentCode)) {
        showToast('请输入正确的验证码')
        return
      }
      result = await loginBySmsCode(currentPhone, currentCode, inviteCode.value)
    } else {
      if (!PASSWORD_REGEX.test(currentPassword)) {
        showToast('请输入6-32位密码')
        return
      }
      result = await loginByPassword(currentPhone, currentPassword, inviteCode.value)
    }
    persistLogin(result)
    finishLoginSuccess('登录成功')
  } catch (err) {
    showToast(err?.message || '登录失败，请稍后重试')
  } finally {
    loginLoading.value = false
  }
}

const onWechatLogin = async () => {
  if (wechatLoading.value) {
    return
  }

  if (!ensureAgreement()) {
    return
  }

  wechatLoading.value = true
  try {
    let code = ''
    // #ifdef MP-WEIXIN
    code = await getMiniappLoginCode()
    // #endif
    // #ifndef MP-WEIXIN
    code = `dev_wechat_${Date.now()}`
    // #endif

    const result = await loginByWechatMiniapp({
      code,
      device_id: getWechatDeviceId(),
      invite_code: inviteCode.value
    })

    persistLogin(result)
    finishLoginSuccess('微信登录成功')
  } catch (err) {
    showToast(err?.message || '微信登录失败，请稍后重试')
  } finally {
    wechatLoading.value = false
  }
}

const openDoc = (name) => {
  showToast(name)
}

onLoad((options) => {
  const queryInviteCode = normalizeInviteCode(options?.inviteCode || options?.invite_code)
  const cachedInviteCode = normalizeInviteCode(uni.getStorageSync(INVITE_CODE_STORAGE_KEY))
  syncInviteCode(queryInviteCode || cachedInviteCode)
})

onUnmounted(() => {
  if (countdownTimer) {
    clearInterval(countdownTimer)
    countdownTimer = null
  }
})
</script>

<style>
page {
  height: 100%;
  overflow: hidden;
}
</style>

<style scoped>
.login-page {
  --main-padding-top: 52rpx;
  --main-padding-x: 48rpx;
  --main-padding-bottom: 96rpx;
  --brand-section-gap: 68rpx;
  --brand-logo-size: 128rpx;
  --brand-logo-radius: 24rpx;
  --brand-logo-gap: 36rpx;
  --brand-title-size: 60rpx;
  --brand-title-line-height: 72rpx;
  --brand-subtitle-size: 34rpx;
  --brand-subtitle-line-height: 46rpx;
  --form-gap: 32rpx;
  --field-gap: 16rpx;
  --row-gap: 16rpx;
  --control-height: 100rpx;
  --country-width: 160rpx;
  --code-min-width: 178rpx;
  --action-gap: 18rpx;
  --agreement-padding-top: 32rpx;
  --agreement-bottom-gap: 60rpx;

  height: 100vh;
  overflow: hidden;
  background: #f6f6f8;
  color: #0f172a;
  font-family: 'Manrope', 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

.login-page.layout-compact {
  --main-padding-top: 36rpx;
  --main-padding-x: 36rpx;
  --main-padding-bottom: 62rpx;
  --brand-section-gap: 44rpx;
  --brand-logo-size: 112rpx;
  --brand-logo-gap: 28rpx;
  --brand-title-size: 52rpx;
  --brand-title-line-height: 62rpx;
  --brand-subtitle-size: 30rpx;
  --brand-subtitle-line-height: 40rpx;
  --form-gap: 26rpx;
  --field-gap: 12rpx;
  --row-gap: 14rpx;
  --control-height: 94rpx;
  --country-width: 148rpx;
  --code-min-width: 164rpx;
  --action-gap: 16rpx;
  --agreement-padding-top: 24rpx;
  --agreement-bottom-gap: 48rpx;
}

.login-page.layout-mini {
  --main-padding-top: 22rpx;
  --main-padding-x: 28rpx;
  --main-padding-bottom: 36rpx;
  --brand-section-gap: 24rpx;
  --brand-logo-size: 92rpx;
  --brand-logo-gap: 22rpx;
  --brand-title-size: 44rpx;
  --brand-title-line-height: 52rpx;
  --brand-subtitle-size: 26rpx;
  --brand-subtitle-line-height: 34rpx;
  --form-gap: 18rpx;
  --field-gap: 10rpx;
  --row-gap: 12rpx;
  --control-height: 86rpx;
  --country-width: 132rpx;
  --code-min-width: 150rpx;
  --action-gap: 14rpx;
  --agreement-padding-top: 16rpx;
  --agreement-bottom-gap: 34rpx;
}

.page-shell {
  position: relative;
  height: 100vh;
  overflow: hidden;
  background: #f6f6f8;
}

.content-wrap {
  position: relative;
  z-index: 2;
  height: 100vh;
  overflow: hidden;
}

.capsule-space {
  width: 100%;
  height: 96rpx;
  padding-left: 32rpx;
  padding-right: 32rpx;
}

.content-main {
  height: calc(100vh - 96rpx);
  box-sizing: border-box;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  padding: var(--main-padding-top) var(--main-padding-x) calc(var(--main-padding-bottom) + env(safe-area-inset-bottom));
}

.brand-section {
  margin-bottom: var(--brand-section-gap);
}

.invite-tip {
  margin-top: 22rpx;
  display: inline-flex;
  align-items: center;
  max-width: 100%;
  border-radius: 999rpx;
  background: rgba(26, 87, 219, 0.08);
  padding: 10rpx 20rpx;
}

.invite-tip-text {
  color: #1a57db;
  font-size: 24rpx;
  line-height: 32rpx;
  font-weight: 700;
}

.brand-logo {
  width: var(--brand-logo-size);
  height: var(--brand-logo-size);
  border-radius: var(--brand-logo-radius);
  background: #1a57db;
  box-shadow: 0 12rpx 28rpx rgba(26, 87, 219, 0.22);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: var(--brand-logo-gap);
}

.hub-icon {
  position: relative;
  width: 64rpx;
  height: 64rpx;
}

.hub-line {
  position: absolute;
  top: 50%;
  height: 4rpx;
  border-radius: 999rpx;
  background: #ffffff;
}

.hub-line-left {
  left: 13rpx;
  width: 14rpx;
  transform: translateY(-50%) rotate(32deg);
  transform-origin: left center;
}

.hub-line-right {
  right: 13rpx;
  width: 14rpx;
  transform: translateY(-50%) rotate(-32deg);
  transform-origin: right center;
}

.hub-dot {
  position: absolute;
  width: 14rpx;
  height: 14rpx;
  border-radius: 999rpx;
  background: #ffffff;
}

.hub-dot-top {
  left: 50%;
  top: 8rpx;
  transform: translateX(-50%);
}

.hub-dot-left {
  left: 8rpx;
  bottom: 10rpx;
}

.hub-dot-right {
  right: 8rpx;
  bottom: 10rpx;
}

.brand-title {
  display: block;
  color: #0f172a;
  font-size: var(--brand-title-size);
  line-height: var(--brand-title-line-height);
  font-weight: 700;
  margin-bottom: 12rpx;
  letter-spacing: 0.2rpx;
}

.brand-subtitle {
  display: block;
  color: #64748b;
  font-size: var(--brand-subtitle-size);
  line-height: var(--brand-subtitle-line-height);
}

.form-wrap {
  display: flex;
  flex-direction: column;
  gap: var(--form-gap);
}

.mode-switch {
  display: flex;
  align-items: center;
  border-radius: 20rpx;
  background: #e2e8f0;
  padding: 6rpx;
}

.mode-item {
  flex: 1;
  height: 64rpx;
  border-radius: 16rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24rpx;
  line-height: 32rpx;
  color: #64748b;
  font-weight: 600;
}

.mode-item-active {
  background: #ffffff;
  color: #1a57db;
  box-shadow: 0 2rpx 8rpx rgba(15, 23, 42, 0.08);
}

.field-block {
  display: flex;
  flex-direction: column;
  gap: var(--field-gap);
}

.field-label {
  margin-left: 8rpx;
  color: #334155;
  font-size: 22rpx;
  line-height: 30rpx;
  font-weight: 600;
}

.phone-row,
.sms-row {
  display: flex;
  gap: var(--row-gap);
  align-items: center;
}

.country-code-box {
  width: var(--country-width);
  height: var(--control-height);
  border-radius: 24rpx;
  border: 1rpx solid #e2e8f0;
  background: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
}

.country-code-text {
  color: #0f172a;
  font-size: 28rpx;
  line-height: 36rpx;
  font-weight: 500;
}

.field-input-wrap {
  flex: 1;
}

.field-input {
  width: 100%;
  height: var(--control-height);
  box-sizing: border-box;
  border-radius: 24rpx;
  border: 1rpx solid #e2e8f0;
  background: #ffffff;
  padding: 0 24rpx;
  color: #0f172a;
  font-size: 28rpx;
  line-height: 36rpx;
}

.field-placeholder {
  color: #94a3b8;
}

.sms-input-wrap {
  flex: 1;
  min-width: 0;
}

.code-btn {
  height: var(--control-height);
  min-width: var(--code-min-width);
  flex-shrink: 0;
  box-sizing: border-box;
  border-radius: 24rpx;
  background: rgba(26, 87, 219, 0.1);
  color: #1a57db;
  font-size: 26rpx;
  line-height: 34rpx;
  font-weight: 600;
  padding: 0 24rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  white-space: nowrap;
  text-overflow: clip;
}

.code-btn-active {
  opacity: 0.82;
}

.code-btn-disabled {
  opacity: 0.6;
}

.action-wrap {
  padding-top: 8rpx;
  display: flex;
  flex-direction: column;
  gap: var(--action-gap);
}

.login-btn {
  width: 100%;
  height: var(--control-height);
  border-radius: 24rpx;
  background: #1a57db;
  color: #ffffff;
  font-size: 32rpx;
  line-height: 40rpx;
  font-weight: 700;
  box-shadow: 0 10rpx 24rpx rgba(26, 87, 219, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
}

.login-btn-active {
  transform: scale(0.98);
}

.login-btn-loading {
  opacity: 0.92;
}

.divider-wrap {
  display: flex;
  align-items: center;
  padding: 10rpx 0;
}

.divider-line {
  flex: 1;
  height: 1rpx;
  background: #e2e8f0;
}

.divider-text {
  margin: 0 16rpx;
  color: #94a3b8;
  font-size: 22rpx;
  line-height: 30rpx;
}

.wechat-btn {
  width: 100%;
  height: var(--control-height);
  border-radius: 24rpx;
  border: 1rpx solid #e2e8f0;
  background: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12rpx;
}

.wechat-btn-active {
  opacity: 0.9;
}

.wechat-btn-disabled {
  opacity: 0.72;
}

.wechat-btn-text {
  color: #334155;
  font-size: 28rpx;
  line-height: 36rpx;
  font-weight: 600;
}

.wechat-icon {
  position: relative;
  width: 48rpx;
  height: 44rpx;
}

.wechat-bubble {
  position: absolute;
  border-radius: 999rpx;
  background: #07c160;
}

.bubble-main {
  left: 0;
  top: 8rpx;
  width: 30rpx;
  height: 24rpx;
}

.bubble-main::after {
  content: '';
  position: absolute;
  left: 8rpx;
  bottom: -6rpx;
  width: 8rpx;
  height: 8rpx;
  background: #07c160;
  transform: rotate(45deg);
}

.bubble-sub {
  right: 0;
  top: 0;
  width: 24rpx;
  height: 20rpx;
}

.bubble-sub::after {
  content: '';
  position: absolute;
  right: 6rpx;
  bottom: -5rpx;
  width: 7rpx;
  height: 7rpx;
  background: #07c160;
  transform: rotate(45deg);
}

.wechat-dot {
  position: absolute;
  width: 4rpx;
  height: 4rpx;
  border-radius: 999rpx;
  background: #ffffff;
}

.dot-1 {
  left: 6rpx;
  top: 10rpx;
}

.dot-2 {
  left: 12rpx;
  top: 10rpx;
}

.dot-3 {
  left: 18rpx;
  top: 10rpx;
}

.dot-4 {
  right: 10rpx;
  top: 8rpx;
}

.dot-5 {
  right: 5rpx;
  top: 8rpx;
}

.agreement-wrap {
  margin-top: auto;
  padding-top: var(--agreement-padding-top);
  padding-bottom: calc(var(--agreement-bottom-gap) + env(safe-area-inset-bottom));
  display: flex;
  align-items: flex-start;
  gap: 12rpx;
}

.agreement-check {
  margin-top: 6rpx;
  width: 28rpx;
  height: 28rpx;
  border-radius: 8rpx;
  border: 2rpx solid #cbd5e1;
  background: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.agreement-check-on {
  border-color: #1a57db;
  background: #1a57db;
}

.agreement-mark {
  width: 12rpx;
  height: 7rpx;
  border-left: 2rpx solid #ffffff;
  border-bottom: 2rpx solid #ffffff;
  transform: rotate(-45deg) translateY(-1rpx);
}

.agreement-text {
  color: #64748b;
  font-size: 24rpx;
  line-height: 36rpx;
}

.agreement-link {
  color: #1a57db;
  font-weight: 500;
}

.decor-circle {
  position: absolute;
  border-radius: 9999rpx;
  background: rgba(26, 87, 219, 0.06);
  filter: blur(56rpx);
  z-index: 1;
}

.decor-top {
  width: 512rpx;
  height: 512rpx;
  top: -256rpx;
  right: -256rpx;
}

.decor-bottom {
  width: 768rpx;
  height: 768rpx;
  left: -384rpx;
  bottom: -384rpx;
}

@media (prefers-color-scheme: dark) {
  .login-page,
  .page-shell {
    background: #111621;
    color: #f8fafc;
  }

  .brand-title {
    color: #ffffff;
  }

  .brand-subtitle {
    color: #94a3b8;
  }

  .field-label {
    color: #cbd5e1;
  }

  .country-code-box,
  .field-input,
  .wechat-btn {
    border-color: #334155;
    background: #1e293b;
  }

  .mode-switch {
    background: #1e293b;
  }

  .mode-item {
    color: #94a3b8;
  }

  .mode-item-active {
    background: #0f172a;
    color: #60a5fa;
    box-shadow: none;
  }

  .country-code-text,
  .field-input {
    color: #f8fafc;
  }

  .field-placeholder {
    color: #64748b;
  }

  .code-btn {
    background: rgba(26, 87, 219, 0.2);
    color: #60a5fa;
  }

  .divider-line {
    background: #334155;
  }

  .divider-text {
    color: #64748b;
  }

  .wechat-btn-text {
    color: #e2e8f0;
  }

  .agreement-check {
    border-color: #475569;
    background: #1e293b;
  }

  .agreement-text {
    color: #94a3b8;
  }
}
</style>
