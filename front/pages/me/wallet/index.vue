<template>
  <view class="wallet-page">
    <scroll-view class="wallet-scroll" scroll-y :show-scrollbar="false">
      <view class="wallet-content">
        <WalletBalanceCard :balance-text="displayBalance" :wallet-id="walletId" />

        <view class="action-wrap">
          <button class="recharge-btn" hover-class="recharge-btn-active" @tap="onTapRecharge" @click="onTapRecharge">
            <image class="recharge-icon" mode="aspectFit" src="/static/me-icons/payments-green.png" />
            <text>充值</text>
          </button>
        </view>

        <view class="section-head">
          <text class="section-title">收支明细</text>

          <view class="filter-wrap">
            <button
              class="filter-btn"
              :class="{ 'filter-btn-selected': selectedFilter !== 'all' || showFilterMenu }"
              hover-class="filter-btn-active"
              @tap.stop="onTapFilter"
            >
              <text>{{ filterButtonText }}</text>
              <image class="filter-icon" mode="aspectFit" src="/static/me-icons/tune-gray.png" />
            </button>

            <view v-if="showFilterMenu" class="filter-dropdown" @tap.stop>
              <view
                v-for="option in FILTER_OPTIONS"
                :key="option.value"
                class="filter-option"
                :class="{ 'filter-option-active': selectedFilter === option.value }"
                @tap="onSelectFilter(option.value)"
              >
                <text class="filter-option-text">{{ option.label }}</text>
              </view>
            </view>
          </view>
        </view>

        <view v-if="displayRecords.length > 0" class="tx-list">
          <WalletTransactionItem v-for="item in displayRecords" :key="item.id" :item="item" />
        </view>
        <view v-else class="empty-tip">{{ emptyTipText }}</view>

        <view v-if="loadingMore" class="load-tip">加载中...</view>
        <view v-else-if="!hasMore && displayRecords.length > 0" class="load-tip">没有更多记录了</view>

        <WalletSafetyNotice />

        <view class="wallet-footer">
          <view class="footer-brand-row">
            <image class="footer-shield" mode="aspectFit" src="/static/me-icons/shield-person-primary.png" />
            <text class="footer-brand">由 SAPPHIRE LEDGER 提供安全保护</text>
          </view>
          <text class="footer-copy">© 2024 QuanMaiLian Business Ecosystem</text>
        </view>
      </view>
    </scroll-view>

    <view v-if="showFilterMenu" class="filter-mask" @tap="closeFilterMenu"></view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onLoad, onPullDownRefresh, onReachBottom, onShow } from '@dcloudio/uni-app'
import { getMemberCenterOverview, getMemberOrders, getWalletRechargeOrders } from '../../../api/payment'
import { getCurrentUserProfile } from '../../../api/user'
import WalletBalanceCard from './components/WalletBalanceCard.vue'
import WalletSafetyNotice from './components/WalletSafetyNotice.vue'
import WalletTransactionItem from './components/WalletTransactionItem.vue'
import {
  formatWalletBalance,
  mapMemberOrderRecord,
  mapRechargeOrderRecord,
  mergeWalletRecords,
  withFallbackRecords
} from './modules/wallet-view-model'

const FILTER_OPTIONS = [
  { label: '全部', value: 'all' },
  { label: '支出', value: 'expense' },
  { label: '收入', value: 'income' }
]

const walletBalance = ref(0)
const walletId = ref('--')
const records = ref([])
const selectedFilter = ref('all')
const showFilterMenu = ref(false)

const memberRecords = ref([])
const memberCursor = ref('')
const memberHasMore = ref(false)

const rechargeRecords = ref([])
const rechargeCursor = ref('')
const rechargeHasMore = ref(false)

const loadingMore = ref(false)
const hasMore = ref(false)

const displayBalance = computed(() => formatWalletBalance(walletBalance.value))
const filterButtonText = computed(() => {
  if (selectedFilter.value === 'expense') {
    return '支出'
  }
  if (selectedFilter.value === 'income') {
    return '收入'
  }
  return '筛选'
})
const displayRecords = computed(() => {
  const list = Array.isArray(records.value) ? records.value : []
  if (selectedFilter.value === 'expense') {
    return list.filter((item) => Number(item?.amount || 0) < 0)
  }
  if (selectedFilter.value === 'income') {
    return list.filter((item) => Number(item?.amount || 0) > 0)
  }
  return list
})
const emptyTipText = computed(() => {
  if (selectedFilter.value === 'expense') {
    return '暂无支出记录'
  }
  if (selectedFilter.value === 'income') {
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
  records.value = reset ? withFallbackRecords(merged) : merged
  hasMore.value = Boolean(memberHasMore.value || rechargeHasMore.value)
}

const closeFilterMenu = () => {
  showFilterMenu.value = false
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
  closeFilterMenu()
  uni.navigateTo({
    url: '/pages/me/wallet/recharge/index'
  })
}

const onTapFilter = () => {
  showFilterMenu.value = !showFilterMenu.value
}

const onSelectFilter = (value) => {
  selectedFilter.value = String(value || 'all')
  closeFilterMenu()
}

onLoad(async () => {
  await refreshWalletPage()
})

onShow(async () => {
  await refreshWalletPage()
})

onPullDownRefresh(async () => {
  closeFilterMenu()
  try {
    await refreshWalletPage()
  } finally {
    uni.stopPullDownRefresh()
  }
})

onReachBottom(async () => {
  closeFilterMenu()
  await loadWalletRecords(false)
})
</script>

<style scoped>
.wallet-page {
  min-height: 100vh;
  height: 100vh;
  position: relative;
  background: #f6f6f8;
}

.wallet-scroll {
  height: 100%;
}

.wallet-content {
  padding: 24rpx 32rpx calc(48rpx + env(safe-area-inset-bottom));
}

.action-wrap {
  margin-top: 36rpx;
}

.recharge-btn {
  height: 88rpx;
  border-radius: 28rpx;
  border: 0;
  background: #1a57db;
  color: #ffffff;
  font-size: 32rpx;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12rpx;
  box-shadow: 0 10rpx 26rpx rgba(26, 87, 219, 0.2);
}

.recharge-btn::after {
  border: 0;
}

.recharge-icon {
  width: 34rpx;
  height: 34rpx;
}

.recharge-btn-active {
  opacity: 0.92;
}

.section-head {
  margin-top: 44rpx;
  margin-bottom: 20rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.section-title {
  color: #0f172a;
  font-size: 34rpx;
  font-weight: 700;
}

.filter-wrap {
  position: relative;
  z-index: 30;
}

.filter-btn {
  margin: 0;
  padding: 0 16rpx;
  height: 54rpx;
  border-radius: 18rpx;
  border: 0;
  background: rgba(26, 87, 219, 0.08);
  color: #1a57db;
  font-size: 24rpx;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 6rpx;
}

.filter-btn-selected {
  background: rgba(26, 87, 219, 0.14);
}

.filter-btn::after {
  border: 0;
}

.filter-icon {
  width: 24rpx;
  height: 24rpx;
}

.filter-btn-active {
  opacity: 0.82;
}

.filter-mask {
  position: fixed;
  inset: 0;
  z-index: 20;
  background: transparent;
}

.filter-dropdown {
  position: absolute;
  top: calc(100% + 12rpx);
  right: 0;
  min-width: 168rpx;
  padding: 12rpx;
  border-radius: 24rpx;
  background: #ffffff;
  box-shadow: 0 14rpx 36rpx rgba(15, 23, 42, 0.12);
}

.filter-option {
  min-height: 64rpx;
  padding: 0 18rpx;
  border-radius: 16rpx;
  display: flex;
  align-items: center;
}

.filter-option-active {
  background: rgba(26, 87, 219, 0.08);
}

.filter-option-text {
  color: #0f172a;
  font-size: 24rpx;
  font-weight: 600;
}

.tx-list {
  display: flex;
  flex-direction: column;
  gap: 18rpx;
}

.empty-tip {
  padding: 32rpx 0 12rpx;
  text-align: center;
  color: #94a3b8;
  font-size: 24rpx;
}

.load-tip {
  margin-top: 20rpx;
  text-align: center;
  color: #94a3b8;
  font-size: 22rpx;
}

.wallet-footer {
  margin-top: 36rpx;
  padding: 12rpx 0 8rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8rpx;
}

.footer-brand-row {
  display: flex;
  align-items: center;
  gap: 8rpx;
}

.footer-shield {
  width: 24rpx;
  height: 24rpx;
}

.footer-brand {
  color: #94a3b8;
  font-size: 18rpx;
  font-weight: 700;
  letter-spacing: 1rpx;
}

.footer-copy {
  color: #cbd5e1;
  font-size: 16rpx;
}

@media (prefers-color-scheme: dark) {
  .wallet-page {
    background: #111621;
  }

  .section-title {
    color: #f8fafc;
  }

  .filter-dropdown {
    background: #0f172a;
    box-shadow: 0 14rpx 36rpx rgba(15, 23, 42, 0.4);
  }

  .filter-option-active {
    background: rgba(59, 130, 246, 0.18);
  }

  .filter-option-text {
    color: #e2e8f0;
  }

  .footer-brand {
    color: #64748b;
  }

  .footer-copy {
    color: #475569;
  }
}
</style>
