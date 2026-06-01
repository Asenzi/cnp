<template>
  <view class="page">
    <view class="header" :style="{ paddingTop: statusBarHeight + 'px' }">
      <view class="back-btn" @tap="goBack">
        <image class="back-icon" mode="aspectFit" src="/static/me-icons/arrow-back-dark.png" />
      </view>
      <text class="title">编辑资料</text>
      <view class="placeholder"></view>
    </view>

    <view class="main">
      <!-- 头像区域 -->
      <view class="avatar-section">
        <view class="avatar-wrap" @tap="onChangeAvatar">
          <image class="avatar" mode="aspectFill" :src="avatarUrl" />
          <view class="camera-badge">
            <image class="camera-icon" mode="aspectFit" src="/static/me-icons/camera-white.png" />
          </view>
        </view>
        <text class="avatar-tip">{{ uploadingAvatar ? '上传中...' : '点击更换头像' }}</text>
      </view>

      <!-- 表单区域 -->
      <view class="form">
        <!-- 基本信息 -->
        <view class="section">
          <view class="section-header">
            <view class="section-line"></view>
            <text class="section-title">基本信息</text>
          </view>

          <view class="field">
            <text class="label">昵称</text>
            <input
              v-model="nickname"
              class="input"
              maxlength="64"
              placeholder="请输入您的昵称"
              placeholder-class="placeholder"
            />
          </view>

          <view class="field">
            <text class="label">个人简介</text>
            <textarea
              v-model="bio"
              class="textarea"
              maxlength="255"
              placeholder="描述您的专业背景、成就或合作需求..."
              placeholder-class="placeholder"
            />
          </view>
        </view>

        <!-- 职业信息 -->
        <view class="section">
          <view class="section-header">
            <view class="section-line"></view>
            <text class="section-title">职业信息</text>
          </view>

          <view class="field">
            <text class="label">行业</text>
            <view class="picker-field">
              <picker
                class="picker"
                mode="selector"
                :range="industryOptions"
                range-key="label"
                :value="industryIndex"
                @change="onIndustryChange"
              >
                <view class="picker-value" :class="{ 'picker-placeholder': industryIndex === 0 }">
                  {{ industryOptions[industryIndex].label }}
                </view>
              </picker>
              <image class="arrow" mode="aspectFit" src="/static/me-icons/expand-more-slate.png" />
            </view>
          </view>

          <view class="field">
            <text class="label">公司</text>
            <input
              v-model="companyName"
              class="input"
              maxlength="128"
              placeholder="请输入您的公司名称"
              placeholder-class="placeholder"
            />
          </view>

          <view class="field">
            <text class="label">职位</text>
            <input
              v-model="jobTitle"
              class="input"
              maxlength="64"
              placeholder="请输入您的职位"
              placeholder-class="placeholder"
            />
          </view>

          <view class="field">
            <text class="label">所在城市</text>
            <view class="picker-field">
              <picker
                class="picker"
                mode="multiSelector"
                :range="cityPickerRange"
                range-key="label"
                :value="cityPickerValue"
                @change="onCityChange"
                @columnchange="onCityColumnChange"
              >
                <view class="picker-value" :class="{ 'picker-placeholder': !selectedCityCode }">
                  {{ cityDisplayText }}
                </view>
              </picker>
              <image class="arrow" mode="aspectFit" src="/static/me-icons/expand-more-slate.png" />
            </view>
          </view>
        </view>

        <!-- 联系方式 -->
        <view class="section">
          <view class="section-header">
            <view class="section-line"></view>
            <text class="section-title">联系方式</text>
          </view>

          <view class="notice">
            <text class="notice-text">完善联系方式并完成实名认证后,开通会员或购买人群包,才可查看别人的联系方式</text>
          </view>

          <view class="field">
            <text class="label">展示手机号</text>
            <input
              v-model="displayPhone"
              class="input"
              type="number"
              maxlength="11"
              placeholder="仅用于对外展示"
              placeholder-class="placeholder"
            />
          </view>

          <view class="field">
            <text class="label">展示微信号</text>
            <input
              v-model="displayWechat"
              class="input"
              maxlength="64"
              placeholder="请输入对外展示的微信号"
              placeholder-class="placeholder"
            />
          </view>

          <view class="field">
            <text class="label">邮箱</text>
            <input
              v-model="email"
              class="input"
              type="text"
              maxlength="100"
              placeholder="请输入您的邮箱地址"
              placeholder-class="placeholder"
            />
          </view>
        </view>

        <!-- 保存按钮 -->
        <view class="save-wrap">
          <view class="save-btn" :class="{ 'save-btn-disabled': saving }" @tap="onSave">
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
          const uploadedUrl = data.avatar_url.trim()
          avatarUrl.value = uploadedUrl

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

  const baseUrl = getApiBaseUrl()
  const normalizedAvatarUrl = String(avatarUrl.value || DEFAULT_AVATAR).trim()
  let avatarForSave = normalizedAvatarUrl

  if (normalizedAvatarUrl.startsWith(baseUrl)) {
    avatarForSave = normalizedAvatarUrl.replace(baseUrl, '')
  } else if (normalizedAvatarUrl.startsWith('http://') || normalizedAvatarUrl.startsWith('https://')) {
    avatarForSave = normalizedAvatarUrl
  }

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
.page {
  min-height: 100vh;
  background: #f6f6f8;
}

.header {
  position: sticky;
  top: 0;
  z-index: 10;
  display: flex;
  align-items: center;
  background: #ffffff;
  border-bottom: 1rpx solid #e7ecf3;
}

.back-btn {
  width: 88rpx;
  height: 88rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.back-icon {
  width: 40rpx;
  height: 40rpx;
}

.title {
  flex: 1;
  text-align: center;
  font-size: 32rpx;
  font-weight: 600;
  color: #172033;
}

.placeholder {
  width: 88rpx;
}

.main {
  padding: 24rpx 32rpx;
  padding-bottom: calc(32rpx + env(safe-area-inset-bottom));
}

/* 头像区域 */
.avatar-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12rpx;
  padding: 32rpx 0 40rpx;
}

.avatar-wrap {
  position: relative;
}

.avatar {
  width: 128rpx;
  height: 128rpx;
  border-radius: 64rpx;
  background: #f3f6fa;
}

.camera-badge {
  position: absolute;
  right: 0;
  bottom: 0;
  width: 40rpx;
  height: 40rpx;
  border-radius: 20rpx;
  background: #2563eb;
  border: 3rpx solid #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
}

.camera-icon {
  width: 20rpx;
  height: 20rpx;
}

.avatar-tip {
  font-size: 24rpx;
  color: #66758a;
}

/* 表单 */
.form {
  display: flex;
  flex-direction: column;
  gap: 40rpx;
}

.section {
  background: #ffffff;
  border-radius: 16rpx;
  padding: 32rpx;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 12rpx;
  margin-bottom: 28rpx;
}

.section-line {
  width: 6rpx;
  height: 28rpx;
  background: #2563eb;
  border-radius: 3rpx;
}

.section-title {
  font-size: 28rpx;
  font-weight: 600;
  color: #172033;
}

.notice {
  padding: 20rpx;
  background: #f6f8fc;
  border-radius: 12rpx;
  margin-bottom: 24rpx;
}

.notice-text {
  font-size: 24rpx;
  line-height: 36rpx;
  color: #66758a;
}

.field {
  margin-bottom: 24rpx;
}

.field:last-child {
  margin-bottom: 0;
}

.label {
  display: block;
  font-size: 26rpx;
  font-weight: 500;
  color: #172033;
  margin-bottom: 12rpx;
}

.input,
.textarea,
.picker-field {
  width: 100%;
  background: #f6f8fc;
  border: 1rpx solid #e7ecf3;
  border-radius: 12rpx;
  font-size: 28rpx;
  color: #172033;
  box-sizing: border-box;
}

.input {
  height: 88rpx;
  padding: 0 24rpx;
}

.textarea {
  min-height: 160rpx;
  padding: 20rpx 24rpx;
  line-height: 1.6;
}

.placeholder {
  color: #98a5b8;
}

.picker-field {
  position: relative;
  height: 88rpx;
  display: flex;
  align-items: center;
  padding-right: 60rpx;
}

.picker {
  flex: 1;
  height: 100%;
}

.picker-value {
  height: 88rpx;
  line-height: 88rpx;
  padding-left: 24rpx;
  font-size: 28rpx;
  color: #172033;
}

.picker-placeholder {
  color: #98a5b8;
}

.arrow {
  position: absolute;
  right: 20rpx;
  width: 28rpx;
  height: 28rpx;
  opacity: 0.4;
}

/* 保存按钮 */
.save-wrap {
  margin-top: 8rpx;
}

.save-btn {
  width: 100%;
  height: 88rpx;
  background: #2563eb;
  border-radius: 44rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.save-btn-disabled {
  opacity: 0.6;
}

.save-text {
  font-size: 30rpx;
  font-weight: 500;
  color: #ffffff;
}
</style>
