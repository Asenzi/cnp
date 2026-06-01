<template>
  <view class="login-container">
    <!-- 背景装饰 -->
    <view class="background-layer">
      <view class="gradient-overlay"></view>
      <view class="network-decoration">
        <view class="node node-1"></view>
        <view class="node node-2"></view>
        <view class="node node-3"></view>
        <view class="connection connection-1"></view>
        <view class="connection connection-2"></view>
      </view>
    </view>

    <!-- 内容区 -->
    <view class="content-area" :style="{ paddingTop: statusBarHeight + 'px' }">
      <!-- 品牌区域 -->
      <view class="brand-section">
        <view class="logo-container">
          <view class="logo-glow"></view>
          <view class="hub-icon">
            <view class="hub-center"></view>
            <view class="hub-ring"></view>
            <view class="hub-line hub-line-1"></view>
            <view class="hub-line hub-line-2"></view>
            <view class="hub-line hub-line-3"></view>
            <view class="hub-dot hub-dot-1"></view>
            <view class="hub-dot hub-dot-2"></view>
            <view class="hub-dot hub-dot-3"></view>
          </view>
        </view>
        <text class="brand-title">圈脉链</text>
        <text class="brand-tagline">构建更高效的商业脉络</text>
      </view>

      <!-- 登录区域 -->
      <view class="login-section">
        <view class="login-card">
          <view class="card-glow"></view>

          <button
            class="wechat-login-btn"
            :class="{ 'btn-loading': isLoading }"
            :disabled="isLoading"
            hover-class="btn-hover"
            @tap="handleWechatLogin"
          >
            <view class="btn-glow"></view>
            <view class="btn-content">
              <view class="wechat-icon">
                <view class="wechat-bubble bubble-main">
                  <view class="bubble-dot dot-1"></view>
                  <view class="bubble-dot dot-2"></view>
                </view>
                <view class="wechat-bubble bubble-sub"></view>
              </view>
              <text class="btn-text">{{ isLoading ? '登录中...' : '微信一键登录' }}</text>
            </view>
            <view class="btn-shine"></view>
          </button>

          <view class="agreement-section">
            <view
              class="checkbox-wrapper"
              @tap="toggleAgreement"
            >
              <view class="checkbox" :class="{ 'checkbox-checked': agreed }">
                <view v-if="agreed" class="checkbox-mark"></view>
              </view>
              <text class="agreement-text">
                登录即表示同意
                <text class="agreement-link" @tap.stop="openAgreement('user')">《用户协议》</text>
                和
                <text class="agreement-link" @tap.stop="openAgreement('privacy')">《隐私政策》</text>
              </text>
            </view>
          </view>
        </view>
      </view>

      <!-- 底部装饰 -->
      <view class="footer-decoration">
        <view class="footer-line"></view>
        <text class="footer-text">专业 · 信任 · 价值</text>
        <view class="footer-line"></view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { loginByWechatMiniapp } from '../../../api/auth'
import { getMiniappLoginCode, getWechatDeviceId } from '../../../utils/wechat-auth'

const { statusBarHeight = 0 } = uni.getSystemInfoSync()

const agreed = ref(false)
const isLoading = ref(false)
const inviteCode = ref('')

const INVITE_CODE_STORAGE_KEY = '__INVITE_CODE__'

const showToast = (title) => {
  uni.showToast({
    title,
    icon: 'none',
    duration: 2000
  })
}

const toggleAgreement = () => {
  agreed.value = !agreed.value
}

const openAgreement = (type) => {
  const url = type === 'user'
    ? '/pages/legal/user-agreement'
    : '/pages/legal/privacy-policy'

  uni.navigateTo({ url })
}

const handleWechatLogin = async () => {
  if (isLoading.value) return

  if (!agreed.value) {
    showToast('请先同意用户协议与隐私政策')
    return
  }

  isLoading.value = true

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

    uni.setStorageSync('token', result?.access_token || '')
    uni.setStorageSync('isLoggedIn', true)
    uni.setStorageSync('userInfo', result?.user_info || {})
    uni.removeStorageSync(INVITE_CODE_STORAGE_KEY)

    showToast('登录成功')

    setTimeout(() => {
      uni.switchTab({
        url: '/pages/tab/me/index'
      })
    }, 300)
  } catch (err) {
    showToast(err?.message || '登录失败，请稍后重试')
  } finally {
    isLoading.value = false
  }
}

onLoad((options) => {
  const queryInviteCode = String(options?.inviteCode || options?.invite_code || '').trim()
  const cachedInviteCode = String(uni.getStorageSync(INVITE_CODE_STORAGE_KEY) || '').trim()
  const finalInviteCode = queryInviteCode || cachedInviteCode

  if (finalInviteCode) {
    inviteCode.value = finalInviteCode
    uni.setStorageSync(INVITE_CODE_STORAGE_KEY, finalInviteCode)
  }
})
</script>

<style scoped>
page {
  height: 100%;
  overflow: hidden;
}

.login-container {
  position: relative;
  width: 100%;
  height: 100vh;
  overflow: hidden;
}

/* ===== 背景层 ===== */
.background-layer {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 1;
}

.gradient-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(165deg, #e8f0ff 0%, #f0f5ff 20%, #fafbff 45%, #ffffff 100%);
}

.network-decoration {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  opacity: 0.4;
}

.node {
  position: absolute;
  width: 8rpx;
  height: 8rpx;
  border-radius: 50%;
  background: linear-gradient(135deg, #3b82f6 0%, #60a5fa 50%, #d4a574 100%);
  box-shadow: 0 0 20rpx rgba(59, 130, 246, 0.6);
}

.node-1 {
  top: 18%;
  left: 15%;
  animation: pulse 3s ease-in-out infinite;
}

.node-2 {
  top: 35%;
  right: 20%;
  animation: pulse 3s ease-in-out 1s infinite;
}

.node-3 {
  bottom: 25%;
  left: 25%;
  animation: pulse 3s ease-in-out 2s infinite;
}

.connection {
  position: absolute;
  height: 1rpx;
  background: linear-gradient(90deg,
    transparent 0%,
    rgba(59, 130, 246, 0.3) 50%,
    transparent 100%
  );
  transform-origin: left center;
}

.connection-1 {
  top: 18%;
  left: 15%;
  width: 280rpx;
  transform: rotate(25deg);
}

.connection-2 {
  bottom: 25%;
  left: 25%;
  width: 320rpx;
  transform: rotate(-15deg);
}

@keyframes pulse {
  0%, 100% {
    opacity: 0.4;
    transform: scale(1);
  }
  50% {
    opacity: 1;
    transform: scale(1.3);
  }
}

/* ===== 内容区 ===== */
.content-area {
  position: relative;
  z-index: 2;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: space-between;
  min-height: 100vh;
  padding: 0 48rpx;
  padding-bottom: calc(80rpx + env(safe-area-inset-bottom));
  box-sizing: border-box;
}

/* ===== 品牌区域 ===== */
.brand-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-top: 225rpx;
}

.logo-container {
  position: relative;
  width: 160rpx;
  height: 160rpx;
  margin-bottom: 48rpx;
}

.logo-glow {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 200rpx;
  height: 200rpx;
  transform: translate(-50%, -50%);
  background: radial-gradient(circle, rgba(37, 99, 235, 0.15) 0%, rgba(212, 165, 116, 0.15) 50%, transparent 70%);
  animation: glow-pulse 4s ease-in-out infinite;
}

@keyframes glow-pulse {
  0%, 100% {
    opacity: 0.5;
    transform: translate(-50%, -50%) scale(1);
  }
  50% {
    opacity: 0.8;
    transform: translate(-50%, -50%) scale(1.1);
  }
}

.hub-icon {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.hub-center {
  position: absolute;
  width: 24rpx;
  height: 24rpx;
  border-radius: 50%;
  background: linear-gradient(135deg, #2563eb 0%, #3b82f6 50%, #d4a574 100%);
  box-shadow:
    0 0 20rpx rgba(37, 99, 235, 0.5),
    0 0 40rpx rgba(37, 99, 235, 0.25);
  z-index: 3;
}

.hub-ring {
  position: absolute;
  width: 80rpx;
  height: 80rpx;
  border-radius: 50%;
  border: 2rpx solid rgba(37, 99, 235, 0.25);
  animation: ring-rotate 8s linear infinite;
}

@keyframes ring-rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.hub-line {
  position: absolute;
  width: 48rpx;
  height: 3rpx;
  background: linear-gradient(90deg,
    rgba(37, 99, 235, 0.6) 0%,
    rgba(212, 165, 116, 0.4) 50%,
    rgba(37, 99, 235, 0.2) 100%
  );
  border-radius: 2rpx;
  transform-origin: left center;
}

.hub-line-1 {
  top: 50%;
  left: 50%;
  transform: translateY(-50%) rotate(0deg);
}

.hub-line-2 {
  top: 50%;
  left: 50%;
  transform: translateY(-50%) rotate(120deg);
}

.hub-line-3 {
  top: 50%;
  left: 50%;
  transform: translateY(-50%) rotate(240deg);
}

.hub-dot {
  position: absolute;
  width: 12rpx;
  height: 12rpx;
  border-radius: 50%;
  background: linear-gradient(135deg, #2563eb 0%, #60a5fa 100%);
  box-shadow: 0 0 12rpx rgba(37, 99, 235, 0.5);
}

.hub-dot-1 {
  top: 50%;
  right: 16rpx;
  transform: translateY(-50%);
}

.hub-dot-2 {
  bottom: 28rpx;
  left: 28rpx;
}

.hub-dot-3 {
  top: 28rpx;
  left: 28rpx;
}

.brand-title {
  display: block;
  color: #1a2332;
  font-size: 64rpx;
  line-height: 72rpx;
  font-weight: 700;
  margin-bottom: 12rpx;
  letter-spacing: 0.2rpx;
}

.brand-tagline {
  display: block;
  color: #64748b;
  font-size: 28rpx;
  line-height: 40rpx;
}

/* ===== 登录区域 ===== */
.login-section {
  width: 100%;
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60rpx 0;
}

.login-card {
  position: relative;
  width: 100%;
  max-width: 560rpx;
}

.card-glow {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 120%;
  height: 140%;
  transform: translate(-50%, -50%);
  background: radial-gradient(ellipse, rgba(37, 99, 235, 0.06) 0%, rgba(212, 165, 116, 0.04) 50%, transparent 70%);
  pointer-events: none;
}

.wechat-login-btn {
  position: relative;
  width: 100%;
  height: 112rpx;
  border-radius: 56rpx;
  background: linear-gradient(135deg, #07c160 0%, #06ae56 100%);
  border: none;
  padding: 0;
  overflow: hidden;
  box-shadow:
    0 8rpx 24rpx rgba(7, 193, 96, 0.35),
    0 0 0 1rpx rgba(212, 165, 116, 0.15) inset;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.wechat-login-btn::after {
  border: none;
}

.btn-glow {
  position: absolute;
  top: -2rpx;
  left: -2rpx;
  right: -2rpx;
  bottom: -2rpx;
  border-radius: 56rpx;
  background: linear-gradient(135deg,
    rgba(37, 99, 235, 0.3) 0%,
    rgba(212, 165, 116, 0.3) 50%,
    rgba(37, 99, 235, 0.3) 100%
  );
  opacity: 0;
  transition: opacity 0.3s ease;
  pointer-events: none;
}

.btn-hover .btn-glow {
  opacity: 1;
}

.btn-content {
  position: relative;
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16rpx;
  height: 100%;
}

.wechat-icon {
  position: relative;
  width: 52rpx;
  height: 48rpx;
}

.wechat-bubble {
  position: absolute;
  border-radius: 50% 50% 50% 0;
  background: #ffffff;
}

.bubble-main {
  left: 0;
  top: 10rpx;
  width: 34rpx;
  height: 28rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6rpx;
  padding-left: 6rpx;
}

.bubble-sub {
  right: 0;
  top: 0;
  width: 26rpx;
  height: 22rpx;
}

.bubble-dot {
  width: 5rpx;
  height: 5rpx;
  border-radius: 50%;
  background: #07c160;
}

.btn-text {
  font-size: 32rpx;
  font-weight: 600;
  color: #ffffff;
  letter-spacing: 1rpx;
}

.btn-shine {
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg,
    transparent 0%,
    rgba(255, 255, 255, 0.3) 50%,
    transparent 100%
  );
  animation: shine 3s ease-in-out infinite;
}

@keyframes shine {
  0% {
    left: -100%;
  }
  50%, 100% {
    left: 100%;
  }
}

.btn-loading {
  opacity: 0.8;
}

.btn-hover {
  transform: translateY(-2rpx);
  box-shadow:
    0 12rpx 32rpx rgba(7, 193, 96, 0.45),
    0 0 0 1rpx rgba(212, 165, 116, 0.25) inset;
}

/* ===== 协议区域 ===== */
.agreement-section {
  margin-top: 40rpx;
}

.checkbox-wrapper {
  display: flex;
  align-items: flex-start;
  gap: 12rpx;
}

.checkbox {
  flex-shrink: 0;
  width: 32rpx;
  height: 32rpx;
  margin-top: 4rpx;
  border-radius: 8rpx;
  border: 2rpx solid rgba(100, 116, 139, 0.3);
  background: rgba(248, 250, 252, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
}

.checkbox-checked {
  border-color: #2563eb;
  background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%);
  box-shadow: 0 0 12rpx rgba(37, 99, 235, 0.4);
}

.checkbox-mark {
  width: 14rpx;
  height: 9rpx;
  border-left: 3rpx solid #ffffff;
  border-bottom: 3rpx solid #ffffff;
  transform: rotate(-45deg) translateY(-2rpx);
}

.agreement-text {
  flex: 1;
  font-size: 24rpx;
  line-height: 38rpx;
  color: #64748b;
  letter-spacing: 0.5rpx;
}

.agreement-link {
  color: #2563eb;
  font-weight: 500;
}

/* ===== 底部装饰 ===== */
.footer-decoration {
  display: flex;
  align-items: center;
  gap: 24rpx;
  padding-bottom: 20rpx;
}

.footer-line {
  flex: 1;
  height: 1rpx;
  background: linear-gradient(90deg,
    transparent 0%,
    rgba(37, 99, 235, 0.2) 50%,
    transparent 100%
  );
}

.footer-text {
  font-size: 22rpx;
  color: #94a3b8;
  letter-spacing: 4rpx;
  font-weight: 300;
}
</style>
