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

    <view class="switch-row">
      <text class="switch-label">成员发布内容需审核</text>
      <switch
        :checked="needPostReview"
        color="#1a57db"
        @change="emit('update:needPostReview', Boolean($event?.detail?.value))"
      />
    </view>
  </view>
</template>

<script setup>
defineProps({
  rules: {
    type: String,
    default: ''
  },
  needPostReview: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:rules', 'update:needPostReview'])
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
  margin-bottom: 14rpx;
}

.rules-textarea {
  width: 100%;
  box-sizing: border-box;
  min-height: 180rpx;
  border-radius: 12rpx;
  border: 1rpx solid #e2e8f0;
  background: #f8fafc;
  padding: 14rpx 18rpx;
  color: #0f172a;
  font-size: 24rpx;
  line-height: 34rpx;
}

.rules-placeholder {
  color: #94a3b8;
}

.switch-row {
  margin-top: 14rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.switch-label {
  color: #334155;
  font-size: 24rpx;
  line-height: 32rpx;
}

@media (prefers-color-scheme: dark) {
  .card {
    background: #0f172a;
    box-shadow: none;
  }

  .card-title {
    color: #f8fafc;
  }

  .rules-textarea {
    border-color: #334155;
    background: #1e293b;
    color: #f8fafc;
  }

  .rules-placeholder {
    color: #64748b;
  }

  .switch-label {
    color: #cbd5e1;
  }
}
</style>
