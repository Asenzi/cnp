<template>
  <view class="card">
    <text class="card-title">圈子规则</text>

    <textarea
      :value="rules"
      class="rules-textarea"
      maxlength="1000"
      placeholder="请制定圈子规则（如：禁止发布广告、需实名认证等）"
      placeholder-class="rules-placeholder"
      @input="emit('update:rules', $event?.detail?.value || '')"
    />
  </view>
</template>

<script setup>
defineProps({
  rules: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['update:rules'])
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

.rules-textarea {
  width: 100%;
  box-sizing: border-box;
  min-height: 180rpx;
  border-radius: 12rpx;
  border: 1rpx solid rgba(15, 23, 42, 0.08);
  background: #f8fafc;
  padding: 16rpx 20rpx;
  color: #0f172a;
  font-size: 26rpx;
  line-height: 1.5;
}

.rules-placeholder {
  color: #94a3b8;
}

@media (prefers-color-scheme: dark) {
  .card {
    background: #0f172a;
  }

  .card-title {
    color: #f1f5f9;
  }

  .rules-textarea {
    border-color: rgba(255, 255, 255, 0.08);
    background: #1e293b;
    color: #f1f5f9;
  }

  .rules-placeholder {
    color: #64748b;
  }
}
</style>
