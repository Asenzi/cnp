<template>
  <view class="edit-page">
    <view class="page-shell">
      <view class="top-nav" :style="navStyle">
        <view class="back-btn" hover-class="back-btn-hover" @tap="goBack">
          <image class="back-icon" mode="aspectFit" src="/static/me-icons/arrow-back-dark.png" />
        </view>
        <text class="nav-title">编辑个人资料</text>
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
          <text class="avatar-tip">{{ uploadingAvatar ? '头像上传中...' : '点击更换头像' }}</text>
        </view>
      </view>

      <view class="form-wrap">
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
              <view class="picker-text">{{ industryOptions[industryIndex].label }}</view>
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
          <text class="field-label">展示手机号</text>
          <input
            v-model="displayPhone"
            class="field-input"
            type="number"
            maxlength="11"
            placeholder="仅用于对外展示，不等同于绑定手机号"
            placeholder-class="field-placeholder"
          />
          <text class="field-tip">完善展示手机号、展示微信号，并完成实名认证和会员开通后，才可查看别人的联系方式。</text>
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
              <view class="picker-text">{{ cityDisplayText }}</view>
            </picker>
            <image class="expand-icon" mode="aspectFit" src="/static/me-icons/expand-more-slate.png" />
          </view>
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

        <view class="field-group">
          <text class="field-label">名片附件</text>

          <view class="upload-area" hover-class="upload-area-hover" @tap="onUploadCard">
            <view class="upload-inner">
              <image class="upload-icon" mode="aspectFit" src="/static/me-icons/upload-primary.png" />
              <text class="upload-text">点击选择名片文件 (JPG, PNG, PDF)</text>
            </view>
          </view>

          <view class="file-list">
            <view v-for="(file, index) in attachedFiles" :key="file.name + index" class="file-item">
              <view class="file-left">
                <image class="file-type-icon" mode="aspectFit" src="/static/me-icons/image-primary.png" />
                <view class="file-meta">
                  <text class="file-name">{{ file.name }}</text>
                  <text class="file-size">{{ file.size }}</text>
                </view>
              </view>
              <view class="file-remove" hover-class="file-remove-hover" @tap="removeFile(index)">
                <image class="cancel-icon" mode="aspectFit" src="/static/me-icons/cancel-slate.png" />
              </view>
            </view>
          </view>
        </view>

        <view class="toggle-card">
          <view class="toggle-copy">
            <text class="toggle-title">展示联系方式</text>
            <text class="toggle-desc">开启后仅展示你填写的展示手机号和微信号，绑定手机号不会对外公开</text>
          </view>
          <view class="switch-wrap" @tap="toggleShowContact">
            <view class="switch-track" :class="{ 'switch-track-on': showContact }"></view>
            <view class="switch-thumb" :class="{ 'switch-thumb-on': showContact }"></view>
          </view>
        </view>

        <view class="save-wrap">
          <view class="save-btn" hover-class="save-btn-hover" @tap="onSave">
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
  uploadCurrentUserAvatar,
  uploadCurrentUserCardFile
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
const showContact = ref(true)
const DISPLAY_PHONE_REGEX = /^1\d{10}$/

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

const attachedFiles = ref([])

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

const toggleShowContact = () => {
  showContact.value = !showContact.value
}

const removeFile = (index) => {
  attachedFiles.value.splice(index, 1)
}

const formatBytes = (size = 0) => {
  if (size <= 0) {
    return '--'
  }
  const mb = size / (1024 * 1024)
  if (mb >= 1) {
    return `${mb.toFixed(1)} MB`
  }
  const kb = size / 1024
  return `${Math.max(1, Math.round(kb))} KB`
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

const onUploadCard = () => {
  uni.chooseMessageFile({
    count: 3,
    type: 'file',
    extension: ['jpg', 'jpeg', 'png', 'pdf'],
    success: async (res) => {
      const files = res?.tempFiles || []
      if (!files.length) {
        return
      }

      for (const file of files) {
        if ((attachedFiles.value || []).length >= 5) {
          break
        }

        const filePath = file?.path
        if (!filePath) {
          continue
        }

        try {
          const uploaded = await uploadCurrentUserCardFile(filePath, file?.name || '附件')
          attachedFiles.value = [
            ...attachedFiles.value,
            {
              name: uploaded?.name || file?.name || '附件',
              size: formatBytes(uploaded?.size || file?.size || 0),
              size_bytes: uploaded?.size || file?.size || 0,
              url: uploaded?.url || ''
            }
          ]
        } catch (err) {
          showToast(err?.message || '附件上传失败')
          return
        }
      }

      showToast('附件上传成功')
    }
  })
}

const applyProfile = (profile = {}) => {
  avatarUrl.value = typeof profile?.avatar_url === 'string' && profile.avatar_url.trim() ? profile.avatar_url : DEFAULT_AVATAR
  nickname.value = typeof profile?.nickname === 'string' ? profile.nickname : ''
  bio.value = typeof profile?.intro === 'string' ? profile.intro : ''
  companyName.value = typeof profile?.company_name === 'string' ? profile.company_name : ''
  jobTitle.value = typeof profile?.job_title === 'string' ? profile.job_title : ''
  displayPhone.value = typeof profile?.display_phone === 'string' ? profile.display_phone : ''
  displayWechat.value = typeof profile?.display_wechat === 'string' ? profile.display_wechat : ''
  showContact.value = profile?.show_contact !== false

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

  const serverFiles = Array.isArray(profile?.card_files) ? profile.card_files : []
  attachedFiles.value = serverFiles
    .filter((item) => item && typeof item === 'object')
    .map((item) => ({
      name: item?.name || '附件',
      size: formatBytes(item?.size || 0),
      size_bytes: item?.size || 0,
      url: item?.url || ''
    }))
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
          avatarUrl.value = data.avatar_url
        }
        showToast('头像已更新')
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
  const selectedIndustry = industryOptions[industryIndex.value] || industryOptions[0]
  const selectedCity = currentSelectedCity.value
  const baseUrl = getApiBaseUrl()
  const normalizedAvatarUrl = String(avatarUrl.value || DEFAULT_AVATAR).trim()
  const avatarForSave = normalizedAvatarUrl.startsWith(`${baseUrl}/static/uploads/`)
    ? normalizedAvatarUrl.replace(baseUrl, '')
    : normalizedAvatarUrl

  if (normalizedDisplayPhone && !DISPLAY_PHONE_REGEX.test(normalizedDisplayPhone)) {
    showToast('请输入正确的展示手机号')
    return
  }

  displayPhone.value = normalizedDisplayPhone
  displayWechat.value = normalizedDisplayWechat

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
    city_code: selectedCity?.value || null,
    city_name: selectedCity?.label || null,
    card_files: attachedFiles.value.map((file) => ({
      name: file.name,
      url: String(file.url || '').startsWith(`${baseUrl}/static/uploads/`)
        ? String(file.url || '').replace(baseUrl, '')
        : String(file.url || ''),
      size: file.size_bytes || 0
    })),
    show_contact: showContact.value
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
  padding: 64rpx;
  padding-bottom: 48rpx;
}

.avatar-stack {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16rpx;
}

.avatar-wrap {
  position: relative;
}

.avatar {
  width: 224rpx;
  height: 224rpx;
  border-radius: 999rpx;
  border: 8rpx solid #f8fafc;
  box-shadow: 0 10rpx 24rpx rgba(15, 23, 42, 0.12);
}

.camera-badge {
  position: absolute;
  right: 0;
  bottom: 0;
  width: 64rpx;
  height: 64rpx;
  border-radius: 999rpx;
  border: 4rpx solid #ffffff;
  background: #1a57db;
  display: flex;
  align-items: center;
  justify-content: center;
}

.camera-icon {
  width: 30rpx;
  height: 30rpx;
}

.avatar-tip {
  font-size: 26rpx;
  color: #64748b;
  font-weight: 500;
}

.form-wrap {
  display: flex;
  flex-direction: column;
  gap: 48rpx;
  padding-left: 32rpx;
  padding-right: 32rpx;
  padding-bottom: calc(96rpx + env(safe-area-inset-bottom));
}

.field-group {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.field-label {
  margin-left: 8rpx;
  font-size: 26rpx;
  font-weight: 700;
  color: #0f172a;
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
  border: 1rpx solid #e2e8f0;
  border-radius: 24rpx;
  background: #f8fafc;
  color: #0f172a;
  transition: all 0.2s ease;
}

.field-input {
  height: 96rpx;
  line-height: 96rpx;
  padding: 0 32rpx;
  font-size: 30rpx;
}

.field-placeholder {
  color: #94a3b8;
}

.picker-wrap {
  position: relative;
  height: 96rpx;
  display: flex;
  align-items: center;
  padding-right: 84rpx;
}

.picker-control {
  flex: 1;
  height: 100%;
}

.picker-text {
  height: 96rpx;
  line-height: 96rpx;
  padding-left: 32rpx;
  font-size: 30rpx;
  color: #0f172a;
}

.expand-icon {
  position: absolute;
  right: 24rpx;
  top: 50%;
  width: 36rpx;
  height: 36rpx;
  transform: translateY(-50%);
}

.field-textarea {
  min-height: 256rpx;
  padding: 24rpx 32rpx;
  font-size: 30rpx;
  line-height: 1.7;
  width: 100%;
  box-sizing: border-box;
}

.upload-area {
  height: 256rpx;
  border: 2rpx dashed #e2e8f0;
  border-radius: 24rpx;
  background: rgba(248, 250, 252, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
}

.upload-area-hover {
  background: #f1f5f9;
}

.upload-inner {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8rpx;
}

.upload-icon {
  width: 64rpx;
  height: 64rpx;
}

.upload-text {
  font-size: 24rpx;
  color: #64748b;
}

.file-list {
  margin-top: 16rpx;
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.file-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24rpx;
  border-radius: 16rpx;
  border: 1rpx solid rgba(26, 87, 219, 0.2);
  background: rgba(26, 87, 219, 0.05);
}

.file-left {
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.file-type-icon {
  width: 40rpx;
  height: 40rpx;
}

.file-meta {
  display: flex;
  flex-direction: column;
  gap: 4rpx;
}

.file-name {
  font-size: 26rpx;
  font-weight: 500;
  color: #0f172a;
}

.file-size {
  font-size: 22rpx;
  color: #64748b;
}

.file-remove {
  width: 48rpx;
  height: 48rpx;
  border-radius: 999rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.file-remove-hover {
  background: rgba(148, 163, 184, 0.18);
}

.cancel-icon {
  width: 36rpx;
  height: 36rpx;
}

.toggle-card {
  margin-top: 8rpx;
  padding: 28rpx;
  border-radius: 24rpx;
  border: 1rpx solid #f1f5f9;
  background: #f8fafc;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24rpx;
}

.toggle-copy {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4rpx;
}

.toggle-title {
  font-size: 26rpx;
  font-weight: 700;
  color: #0f172a;
}

.toggle-desc {
  font-size: 22rpx;
  color: #64748b;
}

.switch-wrap {
  position: relative;
  width: 88rpx;
  height: 48rpx;
}

.switch-track {
  width: 88rpx;
  height: 48rpx;
  border-radius: 999rpx;
  background: #cbd5e1;
  transition: background 0.2s ease;
}

.switch-track-on {
  background: #1a57db;
}

.switch-thumb {
  position: absolute;
  top: 8rpx;
  left: 8rpx;
  width: 32rpx;
  height: 32rpx;
  border-radius: 999rpx;
  background: #ffffff;
  transition: transform 0.2s ease;
}

.switch-thumb-on {
  transform: translateX(40rpx);
}

.save-wrap {
  margin-top: -16rpx;
}

.save-btn {
  width: 100%;
  height: 96rpx;
  border-radius: 24rpx;
  background: #1a57db;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 12rpx 28rpx rgba(26, 87, 219, 0.25);
}

.save-btn-hover {
  background: #1d4ed8;
}

.save-text {
  font-size: 32rpx;
  color: #ffffff;
  font-weight: 700;
}

@media (prefers-color-scheme: dark) {
  .edit-page {
    background: #111621;
  }

  .page-shell {
    background: #111621;
    box-shadow: none;
  }

  .top-nav {
    background: #111621;
    border-bottom-color: #1e293b;
  }

  .back-btn-hover {
    background: #1e293b;
  }

  .back-icon,
  .expand-icon,
  .cancel-icon {
    filter: invert(90%) sepia(10%) saturate(272%) hue-rotate(177deg) brightness(107%) contrast(95%);
  }

  .nav-title,
  .field-label,
  .picker-text,
  .file-name,
  .toggle-title {
    color: #f1f5f9;
  }

  .avatar {
    border-color: #1e293b;
  }

  .camera-badge {
    border-color: #111621;
  }

  .avatar-tip,
  .upload-text,
  .file-size,
  .toggle-desc {
    color: #94a3b8;
  }

  .field-input,
  .picker-wrap,
  .field-textarea {
    background: #0f172a;
    border-color: #1e293b;
    color: #f1f5f9;
  }

  .field-placeholder {
    color: #64748b;
  }

  .upload-area {
    background: rgba(15, 23, 42, 0.6);
    border-color: #1e293b;
  }

  .upload-area-hover {
    background: #1e293b;
  }

  .file-item {
    border-color: rgba(26, 87, 219, 0.25);
    background: rgba(26, 87, 219, 0.1);
  }

  .file-remove-hover {
    background: rgba(100, 116, 139, 0.25);
  }

  .toggle-card {
    background: #0f172a;
    border-color: #1e293b;
  }

  .switch-track {
    background: #334155;
  }

  .switch-track-on {
    background: #1a57db;
  }
}
</style>
