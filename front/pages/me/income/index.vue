<template>
  <view class="income-page">
    <view class="hero-card">
      <view class="hero-glow hero-glow-one"></view>
      <view class="hero-glow hero-glow-two"></view>

      <view class="hero-head">
        <view class="hero-title-wrap">
          <image class="hero-icon" src="https://cos.cnptec.site/static/icon/Profit.png" mode="aspectFit" />
          <view class="hero-title-copy">
            <text class="eyebrow">CIRCLE OWNER INCOME</text>
            <text class="hero-title">我的收益</text>
          </view>
        </view>
        <view class="status-pill">
          <text class="status-dot"></text>
          <text class="status-pill-text">自动结算</text>
        </view>
      </view>

      <view class="balance-block">
        <text class="balance-label">可提现余额</text>
        <view class="balance-row">
          <text class="currency">¥</text>
          <text class="balance-value">{{ moneyText(account.available_balance) }}</text>
        </view>
        <text class="balance-desc">来自付费入圈收益，扣除平台技术服务费后入账</text>
      </view>

      <view class="hero-actions">
        <button class="primary-action" :class="{ 'primary-action-disabled': !hasWithdrawable }"
          :disabled="!hasWithdrawable || withdrawing" hover-class="primary-action-active" @tap="onWithdraw">
          {{ withdrawing ? '提交中...' : '申请提现' }}
        </button>
        <button class="ghost-action" hover-class="ghost-action-active" @tap="fetchIncome">
          刷新收益
        </button>
      </view>
    </view>

    <view class="summary-strip">
      <view class="summary-item">
        <text class="summary-value">¥{{ moneyText(account.pending_amount) }}</text>
        <text class="summary-label">待结算</text>
      </view>
      <view class="summary-divider"></view>
      <view class="summary-item">
        <text class="summary-value">¥{{ moneyText(account.total_income) }}</text>
        <text class="summary-label">累计收益</text>
      </view>
      <view class="summary-divider"></view>
      <view class="summary-item">
        <text class="summary-value">¥{{ moneyText(account.total_withdrawn) }}</text>
        <text class="summary-label">累计提现</text>
      </view>
    </view>

    <view class="rule-card">
      <view class="rule-head">
        <text class="section-title">收益规则</text>
        <text class="rule-badge">付费入圈</text>
      </view>
      <view class="rule-flow">
        <view class="rule-node">
          <text class="rule-node-value">90%</text>
          <text class="rule-node-label">圈主收益</text>
        </view>
        <view class="rule-line"></view>
        <view class="rule-node rule-node-muted">
          <text class="rule-node-value">10%</text>
          <text class="rule-node-label">技术服务费</text>
        </view>
      </view>
      <text class="rule-desc">用户付费申请入圈并完成加入后，系统自动生成收益流水。微信真实分账关闭时，这里展示内部结算收益。</text>
    </view>

    <view class="records-card">
      <view class="records-head">
        <view>
          <text class="section-title">最近收益</text>
          <text class="section-subtitle">展示最近 30 条付费入圈分账记录</text>
        </view>
        <text v-if="records.length" class="records-count">{{ records.length }} 条</text>
      </view>

      <view v-if="loading && !records.length" class="status-wrap">
        <view class="loading-mark"></view>
        <text class="status-text">正在同步收益...</text>
      </view>
      <view v-else-if="loadError && !records.length" class="status-wrap">
        <text class="status-text">{{ loadError }}</text>
        <button class="retry-btn" hover-class="retry-btn-active" @tap="fetchIncome">重新加载</button>
      </view>
      <view v-else-if="!records.length" class="status-wrap">
        <image class="empty-icon" src="https://cos.cnptec.site/static/icon/data-block.png" mode="aspectFit" />
        <text class="status-text">暂无收益记录</text>
        <text class="status-subtext">有成员付费加入你的圈子后，收益会显示在这里</text>
      </view>
      <view v-else class="record-list">
        <view v-for="item in records" :key="item.id || item.order_no" class="record-item">
          <view class="record-icon" :class="statusClass(item.split_status)">
            <text class="record-icon-text">收</text>
          </view>
          <view class="record-main">
            <view class="record-title-row">
              <text class="record-title">{{ recordTitle(item) }}</text>
              <text class="record-amount">+¥{{ moneyText(item.split_amount) }}</text>
            </view>
            <view class="record-meta-row">
              <text class="record-meta">{{ dateText(item.executed_at || item.created_at) }}</text>
              <text class="record-status" :class="statusClass(item.split_status)">{{ statusText(item.split_status)
              }}</text>
            </view>
            <text v-if="item.remark" class="record-remark">{{ item.remark }}</text>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onPullDownRefresh, onShow } from '@dcloudio/uni-app'
import { createWithdrawal, getIncomeOverview } from '../../../api/settlement'

const loading = ref(false)
const withdrawing = ref(false)
const loadError = ref('')
const account = ref({
  available_balance: 0,
  pending_amount: 0,
  total_income: 0,
  total_withdrawn: 0
})
const records = ref([])

const hasWithdrawable = computed(() => Number(account.value?.available_balance || 0) > 0)

const moneyText = (value) => {
  const amount = Number(value || 0)
  return Number.isFinite(amount) ? amount.toFixed(2) : '0.00'
}

const statusText = (status) => {
  const map = {
    pending: '待分账',
    ready: '待处理',
    success: '已入账',
    cancelled: '已取消',
    returned: '已退回',
    external_failed: '分账失败'
  }
  return map[String(status || '').trim()] || '处理中'
}

const statusClass = (status) => {
  const normalized = String(status || '').trim()
  if (normalized === 'success') return 'status-success'
  if (['cancelled', 'returned', 'external_failed'].includes(normalized)) return 'status-danger'
  return 'status-pending'
}

const recordTitle = (item) => {
  if (item?.biz_type === 'circle_join') return '付费入圈收益'
  return '收益入账'
}

const dateText = (value) => {
  if (!value) return '--'
  const date = new Date(String(value).replace(' ', 'T'))
  if (!Number.isFinite(date.getTime())) return String(value).slice(0, 16)
  const pad = (num) => String(num).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`
}

const fetchIncome = async () => {
  loading.value = true
  loadError.value = ''
  try {
    const data = await getIncomeOverview({ limit: 30 })
    account.value = {
      ...account.value,
      ...(data?.account || {})
    }
    records.value = Array.isArray(data?.items) ? data.items : []
  } catch (error) {
    loadError.value = error?.message || '收益加载失败'
  } finally {
    loading.value = false
    uni.stopPullDownRefresh()
  }
}

const onWithdraw = () => {
  if (!hasWithdrawable.value) {
    uni.showToast({ title: '暂无可提现收益', icon: 'none' })
    return
  }
  const amount = Number(account.value?.available_balance || 0)
  uni.showModal({
    title: '确认提现',
    content: `申请提现 ¥${moneyText(amount)}，提交后将进入后台人工打款审核。`,
    success: async (res) => {
      if (!res.confirm || withdrawing.value) return
      withdrawing.value = true
      try {
        await createWithdrawal({ amount, withdraw_type: 'wechat' })
        uni.showToast({ title: '提现申请已提交', icon: 'success' })
        await fetchIncome()
      } catch (error) {
        uni.showToast({ title: error?.message || '提现申请失败', icon: 'none' })
      } finally {
        withdrawing.value = false
      }
    }
  })
}

onShow(() => {
  fetchIncome()
})

onPullDownRefresh(() => {
  fetchIncome()
})
</script>

<style scoped>
.income-page {
  min-height: 100vh;
  box-sizing: border-box;
  padding: 28rpx 32rpx 52rpx;
  background:
    radial-gradient(circle at 12% 0%, rgba(20, 184, 166, 0.14), transparent 34%),
    linear-gradient(180deg, #f4f8f7 0%, #f6f6f8 42%, #f6f6f8 100%);
}

.hero-card {
  position: relative;
  overflow: hidden;
  border-radius: 32rpx;
  padding: 34rpx;
  background: #828282;
  color: #ffffff;
}

.hero-glow {
  position: absolute;
  border-radius: 999rpx;
  filter: blur(6rpx);
  opacity: 0.72;
}

.hero-glow-one {
  right: -90rpx;
  top: -120rpx;
  width: 280rpx;
  height: 280rpx;
  background: rgba(45, 212, 191, 0.28);
}

.hero-glow-two {
  left: -100rpx;
  bottom: -130rpx;
  width: 260rpx;
  height: 260rpx;
  background: rgba(250, 204, 21, 0.16);
}

.hero-head,
.balance-block,
.hero-actions {
  position: relative;
  z-index: 1;
}

.hero-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 24rpx;
}

.hero-title-wrap {
  display: flex;
  align-items: center;
  gap: 18rpx;
}

.hero-icon {
  width: 72rpx;
  height: 72rpx;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.14);
}

.hero-title-copy {
  display: flex;
  flex-direction: column;
  gap: 6rpx;
}

.eyebrow {
  color: rgba(255, 255, 255, 0.58);
  font-size: 18rpx;
  line-height: 24rpx;
  font-weight: 700;
  letter-spacing: 0.18em;
}

.hero-title {
  color: #ffffff;
  font-size: 34rpx;
  line-height: 42rpx;
  font-weight: 700;
}

.status-pill {
  flex-shrink: 0;
  height: 46rpx;
  padding: 0 16rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.14);
  display: flex;
  align-items: center;
  gap: 8rpx;
}

.status-dot {
  width: 10rpx;
  height: 10rpx;
  border-radius: 50%;
  background: #5eead4;
}

.status-pill-text {
  color: rgba(255, 255, 255, 0.86);
  font-size: 22rpx;
}

.balance-block {
  margin-top: 56rpx;
}

.balance-label {
  display: block;
  color: rgba(255, 255, 255, 0.68);
  font-size: 24rpx;
  line-height: 32rpx;
}

.balance-row {
  margin-top: 10rpx;
  display: flex;
  align-items: flex-end;
}

.currency {
  padding-bottom: 10rpx;
  color: rgba(255, 255, 255, 0.9);
  font-size: 34rpx;
  line-height: 40rpx;
  font-weight: 700;
}

.balance-value {
  color: #ffffff;
  font-size: 72rpx;
  line-height: 78rpx;
  font-weight: 800;
  letter-spacing: -0.02em;
}

.balance-desc {
  display: block;
  margin-top: 12rpx;
  color: rgba(255, 255, 255, 0.6);
  font-size: 22rpx;
  line-height: 32rpx;
}

.hero-actions {
  margin-top: 32rpx;
  display: flex;
  gap: 16rpx;
}

.primary-action,
.ghost-action,
.retry-btn {
  height: 76rpx;
  line-height: 76rpx;
  margin: 0;
  border: 0;
  border-radius: 18rpx;
  font-size: 26rpx;
  font-weight: 700;
}

.primary-action {
  flex: 1.2;
  background: #ffffff;
  color: #075f59;
}

.primary-action-disabled {
  background: rgba(255, 255, 255, 0.3);
  color: rgba(255, 255, 255, 0.66);
}

.ghost-action {
  flex: 0.8;
  background: rgba(255, 255, 255, 0.12);
  color: #ffffff;
}

.primary-action::after,
.ghost-action::after,
.retry-btn::after {
  border: 0;
}

.primary-action-active,
.ghost-action-active,
.retry-btn-active {
  opacity: 0.86;
}

.summary-strip {
  margin-top: 20rpx;
  border-radius: 24rpx;
  padding: 26rpx 18rpx;
  background: #ffffff;
  display: flex;
  align-items: center;
}

.summary-item {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8rpx;
}

.summary-value {
  color: #111827;
  font-size: 26rpx;
  line-height: 34rpx;
  font-weight: 700;
}

.summary-label {
  color: #64748b;
  font-size: 22rpx;
}

.summary-divider {
  width: 1rpx;
  height: 46rpx;
  background: #eef2f7;
}

.rule-card,
.records-card {
  margin-top: 24rpx;
  border-radius: 24rpx;
  background: #ffffff;
  overflow: hidden;
}

.rule-card {
  padding: 28rpx;
}

.rule-head,
.records-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20rpx;
}

.section-title {
  display: block;
  color: #111827;
  font-size: 30rpx;
  line-height: 38rpx;
  font-weight: 700;
}

.section-subtitle {
  display: block;
  margin-top: 6rpx;
  color: #94a3b8;
  font-size: 22rpx;
  line-height: 30rpx;
}

.rule-badge,
.records-count {
  flex-shrink: 0;
  border-radius: 999rpx;
  padding: 8rpx 16rpx;
  background: #ecfeff;
  color: #0f766e;
  font-size: 22rpx;
  line-height: 28rpx;
  font-weight: 600;
}

.rule-flow {
  margin-top: 28rpx;
  display: flex;
  align-items: center;
  gap: 18rpx;
}

.rule-node {
  flex: 1;
  min-height: 116rpx;
  border-radius: 20rpx;
  background: #f0fdfa;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6rpx;
}

.rule-node-muted {
  background: #f8fafc;
}

.rule-node-value {
  color: #0f766e;
  font-size: 34rpx;
  line-height: 42rpx;
  font-weight: 800;
}

.rule-node-muted .rule-node-value {
  color: #64748b;
}

.rule-node-label {
  color: #64748b;
  font-size: 22rpx;
}

.rule-line {
  width: 48rpx;
  height: 2rpx;
  background: linear-gradient(90deg, #14b8a6, #cbd5e1);
}

.rule-desc {
  display: block;
  margin-top: 22rpx;
  color: #64748b;
  font-size: 24rpx;
  line-height: 36rpx;
}

.records-card {
  padding-top: 28rpx;
}

.records-head {
  padding: 0 28rpx 18rpx;
}

.status-wrap {
  min-height: 380rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 18rpx;
}

.loading-mark {
  width: 48rpx;
  height: 48rpx;
  border-radius: 50%;
  border: 6rpx solid #dbeafe;
  border-top-color: #0f766e;
}

.empty-icon {
  width: 150rpx;
  height: 150rpx;
}

.status-text {
  color: #94a3b8;
  font-size: 26rpx;
}

.status-subtext {
  color: #cbd5e1;
  font-size: 22rpx;
}

.retry-btn {
  padding: 0 30rpx;
  background: #0f766e;
  color: #ffffff;
}

.record-list {
  padding: 0 28rpx 10rpx;
}

.record-item {
  display: flex;
  gap: 18rpx;
  padding: 24rpx 0;
  border-top: 1rpx solid #eef2f7;
}

.record-icon {
  flex-shrink: 0;
  width: 56rpx;
  height: 56rpx;
  border-radius: 18rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.record-icon-text {
  font-size: 22rpx;
  font-weight: 700;
}

.record-main {
  flex: 1;
  min-width: 0;
}

.record-title-row,
.record-meta-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
}

.record-title {
  color: #111827;
  font-size: 28rpx;
  line-height: 36rpx;
  font-weight: 600;
}

.record-amount {
  flex-shrink: 0;
  color: #0f766e;
  font-size: 30rpx;
  line-height: 36rpx;
  font-weight: 800;
}

.record-meta-row {
  margin-top: 10rpx;
}

.record-meta {
  color: #94a3b8;
  font-size: 22rpx;
  line-height: 30rpx;
}

.record-status {
  flex-shrink: 0;
  border-radius: 999rpx;
  padding: 4rpx 12rpx;
  font-size: 20rpx;
  line-height: 28rpx;
}

.record-remark {
  display: block;
  margin-top: 12rpx;
  color: #94a3b8;
  font-size: 22rpx;
  line-height: 32rpx;
}

.status-success {
  background: #ecfdf5;
  color: #059669;
}

.status-pending {
  background: #eff6ff;
  color: #2563eb;
}

.status-danger {
  background: #fff1f2;
  color: #e11d48;
}
</style>
