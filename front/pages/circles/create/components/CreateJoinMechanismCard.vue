<template>
  <view class="card">
    <view class="option-row">
      <view class="radio">
        <view class="radio-dot"></view>
      </view>

      <view class="option-main">
        <text class="option-title">付费入圈</text>
        <text class="option-desc">支付入圈费用后，由圈主审核通过</text>
      </view>

      <view class="price-trigger" @tap="pricePickerVisible = true">
        <text class="price-trigger-text">￥{{ currentPrice }}</text>
      </view>
    </view>

    <view v-if="pricePickerVisible" class="drawer-mask" @tap="pricePickerVisible = false">
      <view class="price-drawer" @tap.stop>
        <view class="drawer-header">
          <text class="drawer-title">选择入圈价格</text>
          <text class="drawer-close" @tap="pricePickerVisible = false">取消</text>
        </view>
        <view class="price-grid">
          <view
            v-for="tier in priceTiers"
            :key="tier"
            class="price-tier"
            :class="{ 'price-tier-active': Number(price) === tier }"
            @tap="selectPrice(tier)"
          >
            <text>￥{{ tier }}</text>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  price: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['update:price'])
const pricePickerVisible = ref(false)
const priceTiers = [98, 198, 398, 598, 980, 1980, 3980, 5980, 9980]
const currentPrice = computed(() => (priceTiers.includes(Number(props.price)) ? Number(props.price) : 98))

const selectPrice = (tier) => {
  emit('update:price', String(tier))
  pricePickerVisible.value = false
}
</script>

<style scoped>
.card {
  margin: 0;
  background: #ffffff;
  padding: 24rpx 32rpx;
}

.option-row {
  border-radius: 12rpx;
  background: #f8fafc;
  padding: 20rpx;
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.radio {
  width: 32rpx;
  height: 32rpx;
  border-radius: 999rpx;
  border: 2rpx solid #2563eb;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.radio-dot {
  width: 16rpx;
  height: 16rpx;
  border-radius: 999rpx;
  background: #2563eb;
}

.option-main {
  flex: 1;
  min-width: 0;
}

.option-title {
  display: block;
  color: #0f172a;
  font-size: 28rpx;
  line-height: 1.3;
  font-weight: 600;
}

.option-desc {
  display: block;
  margin-top: 4rpx;
  color: #64748b;
  font-size: 22rpx;
  line-height: 1.35;
}

.price-trigger {
  flex-shrink: 0;
  min-width: 136rpx;
  height: 56rpx;
  border-radius: 8rpx;
  background: rgba(37, 99, 235, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #2563eb;
}

.price-trigger-text {
  font-size: 26rpx;
  font-weight: 700;
}

.drawer-mask {
  position: fixed;
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
  z-index: 999;
  background: rgba(15, 23, 42, 0.45);
  display: flex;
  align-items: flex-end;
}

.price-drawer {
  width: 100%;
  border-radius: 28rpx 28rpx 0 0;
  background: #ffffff;
  padding: 28rpx 32rpx calc(32rpx + env(safe-area-inset-bottom));
}

.drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24rpx;
}

.drawer-title {
  color: #0f172a;
  font-size: 30rpx;
  font-weight: 700;
}

.drawer-close {
  color: #64748b;
  font-size: 26rpx;
}

.price-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16rpx;
}

.price-tier {
  height: 84rpx;
  border-radius: 12rpx;
  background: #f1f5f9;
  color: #475569;
  font-size: 28rpx;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
}

.price-tier-active {
  background: rgba(37, 99, 235, 0.12);
  color: #2563eb;
}

@media (prefers-color-scheme: dark) {
  .card,
  .price-drawer {
    background: #0f172a;
  }

  .option-row,
  .price-tier {
    background: #1e293b;
  }

  .option-title,
  .drawer-title {
    color: #f1f5f9;
  }

  .option-desc,
  .drawer-close {
    color: #94a3b8;
  }

  .price-tier {
    color: #cbd5e1;
  }

  .price-tier-active {
    background: rgba(59, 130, 246, 0.18);
    color: #60a5fa;
  }
}
</style>
