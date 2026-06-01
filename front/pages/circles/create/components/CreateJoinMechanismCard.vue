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
  margin: 0;
  background: #ffffff;
  padding: 24rpx 32rpx;
}

.card-title {
  display: block;
  color: #0f172a;
  font-size: 28rpx;
  line-height: 1.3;
  font-weight: 600;
  margin-bottom: 16rpx;
}

.options-wrap {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.option-row {
  border-radius: 12rpx;
  border: 1rpx solid rgba(15, 23, 42, 0.08);
  background: #f8fafc;
  padding: 16rpx 20rpx;
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.option-row-active {
  border-color: rgba(37, 99, 235, 0.2);
  background: rgba(37, 99, 235, 0.04);
}

.radio {
  width: 32rpx;
  height: 32rpx;
  border-radius: 999rpx;
  border: 2rpx solid #cbd5e1;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.option-row-active .radio {
  border-color: #2563eb;
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
  font-size: 26rpx;
  line-height: 1.3;
  font-weight: 500;
}

.option-desc {
  display: block;
  margin-top: 4rpx;
  color: #64748b;
  font-size: 22rpx;
  line-height: 1.3;
}

.price-wrap {
  flex-shrink: 0;
  border-radius: 8rpx;
  background: rgba(15, 23, 42, 0.04);
  padding: 8rpx 12rpx;
  display: flex;
  align-items: center;
  gap: 4rpx;
}

.price-symbol {
  color: #64748b;
  font-size: 22rpx;
  font-weight: 500;
}

.price-input {
  width: 92rpx;
  height: 36rpx;
  border: 0;
  background: transparent;
  color: #2563eb;
  font-size: 24rpx;
  font-weight: 600;
}

.price-placeholder {
  color: #94a3b8;
}

@media (prefers-color-scheme: dark) {
  .card {
    background: #0f172a;
  }

  .card-title,
  .option-title {
    color: #f1f5f9;
  }

  .option-row {
    border-color: rgba(255, 255, 255, 0.08);
    background: #1e293b;
  }

  .option-row-active {
    border-color: rgba(59, 130, 246, 0.25);
    background: rgba(59, 130, 246, 0.08);
  }

  .option-desc {
    color: #94a3b8;
  }

  .radio {
    border-color: #475569;
  }

  .option-row-active .radio {
    border-color: #60a5fa;
  }

  .radio-dot {
    background: #60a5fa;
  }

  .price-wrap {
    background: rgba(255, 255, 255, 0.04);
  }

  .price-symbol {
    color: #94a3b8;
  }

  .price-input {
    color: #60a5fa;
  }
}
</style>
