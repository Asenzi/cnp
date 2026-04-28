<template>
  <view class="edit-page">
    <view class="page-shell">
      <view class="top-nav" :style="navStyle">
        <view class="back-btn" hover-class="back-btn-hover" @tap="goBack">
          <image class="back-icon" mode="aspectFit" src="/static/me-icons/arrow-back-dark.png" />
        </view>
        <text class="nav-title">编辑资料</text>
        <view class="nav-placeholder"></view>
      </view>

      <view class="avatar-section">
        <view class="avatar-stack" hover-class="avatar-stack-hover" @tap="onChangeAvatar">
          <view class="avatar-wrap">
            <image class="avatar" mode="aspectFill" :src="avatarUrl" />
            <view class="camera-badge">
              <image class="camera-icon" mode="aspectFit" src="/static/me-icons/camera-white.png" />
            </view>
          </view>
          <text class="avatar-tip">{{ uploadingAvatar ? '上传中...' : '点击更换头像' }}</text>
        </view>
      </view>

      <view class="form-wrap">
        <view class="section-title">基本信息</view>

        <view class="field-group">
          <text class="field-label">昵称</text>
          <input
            v-model="nickname"
            class="field-input"
            maxlength="64"
            placeholder="请输入您的昵称"
            placeholder-class="field-placeholder"
          />
        </view>

        <view class="field-group">
          <text class="field-label">个人简介</text>
          <textarea
            v-model="bio"
            class="field-textarea"
            maxlength="255"
            placeholder="描述您的专业背景、成就或合作需求..."
            placeholder-class="field-placeholder"
          />
        </view>

        <view class="section-title">职业信息</view>

        <view class="field-group">
          <text class="field-label">行业</text>
          <view class="picker-wrap">
            <picker
              class="picker-control"
              mode="selector"
              :range="industryOptions"
              range-key="label"
              :value="industryIndex"
              @change="onIndustryChange"
            >
              <view class="picker-text" :class="{ 'picker-text-placeholder': industryIndex === 0 }">
                {{ industryOptions[industryIndex].label }}
              </view>
            </picker>
            <image class="expand-icon" mode="aspectFit" src="/static/me-icons/expand-more-slate.png" />
          </view>
        </view>

        <view class="field-group">
          <text class="field-label">公司</text>
          <input
            v-model="companyName"
            class="field-input"
            maxlength="128"
            placeholder="请输入您的公司名称"
            placeholder-class="field-placeholder"
          />
        </view>

        <view class="field-group">
          <text class="field-label">职位</text>
          <input
            v-model="jobTitle"
            class="field-input"
            maxlength="64"
            placeholder="请输入您的职位"
            placeholder-class="field-placeholder"
          />
        </view>

        <view class="field-group">
          <text class="field-label">所在城市</text>
          <view class="picker-wrap">
            <picker
              class="picker-control"
              mode="multiSelector"
              :range="cityPickerRange"
              range-key="label"
              :value="cityPickerValue"
              @change="onCityChange"
              @columnchange="onCityColumnChange"
            >
              <view class="picker-text" :class="{ 'picker-text-placeholder': !selectedCityCode }">
                {{ cityDisplayText }}
              </view>
            </picker>
            <image class="expand-icon" mode="aspectFit" src="/static/me-icons/expand-more-slate.png" />
          </view>
        </view>

        <view class="section-title">联系方式</view>
        <view class="section-desc">完善联系方式并完成实名认证后，开通会员或购买人群包，才可查看别人的联系方式</view>

        <view class="field-group">
          <text class="field-label">展示手机号</text>
          <input
            v-model="displayPhone"
            class="field-input"
            type="number"
            maxlength="11"
            placeholder="仅用于对外展示"
            placeholder-class="field-placeholder"
          />
        </view>

        <view class="field-group">
          <text class="field-label">展示微信号</text>
          <input
            v-model="displayWechat"
            class="field-input"
            maxlength="64"
            placeholder="请输入对外展示的微信号"
            placeholder-class="field-placeholder"
          />
        </view>

        <view class="field-group">
          <text class="field-label">邮箱</text>
          <input
            v-model="email"
            class="field-input"
            type="text"
            maxlength="100"
            placeholder="请输入您的邮箱地址"
            placeholder-class="field-placeholder"
          />
        </view>

        <view class="save-wrap">
          <view class="save-btn" :class="{ 'save-btn-disabled': saving }" hover-class="save-btn-hover" @tap="onSave">
            <text class="save-text">{{ saving ? '保存中...' : '保存修改' }}</text>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import {
  getCurrentUserProfile,
  updateCurrentUserProfile,
  uploadCurrentUserAvatar
} from '../../../api/user'
import { getApiBaseUrl } from '../../../utils/request'
import { PROVINCE_CITY_OPTIONS } from './modules/city-picker-data'

const DEFAULT_AVATAR = '/static/logo.png'

const { statusBarHeight = 0 } = uni.getSystemInfoSync()
const navStyle = `padding-top:${statusBarHeight}px;`

const loading = ref(false)
const saving = ref(false)
const uploadingAvatar = ref(false)

const avatarUrl = ref(DEFAULT_AVATAR)
const nickname = ref('')
const bio = ref('')
const companyName = ref('')
const jobTitle = ref('')
const displayPhone = ref('')
const displayWechat = ref('')
const email = ref('')
const DISPLAY_PHONE_REGEX = /^1\d{10}$/
const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

const industryOptions = [
  { value: '', label: '请选择行业' },
  { value: 'internet_ai', label: '互联网 / AI' },
  { value: 'electronics', label: '电子 / 电器 / 通讯' },
  { value: 'product', label: '产品' },
  { value: 'operations', label: '客服 / 运营' },
  { value: 'sales', label: '销售' },
  { value: 'hr_admin_legal', label: '人力 / 行政 / 法务' },
  { value: 'finance_tax', label: '财务 / 审计 / 税务' },
  { value: 'marketing_pr', label: '市场 / 品牌 / 公关' },
  { value: 'design_media', label: '设计 / 传媒' },
  { value: 'education', label: '教育 / 培训' },
  { value: 'healthcare', label: '医疗 / 健康' },
  { value: 'financial_services', label: '金融' },
  { value: 'manufacturing_supply', label: '制造 / 供应链' },
  { value: 'construction_real_estate', label: '建筑 / 房地产' },
  { value: 'ecommerce_retail', label: '电商 / 零售' },
  { value: 'logistics_trade', label: '物流 / 贸易' },
  { value: 'consulting_services', label: '咨询 / 专业服务' },
  { value: 'energy_environment', label: '能源 / 环保' },
  { value: 'public_service', label: '政府 / 公共服务' },
  { value: 'other', label: '其他' }
]
const industryIndex = ref(0)
const provinceOptions = PROVINCE_CITY_OPTIONS
const provinceIndex = ref(0)
const cityIndex = ref(0)
const selectedCityCode = ref('')

const currentProvince = computed(() => provinceOptions[provinceIndex.value] || provinceOptions[0] || { cities: [] })

const cityPickerRange = computed(() => [
  provinceOptions,
  currentProvince.value?.cities || []
])

const cityPickerValue = computed(() => [provinceIndex.value, cityIndex.value])

const currentSelectedCity = computed(() => {
  if (!selectedCityCode.value) {
    return null
  }
  return currentProvince.value?.cities?.[cityIndex.value] || null
})

const cityDisplayText = computed(() => {
  if (!selectedCityCode.value || !currentSelectedCity.value) {
    return '请选择所在城市'
  }
  return `${currentProvince.value.label} / ${currentSelectedCity.value.label}`
})

const showToast = (title) => {
  uni.showToast({
    title,
    icon: 'none'
  })
}

const formatAmount = (value) => {
  const amount = Number(value)
  return Number.isFinite(amount) ? amount.toFixed(2) : '0.00'
}

const goBack = () => {
  if (getCurrentPages().length > 1) {
    uni.navigateBack()
    return
  }

  uni.switchTab({
    url: '/pages/tab/me/index'
  })
}

const onIndustryChange = (event) => {
  industryIndex.value = Number(event.detail.value || 0)
}

const onCityChange = (event) => {
  const [nextProvinceIndex = 0, nextCityIndex = 0] = Array.isArray(event?.detail?.value) ? event.detail.value : []
  provinceIndex.value = Number(nextProvinceIndex || 0)
  syncCityIndex(Number(nextCityIndex || 0))
  const city = currentProvince.value?.cities?.[cityIndex.value] || null
  selectedCityCode.value = city?.value || ''
}

const onCityColumnChange = (event) => {
  const changedColumn = Number(event?.detail?.column ?? -1)
  const changedValue = Number(event?.detail?.value || 0)
  if (changedColumn === 0) {
    provinceIndex.value = changedValue
    syncCityIndex(0)
    return
  }
  if (changedColumn === 1) {
    syncCityIndex(changedValue)
  }
}

const syncCityIndex = (nextCityIndex = 0) => {
  const cities = currentProvince.value?.cities || []
  if (!cities.length) {
    cityIndex.value = 0
    return
  }
  const normalizedIndex = Math.min(Math.max(Number(nextCityIndex || 0), 0), cities.length - 1)
  cityIndex.value = normalizedIndex
}

const findCitySelection = (cityCode = '', cityName = '') => {
  const normalizedCode = String(cityCode || '').trim()
  const normalizedName = String(cityName || '').trim()

  for (let provinceIdx = 0; provinceIdx < provinceOptions.length; provinceIdx += 1) {
    const province = provinceOptions[provinceIdx]
    const cities = Array.isArray(province?.cities) ? province.cities : []
    const cityIdx = cities.findIndex((city) => {
      if (normalizedCode && city?.value === normalizedCode) {
        return true
      }
      if (normalizedName && city?.label === normalizedName) {
        return true
      }
      return false
    })
    if (cityIdx >= 0) {
      return {
        provinceIdx,
        cityIdx,
        city: cities[cityIdx]
      }
    }
  }

  return null
}

const applyProfile = (profile = {}) => {
  avatarUrl.value = typeof profile?.avatar_url === 'string' && profile.avatar_url.trim() ? profile.avatar_url : DEFAULT_AVATAR
  nickname.value = typeof profile?.nickname === 'string' ? profile.nickname : ''
  bio.value = typeof profile?.intro === 'string' ? profile.intro : ''
  companyName.value = typeof profile?.company_name === 'string' ? profile.company_name : ''
  jobTitle.value = typeof profile?.job_title === 'string' ? profile.job_title : ''
  displayPhone.value = typeof profile?.display_phone === 'string' ? profile.display_phone : ''
  displayWechat.value = typeof profile?.display_wechat === 'string' ? profile.display_wechat : ''
  email.value = typeof profile?.email === 'string' ? profile.email : ''

  const code = typeof profile?.industry_code === 'string' ? profile.industry_code.trim() : ''
  const label = typeof profile?.industry_label === 'string' ? profile.industry_label.trim() : ''
  if (!code && !label) {
    industryIndex.value = 0
  } else {
    let idx = industryOptions.findIndex((option) => option.value === code)
    if (idx < 0 && label) {
      idx = industryOptions.findIndex((option) => option.label === label)
    }
    industryIndex.value = idx >= 0 ? idx : 0
  }

  const profileCityCode = typeof profile?.city_code === 'string' ? profile.city_code.trim() : ''
  const profileCityName = typeof profile?.city_name === 'string' ? profile.city_name.trim() : ''
  const selection = findCitySelection(profileCityCode, profileCityName)
  if (selection) {
    provinceIndex.value = selection.provinceIdx
    syncCityIndex(selection.cityIdx)
    selectedCityCode.value = selection.city?.value || ''
  } else {
    provinceIndex.value = 0
    syncCityIndex(0)
    selectedCityCode.value = ''
  }
}

const loadProfile = async () => {
  if (loading.value) {
    return
  }

  const token = uni.getStorageSync('token')
  if (!token) {
    showToast('请先登录')
    setTimeout(() => {
      uni.navigateTo({
        url: '/pages/auth/login/index'
      })
    }, 200)
    return
  }

  loading.value = true
  try {
    const profile = await getCurrentUserProfile()
    applyProfile(profile)
    uni.setStorageSync('userInfo', profile || {})
  } catch (err) {
    if (err?.statusCode === 401) {
      uni.removeStorageSync('token')
      uni.removeStorageSync('isLoggedIn')
      uni.removeStorageSync('userInfo')
      showToast('登录已失效，请重新登录')
      setTimeout(() => {
        uni.navigateTo({
          url: '/pages/auth/login/index'
        })
      }, 200)
      return
    }

    showToast(err?.message || '加载资料失败')
  } finally {
    loading.value = false
  }
}

const onChangeAvatar = () => {
  if (uploadingAvatar.value) {
    return
  }

  uni.chooseImage({
    count: 1,
    sizeType: ['compressed'],
    sourceType: ['album', 'camera'],
    success: async (res) => {
      const filePath = res?.tempFilePaths?.[0]
      if (!filePath) {
        return
      }

      uploadingAvatar.value = true
      try {
        const data = await uploadCurrentUserAvatar(filePath)
        if (typeof data?.avatar_url === 'string' && data.avatar_url.trim()) {
          // 上传API已经更新了后端的头像，直接更新本地显示
          const uploadedUrl = data.avatar_url.trim()
          avatarUrl.value = uploadedUrl

          // 更新本地缓存
          const userInfo = uni.getStorageSync('userInfo') || {}
          userInfo.avatar_url = uploadedUrl
          uni.setStorageSync('userInfo', userInfo)

          showToast('头像已更新')
        }
      } catch (err) {
        showToast(err?.message || '头像上传失败')
      } finally {
        uploadingAvatar.value = false
      }
    }
  })
}

const onSave = async () => {
  if (saving.value) {
    return
  }

  const normalizedNickname = String(nickname.value || '').trim()
  if (!normalizedNickname) {
    showToast('请输入昵称')
    return
  }

  const intro = String(bio.value || '').trim()
  const normalizedCompanyName = String(companyName.value || '').trim()
  const normalizedJobTitle = String(jobTitle.value || '').trim()
  const normalizedDisplayPhone = String(displayPhone.value || '').replace(/\D/g, '').slice(0, 11)
  const normalizedDisplayWechat = String(displayWechat.value || '').trim().replace(/\s+/g, '')
  const normalizedEmail = String(email.value || '').trim()
  const selectedIndustry = industryOptions[industryIndex.value] || industryOptions[0]
  const selectedCity = currentSelectedCity.value

  // 处理头像URL：如果是完整URL，去掉baseUrl；如果已经是相对路径，直接使用
  const baseUrl = getApiBaseUrl()
  const normalizedAvatarUrl = String(avatarUrl.value || DEFAULT_AVATAR).trim()
  let avatarForSave = normalizedAvatarUrl

  if (normalizedAvatarUrl.startsWith(baseUrl)) {
    // 完整URL，去掉baseUrl部分
    avatarForSave = normalizedAvatarUrl.replace(baseUrl, '')
  } else if (normalizedAvatarUrl.startsWith('http://') || normalizedAvatarUrl.startsWith('https://')) {
    // 其他域名的完整URL，保持不变
    avatarForSave = normalizedAvatarUrl
  }
  // 否则已经是相对路径，直接使用

  if (normalizedDisplayPhone && !DISPLAY_PHONE_REGEX.test(normalizedDisplayPhone)) {
    showToast('请输入正确的展示手机号')
    return
  }

  if (normalizedEmail && !EMAIL_REGEX.test(normalizedEmail)) {
    showToast('请输入正确的邮箱地址')
    return
  }

  displayPhone.value = normalizedDisplayPhone
  displayWechat.value = normalizedDisplayWechat
  email.value = normalizedEmail

  const payload = {
    nickname: normalizedNickname,
    avatar_url: avatarForSave || DEFAULT_AVATAR,
    intro,
    industry_code: selectedIndustry.value || null,
    industry_label: selectedIndustry.value ? selectedIndustry.label : null,
    company_name: normalizedCompanyName || null,
    job_title: normalizedJobTitle || null,
    display_phone: normalizedDisplayPhone || null,
    display_wechat: normalizedDisplayWechat || null,
    email: normalizedEmail || null,
    city_code: selectedCity?.value || null,
    city_name: selectedCity?.label || null
  }

  saving.value = true
  try {
    const profile = await updateCurrentUserProfile(payload)
    const review = profile && typeof profile._review === 'object'
      ? profile._review
      : null
    const nextProfile = profile && typeof profile === 'object'
      ? { ...profile }
      : {}

    if (nextProfile && typeof nextProfile === 'object') {
      delete nextProfile._review
    }

    if (review?.review_required) {
      const feeMessage = review?.fee_paid
        ? `，已扣除审核费¥${formatAmount(review?.fee_amount)}`
        : ''
      showToast(`资料已提交审核${feeMessage}`)
      setTimeout(() => {
        goBack()
      }, 250)
      return
    }

    applyProfile(nextProfile)
    uni.setStorageSync('userInfo', nextProfile)
    showToast('保存成功')
    setTimeout(() => {
      goBack()
    }, 250)
  } catch (err) {
    if (Number(err?.code) === 5701) {
      const detail = err?.payload?.data || {}
      showToast(
        `本月修改次数已超限，需支付审核费¥${formatAmount(detail?.required_amount)}，当前余额¥${formatAmount(detail?.wallet_balance)}`
      )
      return
    }
    showToast(err?.message || '保存失败，请稍后重试')
  } finally {
    saving.value = false
  }
}

onShow(() => {
  loadProfile()
})
</script>

<style scoped>
.edit-page {
  min-height: 100vh;
  background: #f6f6f8;
}

.page-shell {
  min-height: 100vh;
  max-width: 750rpx;
  margin: 0 auto;
  background: #ffffff;
  box-shadow: 0 8rpx 28rpx rgba(15, 23, 42, 0.08);
}

.top-nav {
  position: sticky;
  top: 0;
  z-index: 10;
  display: flex;
  align-items: center;
  gap: 16rpx;
  padding-left: 32rpx;
  padding-right: 32rpx;
  border-bottom: 1rpx solid #f1f5f9;
  background: #ffffff;
}

.back-btn {
  width: 80rpx;
  height: 80rpx;
  border-radius: 999rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.back-btn-hover {
  background: #f1f5f9;
}

.back-icon {
  width: 44rpx;
  height: 44rpx;
}

.nav-title {
  flex: 1;
  height: 88rpx;
  line-height: 88rpx;
  text-align: center;
  font-size: 34rpx;
  font-weight: 700;
  color: #0f172a;
}

.nav-placeholder {
  width: 80rpx;
  height: 80rpx;
}

.avatar-section {
  padding: 48rpx 64rpx 32rpx;
}

.avatar-stack {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12rpx;
}

.avatar-wrap {
  position: relative;
}

.avatar {
  width: 160rpx;
  height: 160rpx;
  border-radius: 999rpx;
  border: 6rpx solid #f8fafc;
  box-shadow: 0 8rpx 20rpx rgba(15, 23, 42, 0.1);
}

.camera-badge {
  position: absolute;
  right: 0;
  bottom: 0;
  width: 48rpx;
  height: 48rpx;
  border-radius: 999rpx;
  border: 3rpx solid #ffffff;
  background: #1a57db;
  display: flex;
  align-items: center;
  justify-content: center;
}

.camera-icon {
  width: 24rpx;
  height: 24rpx;
}

.avatar-tip {
  font-size: 24rpx;
  color: #64748b;
  font-weight: 500;
}

.form-wrap {
  display: flex;
  flex-direction: column;
  gap: 32rpx;
  padding-left: 32rpx;
  padding-right: 32rpx;
  padding-bottom: calc(96rpx + env(safe-area-inset-bottom));
}

.section-title {
  margin-top: 16rpx;
  margin-bottom: -8rpx;
  margin-left: 8rpx;
  font-size: 28rpx;
  font-weight: 700;
  color: #1a57db;
  letter-spacing: 0.5rpx;
}

.section-desc {
  margin-top: -16rpx;
  margin-left: 8rpx;
  margin-right: 8rpx;
  padding: 20rpx 24rpx;
  border-radius: 16rpx;
  background: rgba(26, 87, 219, 0.06);
  border: 1rpx solid rgba(26, 87, 219, 0.12);
  color: #475569;
  font-size: 24rpx;
  line-height: 1.6;
}

.field-group {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.field-label {
  margin-left: 8rpx;
  font-size: 26rpx;
  font-weight: 600;
  color: #334155;
}

.field-tip {
  margin-left: 8rpx;
  color: #64748b;
  font-size: 22rpx;
  line-height: 34rpx;
}

.field-input,
.picker-wrap,
.field-textarea {
  border: 2rpx solid #e2e8f0;
  border-radius: 20rpx;
  background: #ffffff;
  color: #0f172a;
  transition: all 0.2s ease;
}

.field-input:focus,
.field-textarea:focus {
  border-color: #1a57db;
  background: #ffffff;
}

.field-input {
  height: 88rpx;
  line-height: 88rpx;
  padding: 0 28rpx;
  font-size: 28rpx;
}

.field-placeholder {
  color: #94a3b8;
  font-size: 26rpx;
}

.picker-wrap {
  position: relative;
  height: 88rpx;
  display: flex;
  align-items: center;
  padding-right: 80rpx;
}

.picker-control {
  flex: 1;
  height: 100%;
}

.picker-text {
  height: 88rpx;
  line-height: 88rpx;
  padding-left: 28rpx;
  font-size: 28rpx;
  color: #0f172a;
}

.picker-text-placeholder {
  color: #94a3b8;
  font-size: 26rpx;
}

.expand-icon {
  position: absolute;
  right: 20rpx;
  top: 50%;
  width: 32rpx;
  height: 32rpx;
  transform: translateY(-50%);
  opacity: 0.5;
}

.field-textarea {
  min-height: 200rpx;
  padding: 20rpx 28rpx;
  font-size: 28rpx;
  line-height: 1.6;
  width: 100%;
  box-sizing: border-box;
}

.save-wrap {
  margin-top: 16rpx;
  margin-bottom: 16rpx;
}

.save-btn {
  width: 100%;
  height: 88rpx;
  border-radius: 20rpx;
  background: linear-gradient(135deg, #1a57db 0%, #1e40af 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8rpx 20rpx rgba(26, 87, 219, 0.2);
  transition: all 0.2s ease;
}

.save-btn-hover {
  transform: translateY(-2rpx);
  box-shadow: 0 12rpx 24rpx rgba(26, 87, 219, 0.3);
}

.save-btn-disabled {
  opacity: 0.6;
  box-shadow: none;
}

.save-text {
  font-size: 30rpx;
  color: #ffffff;
  font-weight: 600;
  letter-spacing: 1rpx;
}

@media (prefers-color-scheme: dark) {
  .edit-page {
    background: #0f172a;
  }

  .page-shell {
    background: #1e293b;
    box-shadow: none;
  }

  .top-nav {
    background: #1e293b;
    border-bottom-color: #334155;
  }

  .back-btn-hover {
    background: #334155;
  }

  .back-icon,
  .expand-icon {
    filter: invert(90%) sepia(10%) saturate(272%) hue-rotate(177deg) brightness(107%) contrast(95%);
  }

  .nav-title {
    color: #f1f5f9;
  }

  .avatar {
    border-color: #334155;
    box-shadow: 0 8rpx 20rpx rgba(0, 0, 0, 0.2);
  }

  .camera-badge {
    border-color: #1e293b;
  }

  .avatar-tip {
    color: #94a3b8;
  }

  .section-title {
    color: #60a5fa;
  }

  .section-desc {
    background: rgba(96, 165, 250, 0.1);
    border-color: rgba(96, 165, 250, 0.2);
    color: #94a3b8;
  }

  .field-label {
    color: #cbd5e1;
  }

  .field-input,
  .picker-wrap,
  .field-textarea {
    background: #0f172a;
    border-color: #334155;
    color: #f1f5f9;
  }

  .field-input:focus,
  .field-textarea:focus {
    border-color: #3b82f6;
    background: #0f172a;
  }

  .field-placeholder {
    color: #64748b;
  }

  .picker-text {
    color: #f1f5f9;
  }

  .picker-text-placeholder {
    color: #64748b;
  }

  .save-btn {
    background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%);
    box-shadow: 0 8rpx 20rpx rgba(37, 99, 235, 0.3);
  }

  .save-btn-hover {
    box-shadow: 0 12rpx 24rpx rgba(37, 99, 235, 0.4);
  }
}
</style>
