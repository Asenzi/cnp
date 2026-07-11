<template>
  <view class="page">
    <view class="header" :style="{ paddingTop: statusBarHeight + 'px' }">
      <view class="back-btn" @tap="goBack">
        <image class="back-icon" mode="aspectFit" src="https://cos.cnptec.site/static/me-icons/arrow-back-dark.png" />
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
            <image class="camera-icon" mode="aspectFit" src="https://cos.cnptec.site/static/me-icons/camera-white.png" />
          </view>
        </view>
        <text class="avatar-tip">{{ uploadingAvatar ? '上传中...' : avatarTipText }}</text>
      </view>

      <view v-if="reviewNoticeText" class="review-notice">
        <text class="review-notice-text">{{ reviewNoticeText }}</text>
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
              <image class="arrow" mode="aspectFit" src="https://cos.cnptec.site/static/me-icons/expand-more-slate.png" />
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
              <image class="arrow" mode="aspectFit" src="https://cos.cnptec.site/static/me-icons/expand-more-slate.png" />
            </view>
          </view>

          <!-- 位置坐标字段已移除 - 现在由系统自动获取 -->
          <!-- <view class="field">
            <text class="label">位置坐标</text>
            <view class="location-field">
              <view class="location-content">
                <text class="location-value" :class="{ 'location-placeholder': !hasCoordinates }">
                  {{ coordinateDisplayText }}
                </text>
              </view>
              <button
                class="location-btn"
                :disabled="locating"
                hover-class="location-btn-active"
                @tap="onGetLocation"
              >
                {{ locating ? '定位中' : '获取定位' }}
              </button>
            </view>
          </view> -->
        </view>

        <!-- 联系方式 -->
        <view class="section">
          <view class="section-header">
            <view class="section-line"></view>
            <text class="section-title">联系方式</text>
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

const DEFAULT_AVATAR = 'https://cos.cnptec.site/static/logo.png'

const { statusBarHeight = 0 } = uni.getSystemInfoSync()

const loading = ref(false)
const saving = ref(false)
const uploadingAvatar = ref(false)
const locating = ref(false)
const hasSelectedNewAvatar = ref(false) // 标记是否选择了新头像
const profileReview = ref({})

const avatarUrl = ref(DEFAULT_AVATAR)
const nickname = ref('')
const bio = ref('')
const companyName = ref('')
const jobTitle = ref('')
const displayPhone = ref('')
const displayWechat = ref('')
const email = ref('')
const latitude = ref(null)
const longitude = ref(null)
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

const normalizeCoordinate = (value) => {
  if (value === null || value === undefined || value === '') {
    return null
  }
  const coordinate = Number(value)
  return Number.isFinite(coordinate) ? coordinate : null
}

const hasCoordinates = computed(() => (
  normalizeCoordinate(latitude.value) !== null
  && normalizeCoordinate(longitude.value) !== null
))

const coordinateDisplayText = computed(() => {
  if (!hasCoordinates.value) {
    return '暂未获取经纬度'
  }
  return `纬度 ${Number(latitude.value).toFixed(7)}\n经度 ${Number(longitude.value).toFixed(7)}`
})

const reviewNoticeText = computed(() => {
  const statuses = profileReview.value || {}
  if (statuses.avatar_status === 'pending') return '头像审核中，通过后将自动展示'
  if (statuses.avatar_status === 'rejected') return '头像不符合平台规范，请重新上传'
  if (statuses.avatar_status === 'review_failed') return '头像审核暂时失败，请稍后重试'
  if (statuses.nickname_status === 'pending' || statuses.intro_status === 'pending') return '资料审核中，通过后将自动展示'
  if (statuses.nickname_status === 'rejected' || statuses.intro_status === 'rejected') return '资料包含不合规内容，请修改后重试'
  return ''
})

const avatarTipText = computed(() => {
  const status = String(profileReview.value?.avatar_status || '').trim()
  if (status === 'pending') return '头像审核中'
  if (status === 'rejected') return '点击重新上传头像'
  if (status === 'review_failed') return '点击重新上传头像'
  return '点击更换头像'
})

const showToast = (title) => {
  uni.showToast({
    title,
    icon: 'none'
  })
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

// 定位功能已移除 - 现在由系统自动获取
// const onGetLocation = async () => {
//   if (locating.value) {
//     return
//   }

//   locating.value = true
//   try {
//     const location = await new Promise((resolve, reject) => {
//       uni.getLocation({
//         type: 'gcj02',
//         isHighAccuracy: true,
//         highAccuracyExpireTime: 5000,
//         success: resolve,
//         fail: reject
//       })
//     })
//     const nextLatitude = Number(location?.latitude)
//     const nextLongitude = Number(location?.longitude)
//     if (
//       !Number.isFinite(nextLatitude)
//       || !Number.isFinite(nextLongitude)
//       || nextLatitude < -90
//       || nextLatitude > 90
//       || nextLongitude < -180
//       || nextLongitude > 180
//     ) {
//       throw new Error('定位结果无效')
//     }

//     latitude.value = Number(nextLatitude.toFixed(7))
//     longitude.value = Number(nextLongitude.toFixed(7))
//     showToast('定位成功，请点击保存修改')
//   } catch (error) {
//     const message = String(error?.errMsg || error?.message || '').toLowerCase()
//     const denied = message.includes('auth deny') || message.includes('permission')
//     if (denied) {
//       uni.showModal({
//         title: '需要定位权限',
//         content: '请在小程序设置中允许使用位置信息后重试',
//         confirmText: '去设置',
//         success: (result) => {
//           if (result.confirm) {
//             uni.openSetting()
//           }
//         }
//       })
//       return
//     }
//     showToast(error?.message || '定位失败，请稍后重试')
//   } finally {
//     locating.value = false
//   }
// }

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
  profileReview.value = profile?.profile_review && typeof profile.profile_review === 'object'
    ? profile.profile_review
    : {}
  // 只在没有选择新头像时才更新头像
  if (!hasSelectedNewAvatar.value) {
    avatarUrl.value = typeof profile?.avatar_url === 'string' && profile.avatar_url.trim() ? profile.avatar_url : DEFAULT_AVATAR
  }
  nickname.value = typeof profile?.nickname === 'string' ? profile.nickname : ''
  bio.value = typeof profile?.intro === 'string' ? profile.intro : ''
  companyName.value = typeof profile?.company_name === 'string' ? profile.company_name : ''
  jobTitle.value = typeof profile?.job_title === 'string' ? profile.job_title : ''
  displayPhone.value = typeof profile?.display_phone === 'string' ? profile.display_phone : ''
  displayWechat.value = typeof profile?.display_wechat === 'string' ? profile.display_wechat : ''
  email.value = typeof profile?.email === 'string' ? profile.email : ''
  latitude.value = normalizeCoordinate(profile?.latitude)
  longitude.value = normalizeCoordinate(profile?.longitude)

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
    success: (res) => {
      const filePath = res?.tempFilePaths?.[0]
      if (!filePath) {
        return
      }

      console.log('选择的图片路径:', filePath)

      // 标记已选择新头像
      hasSelectedNewAvatar.value = true

      // 更新本地预览，使用临时文件路径
      avatarUrl.value = filePath

      showToast('头像已选择，点击提交保存')
    },
    fail: (err) => {
      console.error('选择图片失败:', err)
      showToast('选择图片失败')
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

  saving.value = true
  let avatarForSave = normalizedAvatarUrl
  let avatarUploadedDirectly = false // 标记头像是否已通过专用接口上传

  try {
    // 如果选择了新头像，必须先上传
    if (hasSelectedNewAvatar.value) {
      uploadingAvatar.value = true
      try {
        console.log('开始上传新头像:', normalizedAvatarUrl)
        const data = await uploadCurrentUserAvatar(normalizedAvatarUrl)
        if (typeof data?.avatar_url === 'string' && data.avatar_url.trim()) {
          avatarForSave = data.avatar_url.trim()
          avatarUploadedDirectly = true // 标记头像已通过专用接口直接保存到数据库
          console.log('头像上传成功（已直接保存到数据库）:', avatarForSave)

          // 更新本地存储的用户信息
          const userInfo = uni.getStorageSync('userInfo') || {}
          userInfo.avatar_url = avatarForSave
          if (data?.profile_review && typeof data.profile_review === 'object') {
            userInfo.profile_review = data.profile_review
            profileReview.value = data.profile_review
          }
          uni.setStorageSync('userInfo', userInfo)

          // 更新本地显示
          avatarUrl.value = avatarForSave
        } else {
          throw new Error('头像上传返回数据异常')
        }
      } catch (err) {
        saving.value = false
        uploadingAvatar.value = false
        console.error('头像上传失败:', err)
        showToast(err?.message || '头像上传失败，请重试')
        return
      } finally {
        uploadingAvatar.value = false
      }
    } else {
      // 没有选择新头像，处理现有头像 URL
      if (normalizedAvatarUrl.startsWith(baseUrl)) {
        avatarForSave = normalizedAvatarUrl.replace(baseUrl, '')
      } else if (normalizedAvatarUrl.startsWith('http://') || normalizedAvatarUrl.startsWith('https://')) {
        avatarForSave = normalizedAvatarUrl
      } else if (normalizedAvatarUrl === DEFAULT_AVATAR) {
        avatarForSave = DEFAULT_AVATAR
      } else {
        // 其他情况使用默认头像
        avatarForSave = DEFAULT_AVATAR
      }
    }

    // 如果只修改了头像，已经通过专用接口保存，直接返回成功
    if (avatarUploadedDirectly) {
      // 检查其他字段是否有修改
      const currentProfile = uni.getStorageSync('userInfo') || {}
      const hasOtherChanges =
        normalizedNickname !== (currentProfile.nickname || '') ||
        intro !== (currentProfile.intro || '') ||
        normalizedCompanyName !== (currentProfile.company_name || '') ||
        normalizedJobTitle !== (currentProfile.job_title || '') ||
        normalizedDisplayPhone !== (currentProfile.display_phone || '') ||
        normalizedDisplayWechat !== (currentProfile.display_wechat || '') ||
        normalizedEmail !== (currentProfile.email || '') ||
        // 经纬度由系统自动更新，不再检查
        // normalizeCoordinate(latitude.value) !== normalizeCoordinate(currentProfile.latitude) ||
        // normalizeCoordinate(longitude.value) !== normalizeCoordinate(currentProfile.longitude) ||
        (selectedIndustry.value && selectedIndustry.value !== (currentProfile.industry_code || '')) ||
        (selectedCity?.value && selectedCity.value !== (currentProfile.city_code || ''))

      if (!hasOtherChanges) {
        // 只修改了头像，已保存成功
        hasSelectedNewAvatar.value = false
        showToast('头像更新成功')
        setTimeout(() => {
          uni.redirectTo({ url: '/pages/me/card/index' })
        }, 250)
        saving.value = false
        return
      }
    }

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
      // 经纬度由系统自动更新，不再手动提交
      // latitude: hasCoordinates.value ? Number(latitude.value) : null,
      // longitude: hasCoordinates.value ? Number(longitude.value) : null
    }

    console.log('提交的数据:', JSON.stringify(payload, null, 2))

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
      showToast('资料已提交审核')
      setTimeout(() => {
        goBack()
      }, 250)
      return
    }

    applyProfile(nextProfile)
    uni.setStorageSync('userInfo', nextProfile)

    // 重置头像选择标记
    hasSelectedNewAvatar.value = false

    showToast('保存成功')
    setTimeout(() => {
      uni.redirectTo({ url: '/pages/me/card/index' })
    }, 250)
  } catch (err) {
    console.error('保存失败，完整错误:', err)
    console.error('错误代码:', err?.code)
    console.error('错误信息:', err?.message)
    console.error('错误payload:', err?.payload)

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

.review-notice {
  margin: -20rpx 0 24rpx;
  padding: 18rpx 22rpx;
  border-radius: 12rpx;
  background: #fff7ed;
  border: 1rpx solid #fed7aa;
}

.review-notice-text {
  color: #9a3412;
  font-size: 24rpx;
  line-height: 34rpx;
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

.location-field {
  min-height: 112rpx;
  padding: 18rpx 18rpx 18rpx 24rpx;
  border: 1rpx solid #e7ecf3;
  border-radius: 12rpx;
  background: #f6f8fc;
  box-sizing: border-box;
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.location-content {
  flex: 1;
  min-width: 0;
}

.location-value,
.location-tip {
  display: block;
}

.location-value {
  color: #172033;
  font-size: 25rpx;
  line-height: 44rpx;
  word-break: break-all;
  white-space: pre-line;
}

.location-placeholder {
  color: #98a5b8;
}

.location-tip {
  margin-top: 6rpx;
  color: #98a5b8;
  font-size: 20rpx;
  line-height: 28rpx;
}

.location-btn {
  flex-shrink: 0;
  height: 60rpx;
  margin: 0;
  padding: 0 20rpx;
  border: 0;
  border-radius: 30rpx;
  background: #e8f0ff;
  color: #2563eb;
  font-size: 23rpx;
  line-height: 60rpx;
  font-weight: 500;
}

.location-btn::after {
  border: 0;
}

.location-btn[disabled] {
  opacity: 0.6;
}

.location-btn-active {
  opacity: 0.76;
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
