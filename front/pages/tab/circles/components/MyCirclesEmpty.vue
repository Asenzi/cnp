<template>
  <AppEmptyState><template #title>未找到匹配圈子</template><template #description>试试其他关键词</template></AppEmptyState>
</template>

<script setup>
import AppEmptyState from '../../../../components/AppEmptyState/AppEmptyState.vue'
</script>

<style scoped>
.empty-wrap {
  margin-top: 28rpx;
  background: transparent;
  min-height: 280rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60rpx 32rpx;
}

.empty-icon {
  width: 200rpx;
  height: 200rpx;
  margin-bottom: 12rpx;
}

.empty-title {
  color: #334155;
  font-size: 26rpx;
  line-height: 34rpx;
  font-weight: 600;
}

.empty-subtitle {
  margin-top: 6rpx;
  color: #94a3b8;
  font-size: 22rpx;
  line-height: 30rpx;
}

@media (prefers-color-scheme: dark) {
  .empty-wrap {
    background: transparent;
  }

  .empty-title {
    color: #cbd5e1;
  }

  .empty-subtitle {
    color: #64748b;
  }
}
</style>
