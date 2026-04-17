<template>
  <view class="result-page">
    <view class="page-shell">
      <view class="main-content">
        <view class="center-wrap">
          <view class="icon-wrap">
            <view class="icon-glow"></view>
            <view class="icon-core">
              <image class="icon-image" mode="aspectFit" src="/static/me-icons/verified-white.png" />
            </view>
          </view>

          <view class="title-wrap">
            <text class="main-title">{{ mainTitle }}</text>
            <text class="main-desc">{{ descText }}</text>
          </view>

          <view class="status-card">
            <view class="status-icon-box">
              <image class="status-icon" mode="aspectFit" src="/static/me-icons/shield-person-primary.png" />
            </view>
            <view class="status-copy">
              <text class="status-name">{{ typeMeta.title }}</text>
              <text class="status-sub">{{ typeMeta.sub }}</text>
            </view>
            <text class="status-tag">{{ statusTag }}</text>
          </view>
        </view>
      </view>

      <view class="footer-bar">
        <view class="btn-primary" hover-class="btn-primary-hover" @tap="backToMe">
          <text class="btn-primary-text">返回个人中心</text>
        </view>
        <view class="btn-ghost" hover-class="btn-ghost-hover" @tap="viewDetail">
          <text class="btn-ghost-text">查看提交详情</text>
        </view>
        <view class="safe-space"></view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'

const TYPE_META = {
  enterprise: {
    title: '企业认证',
    sub: '企业资料审核中',
    detailUrl: '/pages/me/auth/enterprise/index'
  },
  real_name: {
    title: '实名认证',
    sub: '实名资料审核中',
    detailUrl: '/pages/me/auth/realname/index'
  },
  business_card: {
    title: '名片认证',
    sub: '名片资料审核中',
    detailUrl: '/pages/me/auth/submit/index?type=business_card'
  }
}

const type = ref('enterprise')
const status = ref('pending')

const typeMeta = computed(() => TYPE_META[type.value] || TYPE_META.enterprise)

const isApproved = computed(() => status.value === 'approved')

const mainTitle = computed(() => (isApproved.value ? '实名认证成功' : '已提交审核'))

const descText = computed(() => {
  if (isApproved.value && type.value === 'real_name') {
    return '您已完成腾讯云实人核身，当前账号已完成实名认证。'
  }
  return '您的认证资料已成功提交，工作人员将在1-3个工作日内完成审核，请耐心等待。'
})

const statusTag = computed(() => (isApproved.value ? '已完成' : '处理中'))

const backToMe = () => {
  uni.switchTab({
    url: '/pages/tab/me/index'
  })
}

const viewDetail = () => {
  uni.redirectTo({
    url: typeMeta.value.detailUrl
  })
}

onLoad((query) => {
  const rawType = String(query?.type || '').trim()
  if (rawType && TYPE_META[rawType]) {
    type.value = rawType
  }
  const rawStatus = String(query?.status || '').trim()
  if (rawStatus) {
    status.value = rawStatus
  }
})
</script>

<style scoped>
.result-page {
  min-height: 100vh;
  background: #f6f6f8;
}

.page-shell {
  min-height: 100vh;
  max-width: 448px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  background: #ffffff;
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 64px 24px 0;
  box-sizing: border-box;
}

.center-wrap {
  width: 100%;
  max-width: 360px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.icon-wrap {
  position: relative;
  margin-bottom: 32px;
}

.icon-glow {
  position: absolute;
  inset: -16px;
  border-radius: 999px;
  background: rgba(26, 87, 219, 0.16);
  filter: blur(20px);
}

.icon-core {
  position: relative;
  width: 96px;
  height: 96px;
  border-radius: 999px;
  background: #1a57db;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 14px 28px rgba(26, 87, 219, 0.28);
}

.icon-image {
  width: 52px;
  height: 52px;
}

.title-wrap {
  text-align: center;
}

.main-title {
  display: block;
  color: #0f172a;
  font-size: 28px;
  font-weight: 700;
  line-height: 1.2;
}

.main-desc {
  display: block;
  margin-top: 14px;
  color: #64748b;
  font-size: 16px;
  line-height: 1.75;
}

.status-card {
  margin-top: 48px;
  width: 100%;
  padding: 16px;
  border-radius: 14px;
  border: 1px solid rgba(26, 87, 219, 0.12);
  background: rgba(26, 87, 219, 0.06);
  display: flex;
  align-items: center;
  gap: 12px;
  box-sizing: border-box;
}

.status-icon-box {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: rgba(26, 87, 219, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.status-icon {
  width: 22px;
  height: 22px;
}

.status-copy {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.status-name {
  color: #0f172a;
  font-size: 14px;
  font-weight: 700;
}

.status-sub {
  margin-top: 3px;
  color: #64748b;
  font-size: 12px;
}

.status-tag {
  color: #1a57db;
  font-size: 12px;
  font-weight: 600;
}

.footer-bar {
  padding: 16px 24px;
  border-top: 1px solid #e2e8f0;
  background: rgba(255, 255, 255, 0.82);
  backdrop-filter: blur(8px);
}

.btn-primary,
.btn-ghost {
  width: 100%;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-primary {
  height: 56px;
  background: #1a57db;
  box-shadow: 0 10px 20px rgba(26, 87, 219, 0.22);
}

.btn-primary-hover {
  background: rgba(26, 87, 219, 0.9);
}

.btn-primary-text {
  color: #ffffff;
  font-size: 16px;
  font-weight: 700;
}

.btn-ghost {
  margin-top: 12px;
  height: 48px;
  background: rgba(26, 87, 219, 0.1);
}

.btn-ghost-hover {
  background: rgba(26, 87, 219, 0.18);
}

.btn-ghost-text {
  color: #1a57db;
  font-size: 14px;
  font-weight: 600;
}

.safe-space {
  height: calc(8px + env(safe-area-inset-bottom));
}

@media (prefers-color-scheme: dark) {
  .result-page {
    background: #111621;
  }

  .page-shell {
    background: #111621;
  }

  .main-title,
  .status-name {
    color: #f1f5f9;
  }

  .main-desc,
  .status-sub {
    color: #94a3b8;
  }

  .status-card {
    background: rgba(26, 87, 219, 0.12);
    border-color: rgba(26, 87, 219, 0.2);
  }

  .footer-bar {
    border-top-color: #1e293b;
    background: rgba(17, 22, 33, 0.82);
  }
}
</style>
