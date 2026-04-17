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
    iconPath: '/static/me-icons/contact-page-primary.png',
    valueText: phoneMasked.value
  },
  {
    key: 'password',
    label: '修改密码',
    iconPath: '/static/me-icons/tune-gray.png'
  },
  {
    key: 'wechat',
    label: '微信绑定',
    iconPath: '/static/me-icons/help-gray.png',
    valueText: wechatBindText.value
  },
  {
    key: 'realname',
    label: '实名认证',
    iconPath: '/static/me-icons/badge-primary.png',
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

const bindWechat = async () => {
  if (wechatBinding.value) {
    return
  }

  wechatBinding.value = true
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
    showToast('微信绑定成功')
  } catch (err) {
    if (err?.statusCode === 401) {
      uni.navigateTo({
        url: '/pages/auth/login/index'
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
      showToast('手机号未绑定，无法修改密码')
      return
    }
    uni.navigateTo({
      url: '/pages/me/security/password/index'
    })
    return
  }

  if (item.key === 'wechat') {
    if (wechatBound.value) {
      showToast('微信已绑定')
      return
    }
    bindWechat()
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
  margin-top: 16px;
  padding: 0 16px;
  box-sizing: border-box;
}

.first-section {
  margin-top: 16px;
}

.section-card {
  border-radius: 12px;
  overflow: hidden;
  background: #ffffff;
  border: 1px solid #f1f5f9;
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
}

.security-row {
  min-height: 56px;
  padding: 12px 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-sizing: border-box;
  transition: background-color 0.2s ease;
}

.security-row-border {
  border-bottom: 1px solid #f8fafc;
}

.security-row-active {
  background: #f8fafc;
}

.row-left {
  display: flex;
  align-items: center;
  gap: 16px;
  min-width: 0;
  flex: 1;
}

.row-icon-box {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: rgba(26, 87, 219, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.row-icon {
  width: 22px;
  height: 22px;
}

.row-label {
  font-size: 16px;
  font-weight: 500;
  color: #0f172a;
}

.row-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.row-value {
  font-size: 14px;
  color: #64748b;
}

.row-value-primary {
  color: #1a57db;
  font-weight: 500;
}

.row-chevron {
  width: 20px;
  height: 20px;
}

.tip-wrap {
  margin-top: 24px;
  padding: 16px;
  border-radius: 12px;
  border: 1px solid rgba(26, 87, 219, 0.1);
  background: rgba(26, 87, 219, 0.05);
}

.tip-title {
  display: block;
  margin-bottom: 4px;
  font-size: 14px;
  font-weight: 600;
  color: #1a57db;
}

.tip-text {
  display: block;
  font-size: 12px;
  line-height: 1.6;
  color: #475569;
}

.footer-wrap {
  margin-top: auto;
  padding: 32px 16px calc(24px + env(safe-area-inset-bottom));
  display: flex;
  flex-direction: column;
  align-items: center;
}

.close-btn {
  padding: 8px 16px;
  border-radius: 8px;
}

.close-btn-active {
  background: rgba(239, 68, 68, 0.08);
}

.close-text {
  font-size: 14px;
  font-weight: 500;
  color: #94a3b8;
}

.brand-text {
  margin-top: 16px;
  font-size: 10px;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: #94a3b8;
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
