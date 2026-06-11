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
      <view class="picker-wrap" @tap="emit('openIndustryPicker')">
        <text class="picker-text" :class="{ 'picker-text-placeholder': !industry }">
          {{ industry || '请选择行业' }}
        </text>
        <image class="picker-arrow" mode="aspectFit" src="https://cos.cnptec.site/static/me-icons/expand-more-slate.png" />
      </view>
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
  }
})

const emit = defineEmits(['update:name', 'update:industry', 'update:description', 'openIndustryPicker'])
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
  margin-bottom: 20rpx;
}

.field-block + .field-block {
  margin-top: 20rpx;
}

.field-label {
  display: block;
  color: #475569;
  font-size: 24rpx;
  line-height: 1.3;
  font-weight: 500;
  margin-bottom: 10rpx;
}

.field-input,
.picker-wrap,
.field-textarea {
  width: 100%;
  box-sizing: border-box;
  border-radius: 12rpx;
  border: 1rpx solid rgba(15, 23, 42, 0.08);
  background: #f8fafc;
  color: #0f172a;
}

.field-input {
  height: 88rpx;
  padding: 0 20rpx;
  font-size: 28rpx;
}

.picker-wrap {
  height: 88rpx;
  padding: 0 20rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.picker-text {
  color: #0f172a;
  font-size: 28rpx;
}

.picker-text-placeholder {
  color: #94a3b8;
}

.picker-arrow {
  width: 24rpx;
  height: 24rpx;
  opacity: 0.5;
}

.field-textarea {
  min-height: 180rpx;
  padding: 16rpx 20rpx;
  font-size: 26rpx;
  line-height: 1.5;
}

.field-placeholder {
  color: #94a3b8;
}

@media (prefers-color-scheme: dark) {
  .card {
    background: #0f172a;
  }

  .card-title {
    color: #f1f5f9;
  }

  .field-label {
    color: #94a3b8;
  }

  .field-input,
  .picker-wrap,
  .field-textarea {
    border-color: rgba(255, 255, 255, 0.08);
    background: #1e293b;
    color: #f1f5f9;
  }

  .picker-text {
    color: #f1f5f9;
  }

  .picker-text-placeholder,
  .field-placeholder {
    color: #64748b;
  }
}
</style>
