<template>
  <view class="auth-page">
    <view class="page-shell">
      <view class="main-content">
        <view class="heading-wrap">
          <text class="heading-title">选择认证方式</text>
          <text class="heading-desc">完成认证，解锁圈脉链更多职场权益，提升社交公信力</text>
        </view>

        <view class="card-stack">
          <view v-for="card in cards" :key="card.type" class="auth-card">
            <view class="card-icon-box">
              <image class="card-icon" mode="aspectFit" :src="card.icon" />
            </view>
            <view class="card-copy">
              <text class="card-title">{{ card.title }}</text>
              <text class="card-desc">{{ card.desc }}</text>

              <view class="status-row">
                <view v-if="card.status === VERIFICATION_STATUS.PENDING" class="status-pending">
                  <image class="status-verified-icon" mode="aspectFit" src="/static/me-icons/verified-emerald.png" />
                  <text class="status-pending-text">{{ card.statusText }}</text>
                </view>
                <view v-else-if="card.status === VERIFICATION_STATUS.APPROVED" class="status-approved">
                  <image class="status-verified-icon" mode="aspectFit" src="/static/me-icons/verified-emerald.png" />
                  <text class="status-approved-text">{{ card.statusText }}</text>
                </view>
                <text v-else-if="card.status === VERIFICATION_STATUS.REJECTED" class="status-rejected">
                  {{ card.statusText }}
                </text>
                <text v-else class="status-tag">{{ card.statusText }}</text>
              </view>

              <text v-if="card.rejectReason" class="reject-text">驳回原因：{{ card.rejectReason }}</text>
            </view>

            <view class="card-action">
              <view v-if="card.actionDisabled" class="action-btn-disabled" @tap="onDisabledTap(card)">
                <text class="action-btn-disabled-text">{{ card.actionText }}</text>
              </view>
              <view v-else class="action-btn" hover-class="action-btn-hover" @tap="goSubmit(card.type)">
                <text class="action-btn-text">{{ card.actionText }}</text>
              </view>
            </view>
          </view>
        </view>

        <view class="notice-card">
          <image class="notice-icon" mode="aspectFit" src="/static/me-icons/shield-person-primary.png" />
          <view class="notice-copy">
            <text class="notice-title">隐私安全承诺</text>
            <text class="notice-desc">
              圈脉链承诺保护您的隐私信息。认证资料仅用于身份核实，不会在未经授权的情况下透露给第三方。
            </text>
          </view>
        </view>
      </view>

      <view class="page-footer">
        <text class="footer-text">由 圈脉链 提供安全认证服务</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { getMyVerificationOverview } from '../../../api/verification'
import {
  VERIFICATION_STATUS,
  getActionText,
  getStatusText,
  isActionDisabled,
  normalizeOverviewItems,
  verificationTypeList
} from './modules/verification-types'

const loading = ref(false)
const overview = ref({
  is_verified: false,
  items: []
})
const itemMap = ref(normalizeOverviewItems([]))

const cards = computed(() =>
  verificationTypeList.map((meta) => {
    const item = itemMap.value?.[meta.type] || {
      status: VERIFICATION_STATUS.NOT_SUBMITTED,
      reject_reason: ''
    }
    const status = item.status || VERIFICATION_STATUS.NOT_SUBMITTED
    return {
      ...meta,
      status,
      statusText: getStatusText(status),
      actionText: getActionText(status),
      actionDisabled: isActionDisabled(status),
      rejectReason: item.reject_reason || ''
    }
  })
)

const showToast = (title) => {
  uni.showToast({
    title,
    icon: 'none'
  })
}

const loadOverview = async () => {
  if (loading.value) {
    return
  }

  loading.value = true
  try {
    const data = await getMyVerificationOverview()
    overview.value = {
      is_verified: Boolean(data?.is_verified),
      items: Array.isArray(data?.items) ? data.items : []
    }
    itemMap.value = normalizeOverviewItems(overview.value.items)
  } catch (err) {
    if (err?.statusCode === 401) {
      showToast('请先登录')
      setTimeout(() => {
        uni.navigateTo({
          url: '/pages/auth/login/index'
        })
      }, 200)
      return
    }
    showToast(err?.message || '加载认证状态失败')
  } finally {
    loading.value = false
  }
}

const goSubmit = (type) => {
  if (type === 'enterprise') {
    uni.navigateTo({
      url: '/pages/me/auth/enterprise/index'
    })
    return
  }

  if (type === 'real_name') {
    uni.navigateTo({
      url: '/pages/me/auth/realname/index'
    })
    return
  }

  uni.navigateTo({
    url: `/pages/me/auth/submit/index?type=${encodeURIComponent(type)}`
  })
}

const onDisabledTap = (card) => {
  if (card.status === VERIFICATION_STATUS.APPROVED) {
    showToast('该认证已通过')
    return
  }
  if (card.status === VERIFICATION_STATUS.PENDING) {
    showToast('资料审核中，请耐心等待')
  }
}

onShow(() => {
  loadOverview()
})
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  background: #f6f6f8;
  color: #0f172a;
}

.page-shell {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f6f6f8;
}

.main-content {
  flex: 1;
  width: 100%;
  max-width: 1344rpx;
  margin: 0 auto;
  padding: 48rpx 32rpx;
  box-sizing: border-box;
}

.heading-wrap {
  margin-bottom: 32rpx;
}

.heading-title {
  display: block;
  margin-bottom: 12rpx;
  font-size: 48rpx;
  line-height: 1.2;
  font-weight: 700;
  color: #0f172a;
}

.heading-desc {
  display: block;
  font-size: 30rpx;
  line-height: 1.6;
  color: #475569;
}

.card-stack {
  display: flex;
  flex-direction: column;
  gap: 32rpx;
}

.auth-card {
  display: flex;
  align-items: center;
  gap: 24rpx;
  border-radius: 24rpx;
  border: 1rpx solid #f1f5f9;
  background: #ffffff;
  padding: 28rpx;
  box-shadow: 0 4rpx 12rpx rgba(15, 23, 42, 0.04);
}

.card-icon-box {
  width: 96rpx;
  height: 96rpx;
  border-radius: 24rpx;
  background: rgba(26, 87, 219, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.card-icon {
  width: 56rpx;
  height: 56rpx;
}

.card-copy {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.card-title {
  display: block;
  font-size: 34rpx;
  line-height: 1.2;
  font-weight: 700;
  color: #0f172a;
}

.card-desc {
  display: block;
  margin-top: 8rpx;
  font-size: 26rpx;
  line-height: 1.5;
  color: #64748b;
}

.status-row {
  margin-top: 12rpx;
  display: flex;
  align-items: center;
}

.status-tag,
.status-rejected {
  display: inline-block;
  padding: 4rpx 12rpx;
  border-radius: 8rpx;
  font-size: 24rpx;
  line-height: 1.4;
}

.status-tag {
  color: #64748b;
  background: #f1f5f9;
}

.status-rejected {
  color: #dc2626;
  background: rgba(220, 38, 38, 0.08);
}

.status-pending,
.status-approved {
  display: inline-flex;
  align-items: center;
  gap: 6rpx;
  padding: 4rpx 12rpx;
  border-radius: 8rpx;
}

.status-pending {
  background: #ecfdf5;
}

.status-approved {
  background: rgba(5, 150, 105, 0.12);
}

.status-verified-icon {
  width: 20rpx;
  height: 20rpx;
}

.status-pending-text,
.status-approved-text {
  font-size: 24rpx;
  line-height: 1.4;
  font-weight: 500;
}

.status-pending-text {
  color: #059669;
}

.status-approved-text {
  color: #047857;
}

.reject-text {
  margin-top: 8rpx;
  font-size: 22rpx;
  color: #dc2626;
  line-height: 1.4;
}

.card-action {
  margin-left: 8rpx;
  flex-shrink: 0;
}

.action-btn,
.action-btn-disabled {
  min-width: 156rpx;
  height: 68rpx;
  padding-left: 24rpx;
  padding-right: 24rpx;
  border-radius: 999rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.action-btn {
  background: #1a57db;
}

.action-btn-hover {
  background: #1d4ed8;
}

.action-btn-text {
  font-size: 26rpx;
  font-weight: 600;
  color: #ffffff;
}

.action-btn-disabled {
  background: #f1f5f9;
}

.action-btn-disabled-text {
  font-size: 26rpx;
  font-weight: 600;
  color: #94a3b8;
}

.notice-card {
  margin-top: 72rpx;
  padding: 32rpx;
  border-radius: 24rpx;
  border: 1rpx solid rgba(26, 87, 219, 0.1);
  background: rgba(26, 87, 219, 0.05);
  display: flex;
  align-items: flex-start;
  gap: 16rpx;
}

.notice-icon {
  width: 40rpx;
  height: 40rpx;
  flex-shrink: 0;
  margin-top: 2rpx;
}

.notice-copy {
  flex: 1;
}

.notice-title {
  display: block;
  font-size: 28rpx;
  font-weight: 700;
  color: #0f172a;
}

.notice-desc {
  display: block;
  margin-top: 8rpx;
  font-size: 24rpx;
  line-height: 1.6;
  color: #64748b;
}

.page-footer {
  margin-top: auto;
  padding: 64rpx 32rpx calc(64rpx + env(safe-area-inset-bottom));
  text-align: center;
}

.footer-text {
  font-size: 24rpx;
  color: #94a3b8;
}

@media (prefers-color-scheme: dark) {
  .auth-page,
  .page-shell {
    background: #111621;
    color: #f1f5f9;
  }

  .heading-title,
  .card-title,
  .notice-title {
    color: #f1f5f9;
  }

  .heading-desc,
  .card-desc,
  .notice-desc {
    color: #94a3b8;
  }

  .auth-card {
    background: rgba(15, 23, 42, 0.6);
    border-color: #1e293b;
    box-shadow: none;
  }

  .card-icon-box {
    background: rgba(26, 87, 219, 0.2);
  }

  .status-tag {
    background: #1e293b;
    color: #94a3b8;
  }

  .status-rejected {
    background: rgba(220, 38, 38, 0.2);
  }

  .status-pending {
    background: rgba(5, 150, 105, 0.2);
  }

  .status-approved {
    background: rgba(5, 150, 105, 0.3);
  }

  .status-pending-text,
  .status-approved-text {
    color: #6ee7b7;
  }

  .action-btn-disabled {
    background: #1e293b;
  }

  .action-btn-disabled-text {
    color: #64748b;
  }

  .notice-card {
    background: rgba(26, 87, 219, 0.1);
    border-color: rgba(26, 87, 219, 0.2);
  }

  .footer-text {
    color: #475569;
  }
}
</style>
