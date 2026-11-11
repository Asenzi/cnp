<template>
  <view class="income-page">
    <view class="hero-card">
      <view class="hero-glow hero-glow-one"></view>
      <view class="hero-glow hero-glow-two"></view>

      <view class="hero-head">
        <view class="hero-title-wrap">
          <image class="hero-icon" src="https://cos.cnptec.site/static/icon/Profit.png" mode="aspectFit" />
          <view class="hero-title-copy">
            <text class="eyebrow">MY WALLET</text>
            <text class="hero-title">我的钱包</text>
          </view>
        </view>
        <view class="status-pill">
          <text class="status-dot"></text>
          <text class="status-pill-text">提现人工审核</text>
        </view>
      </view>

      <view class="balance-block">
        <text class="balance-label">可提现余额</text>
        <view class="balance-row">
          <text class="currency">¥</text>
          <text class="balance-value">{{ moneyText(account.available_balance) }}</text>
        </view>
        <text class="balance-desc">提现至当前登录微信账户 · 最低提现 ¥{{ payout.minimum_amount }}</text>
      </view>

      <view class="hero-actions">
        <button class="primary-action" :class="{ 'primary-action-disabled': !hasWithdrawable }"
          :disabled="!hasWithdrawable || withdrawing" hover-class="primary-action-active" @tap="onWithdraw">
          {{ withdrawing ? '提交中...' : '申请提现' }}
        </button>
        <button class="ghost-action" hover-class="ghost-action-active" @tap="refreshAll">
          刷新收益
        </button>
      </view>
    </view>

    <view class="payout-row">
      <text>收款方式：当前登录微信</text>
      <text>{{ payout.real_name_verified && payout.wechat_bound ? '已具备提现条件' : '请先完成实名并绑定微信' }}</text>
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
      <view class="summary-divider"></view>
      <view class="summary-item">
        <text class="summary-value">¥{{ moneyText(account.frozen_balance) }}</text>
        <text class="summary-label">冻结中</text>
      </view>
    </view>

    <view class="rule-card">
      <view class="rule-head">
        <text class="section-title">收益规则</text>
        <text class="rule-badge">{{ settlementRule.role_name ? '会员推荐' : '付费入圈' }}</text>
      </view>
      <view class="rule-flow">
        <view class="rule-node">
          <text class="rule-node-value">{{ percentText(settlementRule.receiver_rate) }}</text>
          <text class="rule-node-label">{{ settlementRule.role_name || '圈主' }}收益</text>
        </view>
        <view class="rule-line"></view>
        <view class="rule-node rule-node-muted">
          <text class="rule-node-value">{{ percentText(settlementRule.service_fee_rate) }}</text>
          <text class="rule-node-label">{{ settlementRule.role_name ? '平台部分' : '技术服务费' }}</text>
        </view>
      </view>
      <text class="rule-desc">{{ settlementRule.role_name ? `推荐用户开通会员后，你获得会员实付金额的 ${percentText(settlementRule.receiver_rate)}；收益已入账，可按提现规则申请提现。` : '用户完成付费入圈后，系统会生成收益流水；收益进入可结算状态后即可申请提现。' }}</text>
    </view>

    <view class="records-card">
      <view class="records-head">
        <view>
          <text class="section-title">收益明细</text>
          <text class="section-subtitle">逐笔查看收益与服务费</text>
        </view>
        <text v-if="records.length" class="records-count">{{ records.length }} 条</text>
      </view>
      <view class="filter-row">
        <text v-for="item in incomeFilters" :key="item.value" class="filter-chip" :class="{ 'filter-chip-active': incomeType === item.value }" @tap="changeIncomeType(item.value)">{{ item.label }}</text>
      </view>

      <view v-if="loading && !records.length" class="status-wrap">
        <view class="loading-mark"></view>
        <text class="status-text">正在同步收益...</text>
      </view>
      <view v-else-if="loadError && !records.length" class="status-wrap">
        <text class="status-text">{{ loadError }}</text>
        <button class="retry-btn" hover-class="retry-btn-active" @tap="fetchIncome">重新加载</button>
      </view>
      <AppEmptyState v-else-if="!records.length"><template #title>暂无收益记录</template><template #description>{{ settlementRule.role_name ? '你推荐的用户开通会员后，分佣记录会显示在这里' : '有成员付费加入你的圈子后，收益会显示在这里' }}</template></AppEmptyState>
      <view v-else class="record-list">
        <view v-for="item in records" :key="item.id || item.order_no" class="record-item" @tap="showIncomeDetail(item)">
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
            <text v-if="item.order_no" class="record-order">订单 {{ item.order_no }}</text>
          </view>
        </view>
      </view>
      <button v-if="incomeHasMore" class="load-more-btn" :disabled="loading" @tap="loadMoreRecords">{{ loading ? '加载中...' : '加载更多' }}</button>
    </view>

    <view class="records-card withdrawals-card">
      <view class="records-head">
        <view>
          <text class="section-title">提现记录</text>
          <text class="section-subtitle">查看提现申请处理进度</text>
        </view>
        <text v-if="withdrawals.length" class="records-count">{{ withdrawals.length }} 条</text>
      </view>
      <view class="filter-row">
        <text v-for="item in withdrawalFilters" :key="item.value" class="filter-chip" :class="{ 'filter-chip-active': withdrawalStatus === item.value }" @tap="changeWithdrawalStatus(item.value)">{{ item.label }}</text>
      </view>
      <AppEmptyState v-if="!withdrawals.length"><template #title>暂无提现记录</template></AppEmptyState>
      <view v-else class="record-list">
        <view v-for="item in withdrawals" :key="item.id || item.order_no" class="record-item" @tap="showWithdrawalDetail(item)">
          <view class="record-icon withdrawal-record-icon">
            <text class="record-icon-text">提</text>
          </view>
          <view class="record-main">
            <view class="record-title-row">
              <text class="record-title">提现申请</text>
              <text class="record-amount withdrawal-amount">-¥{{ moneyText(item.amount) }}</text>
            </view>
            <view class="record-meta-row">
              <text class="record-meta">{{ dateText(item.created_at) }}</text>
              <text class="record-status" :class="withdrawalStatusClass(item.status)">{{ withdrawalStatusText(item.status) }}</text>
            </view>
            <text v-if="item.remark" class="record-remark">{{ item.remark }}</text>
            <text v-if="item.status === 'failed'" class="record-remark">金额已退回可提现余额，可重新申请</text>
          </view>
        </view>
      </view>
      <button v-if="withdrawalHasMore" class="load-more-btn" :disabled="loadingWithdrawals" @tap="loadMoreWithdrawals">{{ loadingWithdrawals ? '加载中...' : '加载更多' }}</button>
    </view>
  </view>
</template>

<script setup>
import AppEmptyState from '../../../components/AppEmptyState/AppEmptyState.vue'

import { computed, ref } from 'vue'
import { onPullDownRefresh, onShow } from '@dcloudio/uni-app'
import { createWithdrawal, getIncomeOverview, getWithdrawals } from '../../../api/settlement'

const loading = ref(false)
const withdrawing = ref(false)
const loadError = ref('')
const account = ref({
  available_balance: 0,
  pending_amount: 0,
  total_income: 0,
  total_withdrawn: 0,
  frozen_balance: 0
})
const records = ref([])
const withdrawals = ref([])
const payout = ref({ wechat_bound: false, real_name_verified: false, minimum_amount: '1.00' })
const settlementRule = ref({ receiver_rate: 0.9, service_fee_rate: 0.1, auto_settle_enabled: true })
const incomeType = ref('')
const sourceTypes = ref([])
const withdrawalStatus = ref('')
const incomeCursor = ref(null)
const withdrawalCursor = ref(null)
const incomeHasMore = ref(false)
const withdrawalHasMore = ref(false)
const loadingWithdrawals = ref(false)
const sourceLabels = {
  circle_join: '付费入圈',
  salon: '沙龙',
  city_partner: '城市合伙',
  distribution: '分销'
}
const incomeFilters = computed(() => [
  { value: '', label: '全部' },
  ...sourceTypes.value.map((value) => ({ value, label: sourceLabels[value] || value }))
])
const withdrawalFilters = [
  { value: '', label: '全部' },
  { value: 'pending', label: '处理中' },
  { value: 'success', label: '已打款' },
  { value: 'failed', label: '失败' }
]
const hasWithdrawable = computed(() => Number(account.value?.available_balance || 0) >= Number(payout.value.minimum_amount || 1))

const moneyText = (value) => {
  const amount = Number(value || 0)
  return Number.isFinite(amount) ? amount.toFixed(2) : '0.00'
}

const percentText = (value) => `${(Number(value || 0) * 100).toFixed(0)}%`

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

const withdrawalStatusText = (status) => {
  const map = {
    pending: '处理中',
    processing: '处理中',
    success: '已打款',
    completed: '已打款',
    rejected: '已驳回',
    cancelled: '已取消',
    failed: '失败'
  }
  return map[String(status || '').trim().toLowerCase()] || '待处理'
}

const withdrawalStatusClass = (status) => {
  const normalized = String(status || '').trim().toLowerCase()
  if (['success', 'completed'].includes(normalized)) return 'status-success'
  if (['rejected', 'cancelled', 'failed'].includes(normalized)) return 'status-danger'
  return 'status-pending'
}

const showIncomeDetail = (item) => {
  const fee = Number(item?.platform_fee || 0)
  const amount = Number(item?.split_amount || 0)
  uni.showModal({
    title: '收益详情',
    content: `收益金额 ¥${moneyText(amount)}\n平台服务费 ¥${moneyText(fee)}\n状态：${statusText(item?.split_status)}${item?.order_no ? `\n订单号：${item.order_no}` : ''}`,
    showCancel: false,
    confirmText: '知道了'
  })
}

const showWithdrawalDetail = (item) => {
  uni.showModal({
    title: '提现详情',
    content: `提现金额 ¥${moneyText(item?.amount)}\n状态：${withdrawalStatusText(item?.status)}${item?.order_no ? `\n提现单号：${item.order_no}` : ''}${item?.remark ? `\n备注：${item.remark}` : ''}`,
    showCancel: false,
    confirmText: '知道了'
  })
}

const recordTitle = (item) => {
  return `${sourceLabels[item?.biz_type] || item?.biz_type || '其他'}收益`
}

const dateText = (value) => {
  if (!value) return '--'
  const date = new Date(String(value).replace(' ', 'T'))
  if (!Number.isFinite(date.getTime())) return String(value).slice(0, 16)
  const pad = (num) => String(num).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`
}

const fetchIncome = async ({ append = false } = {}) => {
  if (loading.value) return
  loading.value = true
  loadError.value = ''
  try {
    const data = await getIncomeOverview({ limit: 30, type: incomeType.value, beforeId: append ? incomeCursor.value : null })
    account.value = {
      ...account.value,
      ...(data?.account || {})
    }
    settlementRule.value = {
      ...settlementRule.value,
      ...(data?.rules || {})
    }
    payout.value = { ...payout.value, ...(data?.payout || {}) }
    sourceTypes.value = Array.isArray(data?.source_types) ? data.source_types : []
    const nextRecords = Array.isArray(data?.items) ? data.items : []
    records.value = append ? [...records.value, ...nextRecords.filter((item) => !records.value.some((old) => old.id === item.id))] : nextRecords
    incomeHasMore.value = Boolean(data?.has_more)
    incomeCursor.value = data?.next_before_id || null
  } catch (error) {
    loadError.value = error?.message || '收益加载失败'
  } finally {
    loading.value = false
    uni.stopPullDownRefresh()
  }
}

const fetchWithdrawals = async ({ append = false } = {}) => {
  if (loadingWithdrawals.value) return
  loadingWithdrawals.value = true
  try {
    const data = await getWithdrawals({ limit: 30, status: withdrawalStatus.value, beforeId: append ? withdrawalCursor.value : null })
    const next = Array.isArray(data?.items) ? data.items : []
    withdrawals.value = append ? [...withdrawals.value, ...next.filter((item) => !withdrawals.value.some((old) => old.id === item.id))] : next
    withdrawalHasMore.value = Boolean(data?.has_more)
    withdrawalCursor.value = data?.next_before_id || null
  } catch (error) {
    uni.showToast({ title: error?.message || '提现记录加载失败', icon: 'none' })
  } finally {
    loadingWithdrawals.value = false
  }
}

const refreshAll = async () => {
  await Promise.all([fetchIncome(), fetchWithdrawals()])
}

const changeIncomeType = async (value) => {
  incomeType.value = value
  await fetchIncome()
}

const loadMoreRecords = async () => {
  if (!incomeHasMore.value) return
  await fetchIncome({ append: true })
}

const changeWithdrawalStatus = async (value) => {
  withdrawalStatus.value = value
  await fetchWithdrawals()
}

const loadMoreWithdrawals = async () => {
  if (!withdrawalHasMore.value) return
  await fetchWithdrawals({ append: true })
}

const onWithdraw = () => {
  if (!payout.value.real_name_verified || !payout.value.wechat_bound) {
    uni.showToast({ title: '请先完成实名认证并绑定微信', icon: 'none' })
    return
  }
  if (!hasWithdrawable.value) {
    uni.showToast({ title: '暂无可提现收益', icon: 'none' })
    return
  }
  const amount = Number(account.value?.available_balance || 0)
  uni.showModal({
    title: '确认提现',
    content: `申请提现 ¥${moneyText(amount)} 至当前登录微信账户，提交后进入人工打款审核。请确认当前微信为本人收款账户。`,
    success: async (res) => {
      if (!res.confirm || withdrawing.value) return
      withdrawing.value = true
      try {
        await createWithdrawal({ amount, withdraw_type: 'wechat' })
        uni.showToast({ title: '提现申请已提交', icon: 'success' })
        await refreshAll()
      } catch (error) {
        uni.showToast({ title: error?.message || '提现申请失败', icon: 'none' })
      } finally {
        withdrawing.value = false
      }
    }
  })
}

onShow(() => {
  refreshAll()
})

onPullDownRefresh(() => {
  refreshAll().finally(() => uni.stopPullDownRefresh())
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

.payout-row {
  display: flex;
  justify-content: space-between;
  gap: 16rpx;
  padding: 20rpx 6rpx 0;
  color: #475569;
  font-size: 21rpx;
  line-height: 32rpx;
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

.summary-strip .summary-value {
  font-size: 23rpx;
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

.withdrawals-card {
  margin-bottom: 24rpx;
}

.records-head {
  padding: 0 28rpx 18rpx;
}

.filter-row {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
  padding: 0 28rpx 16rpx;
}

.filter-chip {
  padding: 8rpx 18rpx;
  border-radius: 999rpx;
  background: #f1f5f9;
  color: #64748b;
  font-size: 22rpx;
  line-height: 28rpx;
}

.filter-chip-active {
  background: #dff7f2;
  color: #0f766e;
  font-weight: 600;
}

.status-wrap {
  min-height: 380rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 18rpx;
}

.compact-status-wrap {
  min-height: 150rpx;
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

.load-more-btn {
  width: calc(100% - 56rpx);
  height: 70rpx;
  margin: 8rpx 28rpx 22rpx;
  border: 0;
  border-radius: 16rpx;
  background: #f1f5f9;
  color: #0f766e;
  font-size: 24rpx;
  line-height: 70rpx;
}

.load-more-btn::after {
  border: 0;
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

.withdrawal-record-icon {
  background: #eff6ff;
  color: #2563eb;
}

.withdrawal-amount {
  color: #2563eb;
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

.record-order {
  display: block;
  margin-top: 6rpx;
  color: #cbd5e1;
  font-size: 20rpx;
  line-height: 28rpx;
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
