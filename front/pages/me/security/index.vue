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
                <text class="row-label">{{ item.label }}</text>
              </view>

              <view class="row-right">
                <text v-if="item.valueText" class="row-value" :class="item.valueClass">{{ item.valueText }}</text>
                <image class="row-chevron" mode="aspectFit" src="/static/me-icons/chevron-light.png" />
              </view>
            </view>
          </view>

          <view class="tip-wrap">
            <text class="tip-title">安全提示</text>
            <text class="tip-text">为了保障您的账号安全，请定期更换密码，并确保实名信息真实有效。</text>
          </view>
        </view>
      </view>

      <view class="footer-wrap">
        <view class="close-btn" hover-class="close-btn-active" @tap="onCloseAccount">
          <text class="close-text">注销账号</text>
        </view>
        <text class="brand-text">Professional Networking Security Services</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { getCurrentUserProfile } from '../../../api/user'
import { getMyVerificationOverview } from '../../../api/verification'
import { bindWechatMiniapp, getWechatBindStatus } from '../../../api/auth'
import { getMiniappLoginCode, getWechatDeviceId } from '../../../utils/wechat-auth'

const phoneMasked = ref('未绑定')
const phoneBound = ref(false)
const wechatBound = ref(false)
const wechatBinding = ref(false)
const wechatBindText = computed(() => {
  if (wechatBinding.value) {
    return '绑定中'
  }
  return wechatBound.value ? '已绑定' : '未绑定'
})
const realnameStatusText = ref('未认证')
const realnameApproved = ref(false)
const realnameStatus = ref('not_submitted')

const securityItems = computed(() => [
  {
    key: 'phone',
    label: '手机号',
    iconPath: '/static/icon/phone.png',
    valueText: phoneMasked.value
  },
  {
    key: 'password',
    label: '修改密码',
    iconPath: '/static/icon/chage-pws.png'
  },
  {
    key: 'wechat',
    label: '微信绑定',
    iconPath: '/static/icon/wechat-link.png',
    valueText: wechatBindText.value
  },
  {
    key: 'realname',
    label: '实名认证',
    iconPath: '/static/icon/certification.png',
    valueText: realnameStatusText.value,
    valueClass: realnameApproved.value ? 'row-value-primary' : ''
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

const loadWechatBindStatus = async () => {
  try {
    const statusData = await getWechatBindStatus()
    wechatBound.value = Boolean(statusData?.wechat_bound)
  } catch (err) {
    // fallback: keep status from profile
  }
}

const loadSecurityData = async () => {
  try {
    const profile = await getCurrentUserProfile()
    phoneMasked.value = maskPhone(profile?.phone)
    phoneBound.value = /^\d{11}$/.test(String(profile?.phone || '').replace(/\s+/g, ''))
    wechatBound.value = Boolean(profile?.wechat_bound)
  } catch (err) {
    if (err?.statusCode === 401) {
      uni.navigateTo({
        url: '/pages/auth/login/index'
      })
      return
    }
  }

  await loadWechatBindStatus()

  try {
    const overview = await getMyVerificationOverview()
    const realname = (overview?.items || []).find((item) => item?.type === 'real_name')
    const status = String(realname?.status || 'not_submitted')
    realnameStatus.value = status

    if (status === 'approved') {
      realnameStatusText.value = '已认证'
      realnameApproved.value = true
      return
    }

    if (status === 'pending') {
      realnameStatusText.value = '审核中'
      realnameApproved.value = false
      return
    }

    if (status === 'rejected') {
      realnameStatusText.value = '已驳回'
      realnameApproved.value = false
      return
    }

    realnameStatusText.value = '未认证'
    realnameApproved.value = false
  } catch (err) {
    realnameStatus.value = 'not_submitted'
    realnameStatusText.value = '未认证'
    realnameApproved.value = false
  }
}

const confirmBindWechat = () => {
  uni.showModal({
    title: '绑定微信',
    content: '绑定微信后，您可以使用微信一键登录，无需输入手机号和密码。确定要绑定当前微信账号吗？',
    confirmText: '确定绑定',
    cancelText: '取消',
    success: (res) => {
      if (res?.confirm) {
        bindWechat()
      }
    }
  })
}

const bindWechat = async () => {
  if (wechatBinding.value) {
    return
  }

  wechatBinding.value = true

  uni.showLoading({
    title: '绑定中...',
    mask: true
  })

  try {
    let code = ''
    // #ifdef MP-WEIXIN
    code = await getMiniappLoginCode()
    // #endif
    // #ifndef MP-WEIXIN
    code = `dev_wechat_bind_${Date.now()}`
    // #endif

    await bindWechatMiniapp({
      code,
      device_id: getWechatDeviceId()
    })

    wechatBound.value = true
    uni.hideLoading()

    uni.showModal({
      title: '绑定成功',
      content: '微信账号已成功绑定，下次可以使用微信一键登录',
      showCancel: false,
      confirmText: '知道了'
    })
  } catch (err) {
    uni.hideLoading()

    if (err?.statusCode === 401) {
      uni.navigateTo({
        url: '/pages/auth/login/index'
      })
      return
    }

    // 处理已绑定其他账号的情况
    if (err?.message?.includes('已绑定') || err?.message?.includes('already bound')) {
      uni.showModal({
        title: '绑定失败',
        content: '该微信账号已绑定其他手机号，一个微信账号只能绑定一个手机号',
        showCancel: false,
        confirmText: '知道了'
      })
      return
    }

    showToast(err?.message || '微信绑定失败，请稍后重试')
  } finally {
    wechatBinding.value = false
  }
}

const onRowTap = (item) => {
  if (!item?.key) {
    return
  }

  if (item.key === 'realname') {
    if (realnameStatus.value === 'approved') {
      showToast('已完成实名认证')
      return
    }

    if (realnameStatus.value === 'pending') {
      showToast('实名认证审核中')
      return
    }

    uni.navigateTo({
      url: '/pages/me/auth/realname/index'
    })
    return
  }

  if (item.key === 'phone') {
    uni.navigateTo({
      url: '/pages/me/security/phone/index'
    })
    return
  }

  if (item.key === 'password') {
    if (!phoneBound.value) {
      uni.showModal({
        title: '无法修改密码',
        content: '请先绑定手机号，才能设置或修改密码',
        confirmText: '去绑定',
        cancelText: '取消',
        success: (res) => {
          if (res?.confirm) {
            uni.navigateTo({
              url: '/pages/me/security/phone/index'
            })
          }
        }
      })
      return
    }
    uni.navigateTo({
      url: '/pages/me/security/password/index'
    })
    return
  }

  if (item.key === 'wechat') {
    if (wechatBound.value) {
      uni.showModal({
        title: '微信已绑定',
        content: '您的账号已绑定微信，可以使用微信一键登录',
        showCancel: false,
        confirmText: '知道了'
      })
      return
    }
    confirmBindWechat()
  }
}

const onCloseAccount = () => {
  showToast('注销账号功能开发中')
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
