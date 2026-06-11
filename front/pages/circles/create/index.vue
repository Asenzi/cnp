<template>
  <view class="create-circle-page">
    <scroll-view class="main-scroll" scroll-y :show-scrollbar="false">
      <view class="content-wrap">
        <CreateCoverUploader v-model="form.coverUrl" />
        <CreateAvatarUploader v-model="form.avatarUrl" />

        <view v-if="!realNameVerified || !isCircleOwner" class="verify-notice-card">
          <text class="verify-notice-title">{{ createRequirementTitle }}</text>
          <text class="verify-notice-desc">{{ createRequirementDesc }}</text>
        </view>

        <CreateBasicInfoCard
          :name="form.name"
          :industry="form.industry"
          :description="form.description"
          @update:name="form.name = $event"
          @update:industry="form.industry = $event"
          @update:description="form.description = $event"
          @openIndustryPicker="industryPickerVisible = true"
        />

        <CreateJoinMechanismCard
          :join-type="form.joinType"
          :price="form.price"
          :join-type-options="joinTypeOptions"
          @update:joinType="form.joinType = $event"
          @update:price="form.price = normalizePrice($event)"
        />

        <CreateRulesCard
          :rules="form.rules"
          @update:rules="form.rules = $event"
        />
      </view>
    </scroll-view>

    <CreateBottomAction :loading="submitting" :text="submitButtonText" @submit="onSubmit" />

    <IndustryPickerPanel
      :visible="industryPickerVisible"
      :value="form.industry"
      @close="industryPickerVisible = false"
      @confirm="onConfirmIndustry"
    />
  </view>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { createCircle, uploadCircleAvatar, uploadCircleCover } from '../../../api/circle'
import { getCurrentUserProfile } from '../../../api/user'
import CreateAvatarUploader from './components/CreateAvatarUploader.vue'
import CreateBasicInfoCard from './components/CreateBasicInfoCard.vue'
import CreateBottomAction from './components/CreateBottomAction.vue'
import CreateCoverUploader from './components/CreateCoverUploader.vue'
import CreateJoinMechanismCard from './components/CreateJoinMechanismCard.vue'
import CreateRulesCard from './components/CreateRulesCard.vue'
import IndustryPickerPanel from './components/IndustryPickerPanel.vue'
import {
  defaultCircleAvatar,
  defaultCoverImage,
  joinTypeOptions
} from './modules/create-circle-form'

const submitting = ref(false)
const industryPickerVisible = ref(false)

const form = reactive({
  coverUrl: defaultCoverImage,
  avatarUrl: defaultCircleAvatar,
  name: '',
  industry: '',
  description: '',
  joinType: 'paid',
  price: '',
  rules: '',
  needPostReview: false
})
const currentUser = ref({})

const parseStoredUserInfo = () => {
  const stored = uni.getStorageSync('userInfo')
  if (typeof stored === 'string') {
    try {
      return JSON.parse(stored)
    } catch (err) {
      return {}
    }
  }
  return stored && typeof stored === 'object' ? stored : {}
}

currentUser.value = parseStoredUserInfo()

const realNameVerified = computed(() => Boolean(currentUser.value?.is_verified))
const isCircleOwner = computed(() => Boolean(currentUser.value?.is_circle_owner))
const createRequirementTitle = computed(() => {
  if (!realNameVerified.value) return '完成实名认证后才可创建圈子'
  return '开通圈主身份后才可创建圈子'
})
const createRequirementDesc = computed(() => {
  if (!realNameVerified.value) return '请先完成实名认证，再继续创建圈子。'
  return '圈主身份一次付费、永久有效，支付成功后即可创建圈子。'
})
const submitButtonText = computed(() => {
  if (!realNameVerified.value) return '完成实名认证后可创建圈子'
  if (!isCircleOwner.value) return '开通圈主身份'
  return '立即创建圈子'
})

const normalizePrice = (value) => {
  const raw = String(value || '').replace(/[^\d.]/g, '')
  const parts = raw.split('.')
  if (parts.length <= 1) {
    return raw
  }
  return `${parts[0]}.${parts.slice(1).join('').slice(0, 2)}`
}

const showToast = (title) => {
  uni.showToast({
    title,
    icon: 'none'
  })
}

const hasToken = () => {
  const token = uni.getStorageSync('token')
  return typeof token === 'string' ? token.trim().length > 0 : Boolean(token)
}

const loadCurrentUserProfile = async () => {
  const token = uni.getStorageSync('token')
  if (!token) {
    currentUser.value = {}
    return
  }

  try {
    const profile = await getCurrentUserProfile()
    currentUser.value = profile || {}
  } catch (err) {
    currentUser.value = {}
  }
}

const isLocalTempFilePath = (value) => {
  const normalized = String(value || '').trim()
  if (!normalized) {
    return false
  }
  if (/^https?:\/\/tmp\//i.test(normalized)) {
    return true
  }
  if (/^https?:\/\//i.test(normalized)) {
    return false
  }
  if (normalized.startsWith('/static/')) {
    return false
  }
  return true
}

const validateForm = () => {
  if (!hasToken()) {
    showToast('请先登录')
    setTimeout(() => {
      uni.navigateTo({
        url: '/pages/auth/login/index'
      })
    }, 260)
    return false
  }
  if (!realNameVerified.value) {
    showToast('完成实名认证后才可创建圈子')
    setTimeout(() => {
      uni.navigateTo({
        url: '/pages/me/auth/realname/index'
      })
    }, 260)
    return false
  }
  if (!isCircleOwner.value) {
    showToast('请先开通圈主身份')
    setTimeout(() => {
      uni.navigateTo({
        url: '/pages/me/circle-owner/apply/index'
      })
    }, 260)
    return false
  }
  if (!form.name.trim()) {
    showToast('请输入圈子名称')
    return false
  }
  if (!form.industry.trim()) {
    showToast('请选择行业')
    return false
  }
  if (!form.description.trim()) {
    showToast('请输入圈子简介')
    return false
  }
  if (form.joinType === 'paid') {
    const value = Number(form.price)
    if (!form.price || Number.isNaN(value) || value <= 0) {
      showToast('请输入有效的付费金额')
      return false
    }
  }
  return true
}

onShow(() => {
  loadCurrentUserProfile()
})

const onConfirmIndustry = (industry) => {
  form.industry = industry
  industryPickerVisible.value = false
}

const onSubmit = async () => {
  if (submitting.value) {
    return
  }
  if (!validateForm()) {
    return
  }

  submitting.value = true
  try {
    let finalCoverUrl = String(form.coverUrl || '').trim()
    if (isLocalTempFilePath(finalCoverUrl)) {
      const uploadResult = await uploadCircleCover(finalCoverUrl, `${Date.now()}-circle-cover`)
      finalCoverUrl = String(uploadResult?.path || uploadResult?.url || '').trim()
      if (!finalCoverUrl) {
        throw new Error('圈子封面上传失败')
      }
    }

    let finalAvatarUrl = String(form.avatarUrl || '').trim()
    if (isLocalTempFilePath(finalAvatarUrl)) {
      const uploadResult = await uploadCircleAvatar(finalAvatarUrl, `${Date.now()}-circle-avatar`)
      finalAvatarUrl = String(uploadResult?.path || uploadResult?.url || '').trim()
      if (!finalAvatarUrl) {
        throw new Error('圈子头像上传失败')
      }
    }
    if (!finalAvatarUrl) {
      finalAvatarUrl = finalCoverUrl
    }

    const payload = {
      name: String(form.name || '').trim(),
      industry_label: String(form.industry || '').trim(),
      description: String(form.description || '').trim(),
      cover_url: finalCoverUrl,
      avatar_url: finalAvatarUrl,
      join_type: String(form.joinType || 'free'),
      join_price: form.joinType === 'paid' ? Number(form.price || 0) : 0,
      rules_text: String(form.rules || '').trim() || null,
      need_post_review: Boolean(form.needPostReview)
    }

    const created = await createCircle(payload)
    const circleCode = String(created?.circle_code || '').trim()

    showToast('圈子创建成功')

    // 成功后不重置 submitting，防止重复提交
    setTimeout(() => {
      if (circleCode) {
        uni.navigateTo({
          url: `/pages/circles/detail/index?code=${encodeURIComponent(circleCode)}`
        })
        return
      }
      uni.navigateTo({
        url: '/pages/circles/detail/index'
      })
    }, 260)
  } catch (err) {
    // 只有失败时才重置 submitting
    submitting.value = false

    const statusCode = Number(err?.statusCode || 0)
    if (statusCode === 401) {
      showToast('请先登录')
      setTimeout(() => {
        uni.navigateTo({
          url: '/pages/auth/login/index'
        })
      }, 200)
      return
    }
    showToast(err?.message || '创建圈子失败，请稍后重试')
  }
}
</script>

<style scoped>
.create-circle-page {
  min-height: 100vh;
  background: #f6f6f8;
}

.main-scroll {
  height: 100vh;
}

.content-wrap {
  padding: 16rpx 0 calc(120rpx + env(safe-area-inset-bottom));
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.verify-notice-card {
  margin: 0 32rpx;
  padding: 18rpx 20rpx;
  border-radius: 12rpx;
  background: rgba(37, 99, 235, 0.04);
  border: 1rpx solid rgba(37, 99, 235, 0.1);
  display: flex;
  flex-direction: column;
  gap: 6rpx;
}

.verify-notice-title {
  font-size: 26rpx;
  line-height: 1.4;
  font-weight: 600;
  color: #2563eb;
}

.verify-notice-desc {
  font-size: 22rpx;
  line-height: 1.4;
  color: #64748b;
}

@media (prefers-color-scheme: dark) {
  .create-circle-page {
    background: #111621;
  }

  .verify-notice-card {
    background: rgba(59, 130, 246, 0.08);
    border-color: rgba(59, 130, 246, 0.15);
  }

  .verify-notice-title {
    color: #60a5fa;
  }

  .verify-notice-desc {
    color: #94a3b8;
  }
}
</style>
