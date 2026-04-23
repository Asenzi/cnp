<template>
  <view>
    <view class="profile-row">
      <view class="avatar-wrap">
        <image class="avatar" mode="aspectFill" :src="displayAvatar" />
        <view v-if="isVerified" class="verified-badge">
          <image class="verified-icon-img" mode="aspectFit" src="/static/me-icons/verified-white.png" />
        </view>
      </view>

      <view class="profile-info">
        <view class="name-row">
          <text class="name">{{ displayName }}</text>
          <view class="edit-btn" @tap="$emit('edit')">
            <image class="edit-icon-img" mode="aspectFit" src="/static/icon/edit.png" />
          </view>
        </view>

        <view class="id-row">
          <text class="id-text">ID: {{ displayUserId }}</text>
        </view>

        <view class="meta-row">
          <text class="meta-text">{{ displayMetaLine }}</text>
        </view>
      </view>
    </view>

    <view class="intro-card">
      <text class="intro-text">{{ displayIntro }}</text>
    </view>

    <view class="stats-row" :class="{ 'stats-row-compact': withMemberCard }">
      <view class="stat-card stat-card-click" hover-class="stat-card-active" @tap="$emit('open-circles')">
        <text class="stat-value" :class="{ 'stat-value-muted': displayCircleCount === '--' }">{{ displayCircleCount }}</text>
        <text class="stat-label">我的圈子</text>
      </view>
      <!-- 积分功能暂时隐藏
      <view class="stat-card stat-card-click" hover-class="stat-card-active" @tap="$emit('open-points')">
        <text class="stat-value" :class="{ 'stat-value-muted': displayPoints === '--' }">{{ displayPoints }}</text>
        <text class="stat-label">积分</text>
      </view>
      -->
      <view class="stat-card stat-card-click" hover-class="stat-card-active" @tap="$emit('open-wallet')">
        <text class="stat-value stat-value-primary" :class="{ 'stat-value-muted': displayBalance === '--' }">
          {{ displayBalance }}
        </text>
        <text class="stat-label">账户余额</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  userInfo: {
    type: Object,
    default: () => ({})
  },
  withMemberCard: {
    type: Boolean,
    default: false
  }
})

defineEmits(['edit', 'open-circles', 'open-wallet'])

const DEFAULT_AVATAR = '/static/logo.png'

const displayAvatar = computed(() => {
  const avatar = typeof props.userInfo?.avatar_url === 'string' ? props.userInfo.avatar_url.trim() : ''
  return avatar || DEFAULT_AVATAR
})

const isVerified = computed(() => {
  const value = props.userInfo?.is_verified
  if (typeof value === 'boolean') {
    return value
  }
  if (typeof value === 'number') {
    return value === 1
  }
  if (typeof value === 'string') {
    const normalized = value.trim().toLowerCase()
    return normalized === '1' || normalized === 'true' || normalized === 'yes'
  }
  return false
})

const displayUserId = computed(() => {
  const raw = props.userInfo?.userId ?? props.userInfo?.user_id
  if (typeof raw === 'string') {
    const userId = raw.trim()
    return userId || '--'
  }
  if (typeof raw === 'number' && Number.isFinite(raw)) {
    return String(raw)
  }
  return '--'
})

const displayName = computed(() => {
  const nickname = typeof props.userInfo?.nickname === 'string' ? props.userInfo.nickname.trim() : ''
  if (nickname) {
    return nickname
  }

  const phone = typeof props.userInfo?.phone === 'string' ? props.userInfo.phone : ''
  if (phone.length >= 4) {
    return `用户${phone.slice(-4)}`
  }

  return '已登录用户'
})

const displayIntro = computed(() => {
  const intro = typeof props.userInfo?.intro === 'string' ? props.userInfo.intro.trim() : ''
  if (intro) {
    return intro
  }
  return '欢迎来到圈脉链，完善资料让更多商机找到你'
})

const displayMetaLine = computed(() => {
  const industry =
    typeof props.userInfo?.industry_label === 'string'
      ? props.userInfo.industry_label.trim()
      : ''
  const company =
    typeof props.userInfo?.company_name === 'string'
      ? props.userInfo.company_name.trim()
      : typeof props.userInfo?.company === 'string'
        ? props.userInfo.company.trim()
        : ''

  if (industry && company) {
    return `${industry} | ${company}`
  }

  return industry || company || '该用户暂未完善个人信息'
})

const formatCount = (value) => {
  if (typeof value === 'number' && Number.isFinite(value)) {
    return value.toLocaleString('zh-CN')
  }
  if (typeof value === 'string') {
    const normalized = value.trim()
    if (!normalized) {
      return '--'
    }
    const parsed = Number(normalized)
    if (Number.isFinite(parsed)) {
      return parsed.toLocaleString('zh-CN')
    }
  }
  return '--'
}

const displayCircleCount = computed(() => formatCount(props.userInfo?.circle_count))
// 积分功能暂时隐藏
// const displayPoints = computed(() => {
//   const sourceValue =
//     props.userInfo?.points
//     ?? props.userInfo?.point_count
//     ?? props.userInfo?.score
//     ?? props.userInfo?.integral
//     ?? props.userInfo?.network_count
//   return formatCount(sourceValue)
// })

const displayBalance = computed(() => {
  const value = props.userInfo?.balance
  if (typeof value === 'number' && Number.isFinite(value)) {
    return `¥${value.toLocaleString('zh-CN', { minimumFractionDigits: 0, maximumFractionDigits: 2 })}`
  }
  if (typeof value === 'string') {
    const normalized = value.trim()
    if (!normalized) {
      return '--'
    }
    const parsed = Number(normalized.replace(/^¥/, ''))
    if (Number.isFinite(parsed)) {
      return `¥${parsed.toLocaleString('zh-CN', { minimumFractionDigits: 0, maximumFractionDigits: 2 })}`
    }
  }
  return '--'
})
</script>

<style scoped>
.profile-row {
  display: flex;
  align-items: flex-start;
  gap: 24rpx;
  margin-bottom: 24rpx;
}

.avatar-wrap {
  position: relative;
}

.avatar {
  width: 160rpx;
  height: 160rpx;
  border-radius: 20rpx;
  border: 4rpx solid #ffffff;
  background: #e2e8f0;
}

.verified-badge {
  position: absolute;
  right: -4rpx;
  bottom: -4rpx;
  width: 44rpx;
  height: 44rpx;
  border-radius: 999rpx;
  border: 4rpx solid #ffffff;
  background: #1a57db;
  display: flex;
  align-items: center;
  justify-content: center;
}

.verified-icon-img {
  width: 28rpx;
  height: 28rpx;
}

.profile-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.name-row {
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.name {
  font-size: 36rpx;
  font-weight: 700;
  line-height: 1.2;
}

.edit-btn {
  width: 40rpx;
  height: 40rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.edit-icon-img {
  width: 36rpx;
  height: 36rpx;
}

.id-row {
  margin-top: 2rpx;
}

.id-text {
  display: inline-block;
  font-size: 24rpx;
  font-weight: 600;
  color: #334155;
  line-height: 1.5;
}

.meta-row {
  margin-top: 2rpx;
}

.meta-text {
  display: inline-block;
  font-size: 24rpx;
  font-weight: 600;
  color: #64748b;
  line-height: 1.5;
}

.intro-card {
  margin-bottom: 32rpx;
  padding: 24rpx;
  border: 1rpx solid rgba(26, 87, 219, 0.1);
  border-radius: 20rpx;
  background: rgba(26, 87, 219, 0.05);
}

.intro-text {
  font-size: 26rpx;
  color: #475569;
  line-height: 1.6;
}

.stats-row {
  display: flex;
  gap: 16rpx;
  margin-bottom: 48rpx;
}

.stats-row-compact {
  margin-bottom: 32rpx;
}

.stat-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8rpx;
  padding: 20rpx 12rpx;
  border-radius: 20rpx;
  border: 1rpx solid #f1f5f9;
  background: #ffffff;
  box-shadow: 0 2rpx 8rpx rgba(15, 23, 42, 0.04);
}

.stat-card-click {
  transition: opacity 0.2s ease;
}

.stat-card-active {
  opacity: 0.82;
}

.stat-value {
  font-size: 36rpx;
  font-weight: 700;
  color: #0f172a;
  line-height: 1.2;
}

.stat-value-primary {
  color: #1a57db;
}

.stat-value-muted {
  color: #94a3b8 !important;
}

.stat-label {
  font-size: 22rpx;
  color: #64748b;
  font-weight: 500;
}

@media (prefers-color-scheme: dark) {
  .avatar {
    border-color: #1e293b;
    background: #334155;
  }

  .verified-badge {
    border-color: #1e293b;
  }

  .name,
  .stat-value {
    color: #f1f5f9;
  }

  .id-text {
    color: #cbd5e1;
  }

  .meta-text {
    color: #94a3b8;
  }

  .stat-label {
    color: #94a3b8;
  }

  .intro-card {
    background: rgba(26, 87, 219, 0.1);
    border-color: rgba(26, 87, 219, 0.2);
  }

  .intro-text {
    color: #94a3b8;
  }

  .stat-card {
    border-color: #334155;
    background: #1e293b;
    box-shadow: none;
  }
}
</style>

