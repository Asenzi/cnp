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
            <image class="edit-icon-img" mode="aspectFit" src="/static/me-icons/edit-gray.png" />
          </view>
        </view>

        <view class="id-row">
          <text class="id-text">ID: {{ displayUserId }}</text>
        </view>

        <view class="meta-row">
          <text class="meta-tag" :class="isVerified ? 'meta-tag-primary' : 'meta-tag-muted'">
            {{ isVerified ? '已认证用户' : '未认证用户' }}
          </text>
          <text class="meta-tag" :class="showContact ? 'meta-tag-primary' : 'meta-tag-muted'">
            {{ showContact ? '联系方式已公开' : '联系方式已隐藏' }}
          </text>
          <text v-if="cardFilesCount > 0" class="meta-tag meta-tag-muted">
            名片附件 {{ cardFilesCount }} 份
          </text>
        </view>

        <text class="summary">{{ displaySummary }}</text>
      </view>
    </view>

    <view class="intro-card">
      <view class="intro-title-row">
        <image class="intro-mark-img" mode="aspectFit" src="/static/me-icons/description-primary.png" />
        <text class="intro-title">个人简介</text>
      </view>
      <text class="intro-text">{{ displayIntro }}</text>
    </view>

    <view class="stats-row" :class="{ 'stats-row-compact': withMemberCard }">
      <view class="stat-card stat-card-click" hover-class="stat-card-active" @tap="$emit('open-circles')">
        <text class="stat-value" :class="{ 'stat-value-muted': displayCircleCount === '--' }">{{ displayCircleCount }}</text>
        <text class="stat-label">我的圈子</text>
      </view>
      <view class="stat-card stat-card-click" hover-class="stat-card-active" @tap="$emit('open-points')">
        <text class="stat-value" :class="{ 'stat-value-muted': displayPoints === '--' }">{{ displayPoints }}</text>
        <text class="stat-label">积分</text>
      </view>
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

defineEmits(['edit', 'open-circles', 'open-points', 'open-wallet'])

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

const displaySummary = computed(() => {
  const industryLabel =
    typeof props.userInfo?.industry_label === 'string' ? props.userInfo.industry_label.trim() : ''
  if (industryLabel) {
    return industryLabel
  }
  return '欢迎来到圈脉链，完善资料让更多商机找到你'
})

const displayIntro = computed(() => {
  const intro = typeof props.userInfo?.intro === 'string' ? props.userInfo.intro.trim() : ''
  if (intro) {
    return intro
  }
  return '欢迎来到圈脉链，完善资料让更多商机找到你'
})

const showContact = computed(() => {
  const value = props.userInfo?.show_contact
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
  return true
})

const cardFilesCount = computed(() => {
  const files = props.userInfo?.card_files
  if (!Array.isArray(files)) {
    return 0
  }
  return files.length
})

const formatCount = (value) => {
  if (typeof value === 'number' && Number.isFinite(value)) {
    return value.toLocaleString('zh-CN')
  }
  if (typeof value === 'string' && value.trim()) {
    return value.trim()
  }
  return '--'
}

const displayCircleCount = computed(() => formatCount(props.userInfo?.circle_count))
const displayPoints = computed(() => {
  const sourceValue =
    props.userInfo?.points
    ?? props.userInfo?.point_count
    ?? props.userInfo?.score
    ?? props.userInfo?.integral
    ?? props.userInfo?.network_count
  return formatCount(sourceValue)
})

const displayBalance = computed(() => {
  const value = props.userInfo?.balance
  if (typeof value === 'number' && Number.isFinite(value)) {
    return `¥${value.toLocaleString('zh-CN', { minimumFractionDigits: 0, maximumFractionDigits: 2 })}`
  }
  if (typeof value === 'string' && value.trim()) {
    const normalized = value.trim()
    return normalized.startsWith('¥') ? normalized : `¥${normalized}`
  }
  return '--'
})
</script>

<style scoped>
.profile-row {
  display: flex;
  align-items: flex-start;
  gap: 32rpx;
  margin-bottom: 32rpx;
}

.avatar-wrap {
  position: relative;
}

.avatar {
  width: 192rpx;
  height: 192rpx;
  border-radius: 24rpx;
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
  font-size: 40rpx;
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
  border-radius: 999rpx;
  padding: 5rpx 12rpx;
  font-size: 20rpx;
  font-weight: 600;
  color: #334155;
  background: #eef2ff;
}

.summary {
  margin-top: 4rpx;
  font-size: 28rpx;
  color: #64748b;
}

.meta-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8rpx;
  margin-top: 4rpx;
}

.meta-tag {
  display: inline-block;
  border-radius: 999rpx;
  padding: 4rpx 12rpx;
  font-size: 20rpx;
  font-weight: 600;
  line-height: 1.2;
}

.meta-tag-primary {
  color: #1a57db;
  background: rgba(26, 87, 219, 0.1);
}

.meta-tag-muted {
  color: #64748b;
  background: #f1f5f9;
}

.intro-card {
  margin-bottom: 48rpx;
  padding: 32rpx;
  border: 1rpx solid rgba(26, 87, 219, 0.1);
  border-radius: 24rpx;
  background: rgba(26, 87, 219, 0.05);
}

.intro-title-row {
  display: flex;
  align-items: center;
  gap: 12rpx;
  margin-bottom: 8rpx;
}

.intro-mark-img {
  width: 36rpx;
  height: 36rpx;
}

.intro-title {
  font-size: 28rpx;
  color: #334155;
  font-weight: 600;
}

.intro-text {
  font-size: 28rpx;
  color: #475569;
  line-height: 1.65;
}

.stats-row {
  display: flex;
  gap: 24rpx;
  margin-bottom: 64rpx;
}

.stats-row-compact {
  margin-bottom: 24rpx;
}

.stat-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8rpx;
  padding: 24rpx 12rpx;
  border-radius: 24rpx;
  border: 1rpx solid #f1f5f9;
  background: #ffffff;
  box-shadow: 0 4rpx 12rpx rgba(15, 23, 42, 0.04);
}

.stat-card-click {
  transition: opacity 0.2s ease;
}

.stat-card-active {
  opacity: 0.82;
}

.stat-value {
  font-size: 40rpx;
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
    background: #1e293b;
  }

  .summary,
  .stat-label {
    color: #94a3b8;
  }

  .meta-tag-muted {
    color: #94a3b8;
    background: #1e293b;
  }

  .intro-card {
    background: rgba(26, 87, 219, 0.1);
    border-color: rgba(26, 87, 219, 0.2);
  }

  .intro-title {
    color: #cbd5e1;
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

