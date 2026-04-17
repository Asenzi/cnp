<template>
  <view class="create-circle-page">
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
          :join-type="form.joinType"
          :price="form.price"
          :join-type-options="joinTypeOptions"
          @update:joinType="form.joinType = $event"
          @update:price="form.price = normalizePrice($event)"
        />

        <CreateRulesCard
          :rules="form.rules"
          :need-post-review="form.needPostReview"
          @update:rules="form.rules = $event"
          @update:needPostReview="form.needPostReview = $event"
        />
      </view>
    </scroll-view>

    <CreateBottomAction :loading="submitting" @submit="onSubmit" />
  </view>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { createCircle, uploadCircleAvatar, uploadCircleCover } from '../../../api/circle'
import CreateAvatarUploader from './components/CreateAvatarUploader.vue'
import CreateBasicInfoCard from './components/CreateBasicInfoCard.vue'
import CreateBottomAction from './components/CreateBottomAction.vue'
import CreateCoverUploader from './components/CreateCoverUploader.vue'
import CreateJoinMechanismCard from './components/CreateJoinMechanismCard.vue'
import CreateRulesCard from './components/CreateRulesCard.vue'
import {
  defaultCircleAvatar,
  defaultCoverImage,
  industryOptions,
  joinTypeOptions
} from './modules/create-circle-form'

const submitting = ref(false)

const form = reactive({
  coverUrl: defaultCoverImage,
  avatarUrl: defaultCircleAvatar,
  name: '',
  industry: '',
  description: '',
  joinType: 'free',
  price: '',
  rules: '',
  needPostReview: false
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

const isLocalTempFilePath = (value) => {
  const normalized = String(value || '').trim()
  if (!normalized) {
    return false
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
  if (form.joinType === 'paid') {
    const value = Number(form.price)
    if (!form.price || Number.isNaN(value) || value <= 0) {
      showToast('请输入有效的付费金额')
      return false
    }
  }
  return true
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
  } finally {
    submitting.value = false
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
  padding: 24rpx 0 calc(132rpx + env(safe-area-inset-bottom));
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

@media (prefers-color-scheme: dark) {
  .create-circle-page {
    background: #111621;
  }
}
</style>
