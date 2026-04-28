<template>
  <view class="wallet-page">
    <scroll-view class="wallet-scroll" scroll-y :show-scrollbar="false">
      <view class="wallet-content">
        <WalletBalanceCard :balance-text="displayBalance" :wallet-id="walletId" />

        <view class="action-wrap">
          <view class="recharge-btn" hover-class="recharge-btn-hover" @tap="onTapRecharge">
            <view class="recharge-btn-inner">
              <image class="recharge-icon" mode="aspectFit" src="/static/icon/recharge.png" />
              <text class="recharge-text">充值</text>
            </view>
          </view>
        </view>

        <view class="section-head">
          <text class="section-title">收支明细</text>

          <view class="filter-row">
            <view
              class="filter-btn"
              :class="{ 'filter-btn-selected': selectedTimeFilter !== 'all' || showTimeFilterMenu }"
              hover-class="filter-btn-hover"
              @tap.stop="onTapTimeFilter"
            >
              <text class="filter-text">{{ timeFilterButtonText }}</text>
              <image class="filter-icon" mode="aspectFit" src="/static/me-icons/tune-gray.png" />
            </view>

            <view
              class="filter-btn"
              :class="{ 'filter-btn-selected': selectedTypeFilter !== 'all' || showTypeFilterMenu }"
              hover-class="filter-btn-hover"
              @tap.stop="onTapTypeFilter"
            >
              <text class="filter-text">{{ typeFilterButtonText }}</text>
              <image class="filter-icon" mode="aspectFit" src="/static/me-icons/tune-gray.png" />
            </view>

            <view v-if="showTimeFilterMenu" class="filter-dropdown time-filter-dropdown" @tap.stop>
              <view
                v-for="option in TIME_FILTER_OPTIONS"
                :key="option.value"
                class="filter-option"
                :class="{ 'filter-option-active': selectedTimeFilter === option.value }"
                hover-class="filter-option-hover"
                @tap="onSelectTimeFilter(option.value)"
              >
                <text class="filter-option-text">{{ option.label }}</text>
                <view v-if="selectedTimeFilter === option.value" class="filter-check">✓</view>
              </view>
            </view>

            <view v-if="showTypeFilterMenu" class="filter-dropdown type-filter-dropdown" @tap.stop>
              <view
                v-for="option in TYPE_FILTER_OPTIONS"
                :key="option.value"
                class="filter-option"
                :class="{ 'filter-option-active': selectedTypeFilter === option.value }"
                hover-class="filter-option-hover"
                @tap="onSelectTypeFilter(option.value)"
              >
                <text class="filter-option-text">{{ option.label }}</text>
                <view v-if="selectedTypeFilter === option.value" class="filter-check">✓</view>
              </view>
            </view>
          </view>
        </view>

        <view v-if="displayRecords.length > 0" class="tx-list">
          <WalletTransactionItem v-for="item in displayRecords" :key="item.id" :item="item" />
        </view>
        <view v-else class="empty-wrap">
          <view class="empty-icon-wrap">
            <image class="empty-icon" mode="aspectFit" src="/static/icon/block.png" />
          </view>
          <text class="empty-text">{{ emptyTipText }}</text>
        </view>

        <view v-if="loadingMore" class="load-tip">
          <view class="loading-spinner"></view>
          <text>加载中...</text>
        </view>
        <view v-else-if="!hasMore && displayRecords.length > 0" class="load-tip">没有更多了</view>
      </view>
    </scroll-view>

    <view v-if="showTimeFilterMenu || showTypeFilterMenu" class="filter-mask" @tap="closeAllFilterMenus"></view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onLoad, onPullDownRefresh, onReachBottom, onShow } from '@dcloudio/uni-app'
import { getMemberCenterOverview, getMemberOrders, getWalletRechargeOrders } from '../../../api/payment'
import { getCurrentUserProfile } from '../../../api/user'
import WalletBalanceCard from './components/WalletBalanceCard.vue'
import WalletTransactionItem from './components/WalletTransactionItem.vue'
import {
  formatWalletBalance,
  mapMemberOrderRecord,
  mapRechargeOrderRecord,
  mergeWalletRecords
} from './modules/wallet-view-model'

const TIME_FILTER_OPTIONS = [
  { label: '全部时间', value: 'all' },
  { label: '近一周', value: 'week' },
  { label: '近一月', value: 'month' },
  { label: '近一年', value: 'year' }
]

const TYPE_FILTER_OPTIONS = [
  { label: '全部', value: 'all' },
  { label: '支出', value: 'expense' },
  { label: '收入', value: 'income' }
]

const walletBalance = ref(0)
const walletId = ref('--')
const records = ref([])
const selectedTimeFilter = ref('all')
const selectedTypeFilter = ref('all')
const showTimeFilterMenu = ref(false)
const showTypeFilterMenu = ref(false)

const memberRecords = ref([])
const memberCursor = ref('')
const memberHasMore = ref(false)

const rechargeRecords = ref([])
const rechargeCursor = ref('')
const rechargeHasMore = ref(false)

const loadingMore = ref(false)
const hasMore = ref(false)

const displayBalance = computed(() => formatWalletBalance(walletBalance.value))

const timeFilterButtonText = computed(() => {
  const option = TIME_FILTER_OPTIONS.find((opt) => opt.value === selectedTimeFilter.value)
  return option?.label || '时间'
})

const typeFilterButtonText = computed(() => {
  const option = TYPE_FILTER_OPTIONS.find((opt) => opt.value === selectedTypeFilter.value)
  return option?.label || '类型'
})

const getTimeFilterTimestamp = () => {
  const now = Date.now()
  if (selectedTimeFilter.value === 'week') {
    return now - 7 * 24 * 60 * 60 * 1000
  }
  if (selectedTimeFilter.value === 'month') {
    return now - 30 * 24 * 60 * 60 * 1000
  }
  if (selectedTimeFilter.value === 'year') {
    return now - 365 * 24 * 60 * 60 * 1000
  }
  return 0
}

const displayRecords = computed(() => {
  let list = Array.isArray(records.value) ? records.value : []

  // 时间筛选
  const timeThreshold = getTimeFilterTimestamp()
  if (timeThreshold > 0) {
    list = list.filter((item) => {
      const itemTs = Number(item?.sortTs || 0)
      return itemTs >= timeThreshold
    })
  }

  // 类型筛选
  if (selectedTypeFilter.value === 'expense') {
    list = list.filter((item) => Number(item?.amount || 0) < 0)
  } else if (selectedTypeFilter.value === 'income') {
    list = list.filter((item) => Number(item?.amount || 0) > 0)
  }

  return list
})

const emptyTipText = computed(() => {
  if (selectedTypeFilter.value === 'expense') {
    return '暂无支出记录'
  }
  if (selectedTypeFilter.value === 'income') {
    return '暂无收入记录'
  }
  return '暂无收支记录'
})

const resolveWalletId = (profile = {}) => {
  const userIdRaw = String(profile?.userId || profile?.user_id || '').trim()
  if (!userIdRaw) {
    return '--'
  }
  return userIdRaw
}

const mergeRecords = (reset = false) => {
  const merged = mergeWalletRecords(memberRecords.value, rechargeRecords.value)
  records.value = merged
  hasMore.value = Boolean(memberHasMore.value || rechargeHasMore.value)
}

const closeAllFilterMenus = () => {
  showTimeFilterMenu.value = false
  showTypeFilterMenu.value = false
}

const loadWalletOverview = async () => {
  try {
    const overview = await getMemberCenterOverview()
    walletBalance.value = Number(overview?.wallet?.balance || 0)
  } catch {
    walletBalance.value = Number(walletBalance.value || 0)
  }
}

const loadProfile = async () => {
  try {
    const profile = await getCurrentUserProfile()
    walletId.value = resolveWalletId(profile || {})
    if (!Number.isFinite(Number(walletBalance.value)) || Number(walletBalance.value) <= 0) {
      walletBalance.value = Number(profile?.balance || 0)
    }
  } catch {
    walletId.value = '--'
  }
}

const loadMemberOrderRecords = async (reset = false) => {
  if (!reset && !memberHasMore.value) {
    return
  }

  try {
    const payload = await getMemberOrders({
      cursor: reset ? '' : memberCursor.value,
      limit: 20
    })
    const incoming = Array.isArray(payload?.items) ? payload.items.map((item) => mapMemberOrderRecord(item)) : []
    memberRecords.value = reset ? incoming : [...memberRecords.value, ...incoming]
    memberCursor.value = String(payload?.next_cursor || '').trim()
    memberHasMore.value = Boolean(payload?.has_more) && Boolean(memberCursor.value)
  } catch {
    if (reset) {
      memberRecords.value = []
    }
    memberHasMore.value = false
    memberCursor.value = ''
  }
}

const loadRechargeOrderRecords = async (reset = false) => {
  if (!reset && !rechargeHasMore.value) {
    return
  }

  try {
    const payload = await getWalletRechargeOrders({
      cursor: reset ? '' : rechargeCursor.value,
      limit: 20
    })
    const incoming = Array.isArray(payload?.items) ? payload.items.map((item) => mapRechargeOrderRecord(item)) : []
    rechargeRecords.value = reset ? incoming : [...rechargeRecords.value, ...incoming]
    rechargeCursor.value = String(payload?.next_cursor || '').trim()
    rechargeHasMore.value = Boolean(payload?.has_more) && Boolean(rechargeCursor.value)
  } catch {
    if (reset) {
      rechargeRecords.value = []
    }
    rechargeHasMore.value = false
    rechargeCursor.value = ''
  }
}

const loadWalletRecords = async (reset = false) => {
  if (loadingMore.value) {
    return
  }
  if (!reset && !hasMore.value) {
    return
  }

  loadingMore.value = true
  try {
    await Promise.all([loadMemberOrderRecords(reset), loadRechargeOrderRecords(reset)])
    mergeRecords(reset)
  } finally {
    loadingMore.value = false
  }
}

const refreshWalletPage = async () => {
  await Promise.all([loadWalletOverview(), loadProfile()])
  await loadWalletRecords(true)
}

const onTapRecharge = () => {
  closeAllFilterMenus()
  uni.navigateTo({
    url: '/pages/me/wallet/recharge/index'
  })
}

const onTapTimeFilter = () => {
  showTypeFilterMenu.value = false
  showTimeFilterMenu.value = !showTimeFilterMenu.value
}

const onTapTypeFilter = () => {
  showTimeFilterMenu.value = false
  showTypeFilterMenu.value = !showTypeFilterMenu.value
}

const onSelectTimeFilter = (value) => {
  selectedTimeFilter.value = String(value || 'all')
  closeAllFilterMenus()
}

const onSelectTypeFilter = (value) => {
  selectedTypeFilter.value = String(value || 'all')
  closeAllFilterMenus()
}

onLoad(async () => {
  await refreshWalletPage()
})

onShow(async () => {
  await refreshWalletPage()
})

onPullDownRefresh(async () => {
  closeAllFilterMenus()
  try {
    await refreshWalletPage()
  } finally {
    uni.stopPullDownRefresh()
  }
})

onReachBottom(async () => {
  closeAllFilterMenus()
  await loadWalletRecords(false)
})
</script>

<style scoped>
.wallet-page {
  min-height: 100vh;
  height: 100vh;
  position: relative;
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
}

.wallet-scroll {
  height: 100%;
}

.wallet-content {
  padding: 32rpx 24rpx calc(48rpx + env(safe-area-inset-bottom));
}

.action-wrap {
  margin-top: 24rpx;
}

.recharge-btn {
  height: 88rpx;
  border-radius: 20rpx;
  background: linear-gradient(135deg, #1a57db 0%, #1e40af 100%);
  box-shadow: 0 8rpx 24rpx rgba(26, 87, 219, 0.25);
  overflow: hidden;
  position: relative;
  transition: all 0.2s ease;
}

.recharge-btn::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, transparent 100%);
  opacity: 0;
  transition: opacity 0.2s ease;
}

.recharge-btn-hover {
  transform: translateY(-2rpx);
  box-shadow: 0 12rpx 28rpx rgba(26, 87, 219, 0.35);
}

.recharge-btn-hover::before {
  opacity: 1;
}

.recharge-btn-inner {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12rpx;
}

.recharge-icon {
  width: 32rpx;
  height: 32rpx;
}

.recharge-text {
  color: #ffffff;
  font-size: 30rpx;
  font-weight: 600;
  letter-spacing: 1rpx;
}

.section-head {
  margin-top: 48rpx;
  margin-bottom: 20rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.section-title {
  color: #0f172a;
  font-size: 32rpx;
  font-weight: 700;
  letter-spacing: 0.5rpx;
}

.filter-row {
  display: flex;
  align-items: center;
  gap: 12rpx;
  position: relative;
  z-index: 30;
}

.filter-btn {
  padding: 0 20rpx;
  height: 56rpx;
  border-radius: 28rpx;
  background: #ffffff;
  border: 2rpx solid #e2e8f0;
  display: flex;
  align-items: center;
  gap: 8rpx;
  transition: all 0.2s ease;
}

.filter-btn-selected {
  background: rgba(26, 87, 219, 0.08);
  border-color: rgba(26, 87, 219, 0.2);
}

.filter-btn-hover {
  background: #f8fafc;
  border-color: #cbd5e1;
}

.filter-text {
  color: #475569;
  font-size: 24rpx;
  font-weight: 600;
}

.filter-btn-selected .filter-text {
  color: #1a57db;
}

.filter-icon {
  width: 20rpx;
  height: 20rpx;
  opacity: 0.6;
}

.filter-mask {
  position: fixed;
  inset: 0;
  z-index: 20;
  background: rgba(15, 23, 42, 0.1);
  backdrop-filter: blur(2rpx);
}

.filter-dropdown {
  position: absolute;
  top: calc(100% + 12rpx);
  min-width: 180rpx;
  padding: 8rpx;
  border-radius: 20rpx;
  background: #ffffff;
  border: 1rpx solid #e2e8f0;
  box-shadow: 0 16rpx 40rpx rgba(15, 23, 42, 0.12);
}

.time-filter-dropdown {
  right: 100rpx;
}

.type-filter-dropdown {
  right: 0;
}

.filter-option {
  min-height: 64rpx;
  padding: 0 20rpx;
  border-radius: 16rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
  transition: all 0.15s ease;
}

.filter-option-hover {
  background: #f8fafc;
}

.filter-option-active {
  background: rgba(26, 87, 219, 0.08);
}

.filter-option-text {
  color: #334155;
  font-size: 26rpx;
  font-weight: 600;
}

.filter-option-active .filter-option-text {
  color: #1a57db;
}

.filter-check {
  width: 28rpx;
  height: 28rpx;
  border-radius: 14rpx;
  background: #1a57db;
  color: #ffffff;
  font-size: 18rpx;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
}

.tx-list {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.empty-wrap {
  padding: 100rpx 0 60rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24rpx;
}

.empty-icon-wrap {
  width: 160rpx;
  height: 160rpx;
  border-radius: 80rpx;
  background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
  display: flex;
  align-items: center;
  justify-content: center;
}

.empty-icon {
  width: 80rpx;
  height: 80rpx;
  opacity: 0.4;
}

.empty-text {
  color: #94a3b8;
  font-size: 26rpx;
  font-weight: 500;
}

.load-tip {
  margin-top: 24rpx;
  margin-bottom: 20rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12rpx;
  color: #94a3b8;
  font-size: 24rpx;
}

.loading-spinner {
  width: 28rpx;
  height: 28rpx;
  border: 3rpx solid #e2e8f0;
  border-top-color: #1a57db;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@media (prefers-color-scheme: dark) {
  .wallet-page {
    background: linear-gradient(180deg, #0f172a 0%, #020617 100%);
  }

  .section-title {
    color: #f1f5f9;
  }

  .filter-btn {
    background: #1e293b;
    border-color: #334155;
  }

  .filter-btn-selected {
    background: rgba(59, 130, 246, 0.15);
    border-color: rgba(59, 130, 246, 0.3);
  }

  .filter-btn-hover {
    background: #334155;
    border-color: #475569;
  }

  .filter-text {
    color: #cbd5e1;
  }

  .filter-btn-selected .filter-text {
    color: #60a5fa;
  }

  .filter-mask {
    background: rgba(0, 0, 0, 0.3);
  }

  .filter-dropdown {
    background: #1e293b;
    border-color: #334155;
    box-shadow: 0 16rpx 40rpx rgba(0, 0, 0, 0.4);
  }

  .filter-option-hover {
    background: #334155;
  }

  .filter-option-active {
    background: rgba(59, 130, 246, 0.2);
  }

  .filter-option-text {
    color: #cbd5e1;
  }

  .filter-option-active .filter-option-text {
    color: #60a5fa;
  }

  .filter-check {
    background: #3b82f6;
  }

  .empty-icon-wrap {
    background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
  }

  .loading-spinner {
    border-color: #334155;
    border-top-color: #3b82f6;
  }
}
</style>
