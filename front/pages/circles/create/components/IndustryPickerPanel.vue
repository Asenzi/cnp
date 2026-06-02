<template>
  <view v-if="visible" class="picker-mask" @tap="onClose">
    <view class="picker-panel" @tap.stop>
      <view class="panel-head">
        <text class="panel-title">选择行业</text>
        <text class="panel-subtitle">为圈子选择合适的行业分类</text>
      </view>

      <scroll-view class="options-scroll" scroll-y :show-scrollbar="false">
        <view class="option-grid">
          <view
            v-for="industry in industryOptions"
            :key="`industry-${industry}`"
            class="option-chip"
            :class="selectedIndustry === industry ? 'option-chip-active' : ''"
            @tap="onSelectIndustry(industry)"
          >
            <text
              class="option-chip-text"
              :class="selectedIndustry === industry ? 'option-chip-text-active' : ''"
            >
              {{ industry }}
            </text>
          </view>
        </view>
      </scroll-view>

      <view class="actions">
        <button class="cancel-btn" hover-class="cancel-btn-active" @tap="onClose">取消</button>
        <button class="confirm-btn" hover-class="confirm-btn-active" @tap="onConfirm">确定</button>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, watch } from 'vue'
import { INDUSTRY_OPTIONS } from '../../../../utils/industry-options'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  value: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['close', 'confirm'])

const selectedIndustry = ref('')

watch(
  () => props.visible,
  (visible) => {
    if (visible) {
      selectedIndustry.value = props.value
    }
  }
)

const industryOptions = INDUSTRY_OPTIONS

const onSelectIndustry = (industry) => {
  selectedIndustry.value = industry
}

const onClose = () => {
  emit('close')
}

const onConfirm = () => {
  emit('confirm', selectedIndustry.value)
}
</script>

<style scoped>
.picker-mask {
  position: fixed;
  inset: 0;
  z-index: 66;
  background: rgba(2, 6, 23, 0.45);
  display: flex;
  align-items: flex-end;
}

.picker-panel {
  width: 100%;
  max-height: 80vh;
  border-radius: 28rpx 28rpx 0 0;
  background: #ffffff;
  padding: 32rpx 24rpx calc(24rpx + env(safe-area-inset-bottom));
  display: flex;
  flex-direction: column;
}

.panel-head {
  display: flex;
  flex-direction: column;
  gap: 6rpx;
  flex-shrink: 0;
}

.panel-title {
  color: #0f172a;
  font-size: 32rpx;
  line-height: 44rpx;
  font-weight: 700;
}

.panel-subtitle {
  color: #64748b;
  font-size: 22rpx;
  line-height: 32rpx;
}

.options-scroll {
  margin-top: 24rpx;
  flex: 1;
  min-height: 0;
}

.option-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12rpx;
}

.option-chip {
  min-height: 72rpx;
  border-radius: 16rpx;
  padding: 0 20rpx;
  border: 1rpx solid #e2e8f0;
  background: #f8fafc;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.option-chip-active {
  background: rgba(26, 87, 219, 0.1);
  border-color: rgba(26, 87, 219, 0.35);
}

.option-chip-text {
  color: #475569;
  font-size: 24rpx;
  line-height: 32rpx;
  font-weight: 500;
}

.option-chip-text-active {
  color: #1a57db;
  font-weight: 700;
}

.actions {
  margin-top: 28rpx;
  display: flex;
  align-items: center;
  gap: 12rpx;
  flex-shrink: 0;
}

.cancel-btn,
.confirm-btn {
  height: 74rpx;
  border-radius: 14rpx;
  border: 0;
  font-size: 26rpx;
  line-height: 74rpx;
  font-weight: 700;
}

.cancel-btn::after,
.confirm-btn::after {
  border: 0;
}

.cancel-btn {
  flex: 1;
  background: #f1f5f9;
  color: #475569;
}

.confirm-btn {
  flex: 2;
  background: #1a57db;
  color: #ffffff;
}

.cancel-btn-active,
.confirm-btn-active {
  opacity: 0.85;
}

@media (prefers-color-scheme: dark) {
  .picker-mask {
    background: rgba(2, 6, 23, 0.62);
  }

  .picker-panel {
    background: #0f172a;
  }

  .panel-title {
    color: #f8fafc;
  }

  .panel-subtitle {
    color: #cbd5e1;
  }

  .option-chip {
    border-color: #334155;
    background: #1e293b;
  }

  .option-chip-text {
    color: #94a3b8;
  }

  .option-chip-active {
    border-color: rgba(59, 130, 246, 0.6);
    background: rgba(59, 130, 246, 0.15);
  }

  .option-chip-text-active {
    color: #93c5fd;
  }

  .cancel-btn {
    background: #1e293b;
    color: #cbd5e1;
  }
}
</style>
