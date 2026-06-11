<template>
  <view class="wallet-page">
    <scroll-view class="wallet-scroll" scroll-y :show-scrollbar="false">
      <view class="wallet-content">
        <WalletBalanceCard :balance-text="displayBalance" :wallet-id="walletId" />

        <view class="action-wrap">
          <view class="recharge-btn" hover-class="recharge-btn-hover" @tap="onTapRecharge">
            <view class="recharge-btn-inner">
              <image class="recharge-icon" mode="aspectFit" src="https://cos.cnptec.site/static/icon/recharge.png" />
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
              <image class="filter-icon" mode="aspectFit" src="https://cos.cnptec.site/static/me-icons/tune-gray.png" />
            </view>

            <view
              class="filter-btn"
              :class="{ 'filter-btn-selected': selectedTypeFilter !== 'all' || showTypeFilterMenu }"
              hover-class="filter-btn-hover"
              @tap.stop="onTapTypeFilter"
            >
              <text class="filter-text">{{ typeFilterButtonText }}</text>
              <image class="filter-icon" mode="aspectFit" src="https://cos.cnptec.site/static/me-icons/tune-gray.png" />
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
            <image class="empty-icon" mode="aspectFit" src="https://cos.cnptec.site/static/icon/block.png" />
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
  background: #f5f5f5;
}

.wallet-scroll {
  height: 100%;
}

.wallet-content {
  padding: 32rpx 32rpx calc(48rpx + env(safe-area-inset-bottom));
}

.action-wrap {
  margin-top: 32rpx;
}

.recharge-btn {
  height: 96rpx;
  border-radius: 16rpx;
  background: #ffffff;
  border: 2rpx solid #e5e7eb;
  overflow: hidden;
  position: relative;
}

.recharge-btn-hover {
  background: #fafafa;
}

.recharge-btn-inner {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0;
}

.recharge-icon {
  display: none;
}

.recharge-text {
  color: #2563eb;
  font-size: 32rpx;
  font-weight: 400;
}

.section-head {
  margin-top: 48rpx;
  margin-bottom: 24rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.section-title {
  color: #111827;
  font-size: 32rpx;
  font-weight: 600;
}

.filter-row {
  display: flex;
  align-items: center;
  gap: 16rpx;
  position: relative;
}

.filter-btn {
  padding: 0 20rpx;
  height: 56rpx;
  border-radius: 8rpx;
  background: #f5f5f5;
  border: 0;
  display: flex;
  align-items: center;
  gap: 8rpx;
}

.filter-btn-selected {
  background: #e5e7eb;
}

.filter-btn-hover {
  background: #e5e7eb;
}

.filter-text {
  color: #6b7280;
  font-size: 26rpx;
  font-weight: 400;
}

.filter-btn-selected .filter-text {
  color: #111827;
}

.filter-icon {
  width: 20rpx;
  height: 20rpx;
  opacity: 0.5;
}

.filter-dropdown {
  position: absolute;
  top: calc(100% + 12rpx);
  min-width: 200rpx;
  padding: 8rpx;
  border-radius: 12rpx;
  background: #ffffff;
  border: 1rpx solid #e5e7eb;
  box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.1);
  z-index: 100;
}

.time-filter-dropdown {
  right: 100rpx;
}

.type-filter-dropdown {
  right: 0;
}

.filter-option {
  min-height: 72rpx;
  padding: 0 24rpx;
  border-radius: 8rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
}

.filter-option-hover {
  background: #f9fafb;
}

.filter-option-active {
  background: #f3f4f6;
}

.filter-option-text {
  color: #374151;
  font-size: 28rpx;
  font-weight: 400;
}

.filter-option-active .filter-option-text {
  color: #111827;
}

.filter-check {
  width: 32rpx;
  height: 32rpx;
  border-radius: 16rpx;
  background: #2563eb;
  color: #ffffff;
  font-size: 20rpx;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
}

.tx-list {
  background: #ffffff;
  border-radius: 16rpx;
  padding: 0 32rpx;
}

.empty-wrap {
  padding: 120rpx 32rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24rpx;
}

.empty-icon-wrap {
  width: 160rpx;
  height: 160rpx;
  border-radius: 80rpx;
  background: #f3f4f6;
  display: flex;
  align-items: center;
  justify-content: center;
}

.empty-icon {
  width: 80rpx;
  height: 80rpx;
  opacity: 0.3;
}

.empty-text {
  color: #9ca3af;
  font-size: 28rpx;
  font-weight: 400;
}

.load-tip {
  margin-top: 32rpx;
  margin-bottom: 24rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12rpx;
  color: #9ca3af;
  font-size: 26rpx;
}

.loading-spinner {
  width: 32rpx;
  height: 32rpx;
  border: 3rpx solid #e5e7eb;
  border-top-color: #2563eb;
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
    background: #000000;
  }

  .section-title {
    color: #f9fafb;
  }

  .recharge-btn {
    background: #1f2937;
    border-color: #374151;
  }

  .recharge-btn-hover {
    background: #111827;
  }

  .recharge-text {
    color: #60a5fa;
  }

  .filter-btn {
    background: #1f2937;
  }

  .filter-btn-selected {
    background: #374151;
  }

  .filter-btn-hover {
    background: #374151;
  }

  .filter-text {
    color: #9ca3af;
  }

  .filter-btn-selected .filter-text {
    color: #f9fafb;
  }

  .filter-dropdown {
    background: #1f2937;
    border-color: #374151;
  }

  .filter-option-hover {
    background: #374151;
  }

  .filter-option-active {
    background: #111827;
  }

  .filter-option-text {
    color: #d1d5db;
  }

  .filter-option-active .filter-option-text {
    color: #f9fafb;
  }

  .filter-check {
    background: #3b82f6;
  }

  .tx-list {
    background: #111827;
  }

  .empty-icon-wrap {
    background: #1f2937;
  }

  .loading-spinner {
    border-color: #374151;
    border-top-color: #3b82f6;
  }
}
</style>
