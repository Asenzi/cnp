<template>
  <view v-if="visible" class="filter-mask" @tap="onClose">
    <view class="filter-panel" @tap.stop>
      <view class="panel-head">
        <text class="panel-title">{{ uiText.panelTitle }}</text>
        <text class="panel-subtitle">{{ uiText.panelSubtitle }}</text>
      </view>

      <view class="section">
        <view class="section-label">{{ uiText.industrySection }}</view>
        <view class="option-grid">
          <view
            v-for="industry in industryOptions"
            :key="`industry-${industry}`"
            class="option-chip"
            :class="draft.industry_label === industry ? 'option-chip-active' : ''"
            @tap="setIndustry(industry)"
          >
            <text
              class="option-chip-text"
              :class="draft.industry_label === industry ? 'option-chip-text-active' : ''"
            >
              {{ industry }}
            </text>
          </view>
        </view>
      </view>

      <view class="actions">
        <button class="reset-btn" hover-class="reset-btn-active" @tap="onReset">{{ uiText.resetButton }}</button>
        <button class="apply-btn" hover-class="apply-btn-active" @tap="onApply">{{ uiText.applyButton }}</button>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { DEFAULT_INDUSTRY_OPTIONS } from '../modules/industry-options'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  value: {
    type: Object,
    default: () => ({})
  },
  options: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['close', 'apply', 'reset'])

const uiText = {
  panelTitle: '\u9009\u62e9\u884c\u4e1a',
  panelSubtitle: '\u7528\u4e8e\u7f29\u5c0f\u5f53\u524d\u63a8\u8350\u8303\u56f4',
  industrySection: '\u884c\u4e1a\u65b9\u5411',
  resetButton: '\u4e0d\u9650\u884c\u4e1a',
  applyButton: '\u5e94\u7528\u884c\u4e1a'
}

const normalizeFilters = (input = {}) => ({
  industry_label: String(input.industry_label || '').trim()
})

const draft = ref(normalizeFilters(props.value))

watch(
  () => props.visible,
  (visible) => {
    if (visible) {
      draft.value = normalizeFilters(props.value)
    }
  }
)

const industryOptions = computed(() => {
  const candidate = Array.isArray(props.options?.industries)
    ? props.options.industries.map((item) => String(item || '').trim()).filter(Boolean)
    : []
  return candidate.length ? candidate : DEFAULT_INDUSTRY_OPTIONS
})

const setIndustry = (rawValue) => {
  draft.value.industry_label = String(rawValue || '').trim()
}

const onClose = () => {
  emit('close')
}

const onReset = () => {
  draft.value = {
    industry_label: ''
  }
  emit('reset', normalizeFilters(draft.value))
}

const onApply = () => {
  emit('apply', normalizeFilters(draft.value))
}
</script>

<style scoped>
.filter-mask {
  position: fixed;
  inset: 0;
  z-index: 66;
  background: rgba(2, 6, 23, 0.45);
  display: flex;
  align-items: flex-end;
}

.filter-panel {
  width: 100%;
  border-radius: 28rpx 28rpx 0 0;
  background: #ffffff;
  padding: 32rpx 24rpx calc(24rpx + env(safe-area-inset-bottom));
}

.panel-head {
  display: flex;
  flex-direction: column;
  gap: 6rpx;
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

.section {
  margin-top: 24rpx;
}

.section-label {
  color: #334155;
  font-size: 24rpx;
  line-height: 34rpx;
  font-weight: 600;
}

.option-grid {
  margin-top: 16rpx;
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
}

.reset-btn,
.apply-btn {
  height: 74rpx;
  border-radius: 14rpx;
  border: 0;
  font-size: 26rpx;
  line-height: 74rpx;
  font-weight: 700;
}

.reset-btn::after,
.apply-btn::after {
  border: 0;
}

.reset-btn {
  flex: 1;
  background: #f1f5f9;
  color: #475569;
}

.apply-btn {
  flex: 2;
  background: #1a57db;
  color: #ffffff;
}

.reset-btn-active,
.apply-btn-active {
  opacity: 0.85;
}

@media (prefers-color-scheme: dark) {
  .filter-mask {
    background: rgba(2, 6, 23, 0.62);
  }

  .filter-panel {
    background: #0f172a;
  }

  .panel-title {
    color: #f8fafc;
  }

  .panel-subtitle,
  .section-label {
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

  .reset-btn {
    background: #1e293b;
    color: #cbd5e1;
  }
}
</style>
