<template>
  <view class="edit-circle-page">
    <scroll-view class="main-scroll" scroll-y :show-scrollbar="false">
      <view class="content-wrap">
        <CreateCoverUploader v-model="form.coverUrl" />
        <CreateAvatarUploader v-model="form.avatarUrl" />

        <CreateBasicInfoCard
          :name="form.name"
          :industry="form.industry"
          :description="form.description"
          :industry-options="industryOptions"
          @update:name="form.name = $event"
          @update:industry="form.industry = $event"
          @update:description="form.description = $event"
        />

        <CreateJoinMechanismCard
          :price="form.price"
          @update:price="form.price = normalizePrice($event)"
        />

        <CreateRulesCard
          :rules="form.rules"
          @update:rules="form.rules = $event"
        />
      </view>
    </scroll-view>

    <CreateBottomAction
      :loading="submitting"
      loading-text="保存中..."
      text="保存修改"
      @submit="onSubmit"
    />
  </view>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'

import { getCircleDetail, updateCircle, uploadCircleAvatar, uploadCircleCover } from '../../../api/circle'
import CreateAvatarUploader from '../create/components/CreateAvatarUploader.vue'
import CreateBasicInfoCard from '../create/components/CreateBasicInfoCard.vue'
import CreateBottomAction from '../create/components/CreateBottomAction.vue'
import CreateCoverUploader from '../create/components/CreateCoverUploader.vue'
import CreateJoinMechanismCard from '../create/components/CreateJoinMechanismCard.vue'
import CreateRulesCard from '../create/components/CreateRulesCard.vue'
import {
  defaultCircleAvatar,
  defaultCoverImage,
  industryOptions
} from '../create/modules/create-circle-form'
import { getApiBaseUrl } from '../../../utils/request'

const circleCode = ref('')
const submitting = ref(false)
const loading = ref(false)

const form = reactive({
  coverUrl: defaultCoverImage,
  avatarUrl: defaultCircleAvatar,
  name: '',
  industry: '',
  description: '',
  joinType: 'paid',
  price: '98',
  rules: ''
})
const joinPriceTiers = [98, 198, 398, 598, 980, 1980, 3980, 5980, 9980]

const showToast = (title) => {
  uni.showToast({
    title,
    icon: 'none'
  })
}

const normalizePrice = (value) => {
  const raw = String(value || '').replace(/[^\d.]/g, '')
  const parts = raw.split('.')
  if (parts.length <= 1) {
    return raw
  }
  return `${parts[0]}.${parts.slice(1).join('').slice(0, 2)}`
}

const normalizeStoredFilePath = (value) => {
  const normalized = String(value || '').trim()
  if (!normalized) {
    return ''
  }
  const baseUrl = getApiBaseUrl()
  if (normalized.startsWith(`${baseUrl}/static/`)) {
    return normalized.replace(baseUrl, '')
  }
  return normalized
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
  const value = Number(form.price)
  if (!joinPriceTiers.includes(value)) {
    showToast('请输入有效的付费金额')
    return false
  }
  return true
}

const applyCircleDetail = (detail = {}) => {
  const joinPrice = Number(detail?.join_price || 0)
  form.coverUrl = String(detail?.cover_url || '').trim() || defaultCoverImage
  form.avatarUrl = String(detail?.avatar_url || '').trim() || form.coverUrl || defaultCircleAvatar
  form.name = String(detail?.name || '').trim()
  form.industry = String(detail?.industry_label || '').trim()
  form.description = String(detail?.description || '').trim()
  form.joinType = 'paid'
  form.price = joinPriceTiers.includes(joinPrice) ? normalizePrice(joinPrice.toFixed(2)) : '98'
  form.rules = String(detail?.rules_text || '').trim()
}

const loadCircleDetail = async () => {
  if (!circleCode.value || loading.value) {
    return
  }
  loading.value = true
  try {
    const detail = await getCircleDetail(circleCode.value)
    applyCircleDetail(detail)
  } catch (err) {
    showToast(err?.message || '圈子详情加载失败')
    setTimeout(() => {
      uni.navigateBack()
    }, 220)
  } finally {
    loading.value = false
  }
}

const onSubmit = async () => {
  if (submitting.value || loading.value) {
    return
  }
  if (!circleCode.value) {
    showToast('圈子编号缺失')
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
    } else {
      finalCoverUrl = normalizeStoredFilePath(finalCoverUrl)
    }

    let finalAvatarUrl = String(form.avatarUrl || '').trim()
    if (isLocalTempFilePath(finalAvatarUrl)) {
      const uploadResult = await uploadCircleAvatar(finalAvatarUrl, `${Date.now()}-circle-avatar`)
      finalAvatarUrl = String(uploadResult?.path || uploadResult?.url || '').trim()
      if (!finalAvatarUrl) {
        throw new Error('圈子头像上传失败')
      }
    } else {
      finalAvatarUrl = normalizeStoredFilePath(finalAvatarUrl)
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
      join_type: 'paid',
      join_price: Number(form.price || 0),
      rules_text: String(form.rules || '').trim() || null
    }

    const result = await updateCircle(circleCode.value, payload)
    const review = result && typeof result._review === 'object'
      ? result._review
      : null

    if (review?.review_required) {
      showToast('圈子资料已提交审核')
      setTimeout(() => {
        uni.navigateBack()
      }, 260)
      return
    }

    showToast('圈子资料更新成功')
    setTimeout(() => {
      uni.navigateBack()
    }, 260)
  } catch (err) {
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
    showToast(err?.message || '圈子资料更新失败，请稍后重试')
  } finally {
    submitting.value = false
  }
}

onLoad((options = {}) => {
  circleCode.value = String(options?.code || '').trim()
  if (!circleCode.value) {
    showToast('圈子编号缺失')
    setTimeout(() => {
      uni.navigateBack()
    }, 220)
    return
  }
  loadCircleDetail()
})
</script>

<style scoped>
.edit-circle-page {
  min-height: 100vh;
  background: #f6f6f8;
}

.main-scroll {
  height: 100vh;
}

.content-wrap {
  padding: 24rpx 0 calc(132rpx + env(safe-area-inset-bottom));
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.notice-card {
  margin: 0 32rpx;
  padding: 22rpx 24rpx;
  border-radius: 20rpx;
  background: linear-gradient(135deg, rgba(26, 87, 219, 0.12) 0%, rgba(59, 130, 246, 0.08) 100%);
  border: 1rpx solid rgba(26, 87, 219, 0.16);
}

.notice-title {
  display: block;
  color: #0f172a;
  font-size: 30rpx;
  line-height: 40rpx;
  font-weight: 700;
}

.notice-text {
  display: block;
  margin-top: 10rpx;
  color: #475569;
  font-size: 24rpx;
  line-height: 34rpx;
}

@media (prefers-color-scheme: dark) {
  .edit-circle-page {
    background: #111621;
  }

  .notice-card {
    background: rgba(30, 41, 59, 0.92);
    border-color: rgba(59, 130, 246, 0.3);
  }

  .notice-title {
    color: #f8fafc;
  }

  .notice-text {
    color: #cbd5e1;
  }
}
</style>
