<template>
  <view class="security-page">
    <view class="page-shell">
      <view class="main-content">
        <view class="section-wrap first-section">
          <view class="section-card">
            <view
              v-for="(item, index) in securityItems"
              :key="item.key"
              class="security-row"
              :class="{ 'security-row-border': index < securityItems.length - 1 }"
              hover-class="security-row-active"
              @tap="onRowTap(item)"
            >
              <view class="row-left">
                <view class="row-icon-box">
                  <image class="row-icon" mode="aspectFit" :src="item.iconPath" />
                </view>
                <text class="row-label" :class="item.labelClass">{{ item.label }}</text>
              </view>

              <view class="row-right">
                <text v-if="item.valueText" class="row-value" :class="item.valueClass">{{ item.valueText }}</text>
                <image class="row-chevron" mode="aspectFit" src="https://cos.cnptec.site/static/me-icons/chevron-light.png" />
              </view>
            </view>
          </view>

        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { closeAccount } from '../../../api/auth'
import { getCurrentUserProfile as fetchCurrentUserProfile } from '../../../api/user'
import { disconnectRealtimeSocket } from '../../../utils/realtime'

const phoneMasked = ref('未绑定')
const closingAccount = ref(false)

const securityItems = computed(() => [
  {
    key: 'phone',
    label: '更换手机号',
    iconPath: 'https://cos.cnptec.site/static/icon/phone.png',
    valueText: phoneMasked.value
  },
  {
    key: 'close-account',
    label: '注销账号',
    iconPath: 'https://cos.cnptec.site/static/me-icons/cancel-slate.png',
    labelClass: 'row-label-danger'
  }
])

const showToast = (title) => {
  uni.showToast({
    title,
    icon: 'none'
  })
}

const maskPhone = (phone) => {
  const raw = String(phone || '').replace(/\s+/g, '')
  if (!/^\d{11}$/.test(raw)) {
    return '未绑定'
  }
  return `${raw.slice(0, 3)}****${raw.slice(7)}`
}

const loadSecurityData = async () => {
  try {
    const profile = await fetchCurrentUserProfile()
    phoneMasked.value = maskPhone(profile?.phone)
  } catch (err) {
    if (err?.statusCode === 401) {
      uni.navigateTo({
        url: '/pages/auth/login/index'
      })
      return
    }
  }
}

const onRowTap = (item) => {
  if (!item?.key) {
    return
  }

  if (item.key === 'phone') {
    uni.navigateTo({
      url: '/pages/me/security/phone/index'
    })
    return
  }

  if (item.key === 'close-account') {
    onCloseAccount()
  }
}

const onCloseAccount = () => {
  if (closingAccount.value) {
    return
  }

  uni.showModal({
    title: '注销账号',
    content: '注销后当前账号将停用，手机号和微信将解绑，历史数据将不再作为有效账号展示。',
    confirmText: '继续注销',
    cancelText: '取消',
    confirmColor: '#ef4444',
    success: (res) => {
      if (res?.confirm) {
        confirmCloseAccountAgain()
      }
    }
  })
}

const confirmCloseAccountAgain = () => {
  uni.showModal({
    title: '再次确认',
    content: '请再次确认是否注销账号。注销完成后需要重新注册或登录新账号。',
    confirmText: '确认注销',
    cancelText: '我再想想',
    confirmColor: '#ef4444',
    success: (res) => {
      if (res?.confirm) {
        submitCloseAccount()
      }
    }
  })
}

const clearLoginState = () => {
  disconnectRealtimeSocket()
  uni.removeStorageSync('token')
  uni.removeStorageSync('isLoggedIn')
  uni.removeStorageSync('userInfo')
}

const submitCloseAccount = async () => {
  closingAccount.value = true
  uni.showLoading({
    title: '注销中...',
    mask: true
  })

  try {
    await closeAccount('注销账号')
    uni.hideLoading()
    clearLoginState()
    uni.showToast({
      title: '账号已注销',
      icon: 'none'
    })
    setTimeout(() => {
      uni.switchTab({
        url: '/pages/tab/me/index'
      })
    }, 300)
  } catch (err) {
    uni.hideLoading()
    showToast(err?.message || '注销账号失败，请稍后重试')
  } finally {
    closingAccount.value = false
  }
}

onShow(() => {
  loadSecurityData()
})
</script>

<style scoped>
.security-page {
  min-height: 100vh;
  background: #f6f6f8;
  color: #0f172a;
}

.page-shell {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.main-content {
  flex: 1;
}

.section-wrap {
  margin-top: 32rpx;
  padding: 0 32rpx;
  box-sizing: border-box;
}

.first-section {
  margin-top: 32rpx;
}

.section-card {
  border-radius: 20rpx;
  overflow: hidden;
  background: #ffffff;
  border: 1rpx solid #f1f5f9;
  box-shadow: 0 4rpx 16rpx rgba(15, 23, 42, 0.04);
}

.security-row {
  min-height: 112rpx;
  padding: 20rpx 28rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-sizing: border-box;
  transition: background-color 0.2s ease;
}

.security-row-border {
  border-bottom: 1rpx solid #f8fafc;
}

.security-row-active {
  background: #f8fafc;
}

.row-left {
  display: flex;
  align-items: center;
  gap: 24rpx;
  min-width: 0;
  flex: 1;
}

.row-icon-box {
  width: 64rpx;
  height: 64rpx;
  border-radius: 16rpx;
  background: rgba(26, 87, 219, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.row-icon {
  width: 32rpx;
  height: 32rpx;
}

.row-label {
  font-size: 28rpx;
  font-weight: 600;
  color: #0f172a;
}

.row-label-danger {
  color: #ef4444;
}

.row-right {
  display: flex;
  align-items: center;
  gap: 12rpx;
  flex-shrink: 0;
}

.row-value {
  font-size: 24rpx;
  color: #64748b;
  font-weight: 500;
}

.row-value-primary {
  color: #1a57db;
  font-weight: 600;
}

.row-chevron {
  width: 28rpx;
  height: 28rpx;
  opacity: 0.5;
}

.tip-wrap {
  margin-top: 32rpx;
  padding: 24rpx 28rpx;
  border-radius: 20rpx;
  border: 1rpx solid rgba(26, 87, 219, 0.1);
  background: rgba(26, 87, 219, 0.05);
}

.tip-title {
  display: block;
  margin-bottom: 8rpx;
  font-size: 24rpx;
  font-weight: 700;
  color: #1a57db;
}

.tip-text {
  display: block;
  font-size: 22rpx;
  line-height: 1.6;
  color: #475569;
}

.footer-wrap {
  margin-top: auto;
  padding: 64rpx 32rpx calc(48rpx + env(safe-area-inset-bottom));
  display: flex;
  flex-direction: column;
  align-items: center;
}

.close-btn {
  padding: 16rpx 32rpx;
  border-radius: 16rpx;
}

.close-btn-active {
  background: rgba(239, 68, 68, 0.08);
}

.close-text {
  font-size: 24rpx;
  font-weight: 500;
  color: #94a3b8;
}

.brand-text {
  margin-top: 24rpx;
  font-size: 18rpx;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: #cbd5e1;
  opacity: 0.6;
}

@media (prefers-color-scheme: dark) {
  .security-page {
    background: #111621;
    color: #f1f5f9;
  }

  .section-card {
    background: #0f172a;
    border-color: #1e293b;
    box-shadow: none;
  }

  .security-row-border {
    border-bottom-color: #1e293b;
  }

  .security-row-active {
    background: #1e293b;
  }

  .row-label {
    color: #f1f5f9;
  }

  .row-value,
  .close-text,
  .brand-text {
    color: #94a3b8;
  }

  .row-icon-box {
    background: rgba(26, 87, 219, 0.18);
  }

  .tip-wrap {
    border-color: rgba(26, 87, 219, 0.22);
    background: rgba(26, 87, 219, 0.12);
  }

  .tip-text {
    color: #94a3b8;
  }
}
</style>
