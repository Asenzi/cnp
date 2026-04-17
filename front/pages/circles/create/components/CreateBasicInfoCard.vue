<template>
  <view class="card">
    <text class="card-title">基本信息</text>

    <view class="field-block">
      <text class="field-label">圈子名称</text>
      <input
        :value="name"
        class="field-input"
        type="text"
        maxlength="40"
        placeholder="请输入圈子名称（例如：华南创业者协会）"
        placeholder-class="field-placeholder"
        @input="emit('update:name', $event?.detail?.value || '')"
      />
    </view>

    <view class="field-block">
      <text class="field-label">所属行业/分类</text>
      <picker :range="industryOptions" :value="industryIndex" @change="onChangeIndustry">
        <view class="picker-wrap">
          <text class="picker-text" :class="{ 'picker-text-placeholder': !industry }">
            {{ industry || '请选择行业' }}
          </text>
          <image class="picker-arrow" mode="aspectFit" src="/static/me-icons/expand-more-slate.png" />
        </view>
      </picker>
    </view>

    <view class="field-block">
      <text class="field-label">圈子简介</text>
      <textarea
        :value="description"
        class="field-textarea"
        maxlength="500"
        placeholder="请简要介绍圈子的背景、目的以及能提供的资源..."
        placeholder-class="field-placeholder"
        @input="emit('update:description', $event?.detail?.value || '')"
      />
    </view>
  </view>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  name: {
    type: String,
    default: ''
  },
  industry: {
    type: String,
    default: ''
  },
  description: {
    type: String,
    default: ''
  },
  industryOptions: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['update:name', 'update:industry', 'update:description'])

const industryIndex = computed(() => {
  if (!props.industry) {
    return 0
  }
  const idx = props.industryOptions.findIndex((item) => item === props.industry)
  return idx < 0 ? 0 : idx
})

const onChangeIndustry = (event) => {
  const index = Number(event?.detail?.value ?? -1)
  if (index >= 0 && index < props.industryOptions.length) {
    emit('update:industry', props.industryOptions[index])
  }
}
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
  margin-bottom: 20rpx;
}

.field-block + .field-block {
  margin-top: 20rpx;
}

.field-label {
  display: block;
  color: #334155;
  font-size: 24rpx;
  line-height: 32rpx;
  font-weight: 600;
  margin-bottom: 10rpx;
}

.field-input,
.picker-wrap,
.field-textarea {
  width: 100%;
  box-sizing: border-box;
  border-radius: 12rpx;
  border: 1rpx solid #e2e8f0;
  background: #f8fafc;
  color: #0f172a;
}

.field-input {
  height: 88rpx;
  padding: 0 18rpx;
  font-size: 26rpx;
}

.picker-wrap {
  height: 88rpx;
  padding: 0 18rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.picker-text {
  color: #0f172a;
  font-size: 26rpx;
}

.picker-text-placeholder {
  color: #94a3b8;
}

.picker-arrow {
  width: 24rpx;
  height: 24rpx;
  opacity: 0.72;
}

.field-textarea {
  min-height: 180rpx;
  padding: 16rpx 18rpx;
  font-size: 24rpx;
  line-height: 34rpx;
}

.field-placeholder {
  color: #94a3b8;
}

@media (prefers-color-scheme: dark) {
  .card {
    background: #0f172a;
    box-shadow: none;
  }

  .card-title {
    color: #f8fafc;
  }

  .field-label {
    color: #cbd5e1;
  }

  .field-input,
  .picker-wrap,
  .field-textarea {
    border-color: #334155;
    background: #1e293b;
    color: #f8fafc;
  }

  .picker-text {
    color: #f8fafc;
  }

  .picker-text-placeholder,
  .field-placeholder {
    color: #64748b;
  }
}
</style>
