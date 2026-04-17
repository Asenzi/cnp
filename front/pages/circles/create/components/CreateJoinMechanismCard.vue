<template>
  <view class="card">
    <text class="card-title">加入机制</text>

    <view class="options-wrap">
      <view
        v-for="option in joinTypeOptions"
        :key="option.key"
        class="option-row"
        :class="{ 'option-row-active': joinType === option.key }"
        @tap="emit('update:joinType', option.key)"
      >
        <view class="radio">
          <view v-if="joinType === option.key" class="radio-dot"></view>
        </view>

        <view class="option-main">
          <text class="option-title">{{ option.title }}</text>
          <text class="option-desc">{{ option.desc }}</text>
        </view>

        <view v-if="option.key === 'paid'" class="price-wrap" @tap.stop>
          <text class="price-symbol">￥</text>
          <input
            :value="price"
            class="price-input"
            type="digit"
            maxlength="10"
            placeholder="0.00"
            placeholder-class="price-placeholder"
            @input="emit('update:price', $event?.detail?.value || '')"
          />
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
defineProps({
  joinType: {
    type: String,
    default: 'free'
  },
  price: {
    type: String,
    default: ''
  },
  joinTypeOptions: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['update:joinType', 'update:price'])
</script>

<style scoped>
.card {
  margin: 0 32rpx;
  background: #ffffff;
  border-radius: 20rpx;
  box-shadow: 0 2rpx 10rpx rgba(15, 23, 42, 0.05);
  padding: 24rpx;
}

.card-title {
  display: block;
  color: #0f172a;
  font-size: 32rpx;
  line-height: 42rpx;
  font-weight: 700;
  margin-bottom: 18rpx;
}

.options-wrap {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.option-row {
  border-radius: 12rpx;
  border: 1rpx solid #e2e8f0;
  padding: 16rpx;
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.option-row-active {
  border-color: rgba(26, 87, 219, 0.55);
  background: rgba(26, 87, 219, 0.04);
}

.radio {
  width: 30rpx;
  height: 30rpx;
  border-radius: 999rpx;
  border: 2rpx solid #cbd5e1;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.radio-dot {
  width: 16rpx;
  height: 16rpx;
  border-radius: 999rpx;
  background: #1a57db;
}

.option-main {
  flex: 1;
  min-width: 0;
}

.option-title {
  display: block;
  color: #0f172a;
  font-size: 24rpx;
  line-height: 32rpx;
  font-weight: 600;
}

.option-desc {
  display: block;
  margin-top: 4rpx;
  color: #64748b;
  font-size: 20rpx;
  line-height: 28rpx;
}

.price-wrap {
  flex-shrink: 0;
  border-radius: 10rpx;
  background: #f1f5f9;
  padding: 8rpx 10rpx;
  display: flex;
  align-items: center;
  gap: 6rpx;
}

.price-symbol {
  color: #64748b;
  font-size: 20rpx;
}

.price-input {
  width: 92rpx;
  height: 32rpx;
  border: 0;
  background: transparent;
  color: #1a57db;
  font-size: 22rpx;
  font-weight: 700;
}

.price-placeholder {
  color: #94a3b8;
}

@media (prefers-color-scheme: dark) {
  .card {
    background: #0f172a;
    box-shadow: none;
  }

  .card-title,
  .option-title {
    color: #f8fafc;
  }

  .option-row {
    border-color: #334155;
  }

  .option-row-active {
    border-color: rgba(59, 130, 246, 0.65);
    background: rgba(26, 87, 219, 0.15);
  }

  .option-desc {
    color: #94a3b8;
  }

  .radio {
    border-color: #475569;
  }

  .price-wrap {
    background: #1e293b;
  }

  .price-symbol {
    color: #94a3b8;
  }
}
</style>
