<script setup lang="ts">
import type { ProductSafetyOverview } from '#/api/admin';

import { computed, onMounted, ref } from 'vue';

import {
  ElAlert,
  ElButton,
  ElCard,
  ElCol,
  ElRow,
  ElSkeleton,
  ElStatistic,
  ElTag,
} from 'element-plus';

import { getAdminProductSafetyOverviewApi } from '#/api/admin';
import { formatCompactNumber } from '#/utils/admin';

defineOptions({ name: 'AdminProductSafetyPage' });

const loading = ref(false);
const overview = ref<ProductSafetyOverview>({
  alerts: {
    review_failure_spike: false,
    review_rejection_spike: false,
  },
  new_users: 0,
  punishments: 0,
  reports: 0,
  retry_pending: 0,
  review_failed: 0,
  review_rejected: 0,
  risk_levels: {},
  window_hours: 24,
});

const cards = computed(() => [
  {
    description: `${overview.value.window_hours} 小时内新增`,
    key: 'new_users',
    title: '新用户',
    value: overview.value.new_users,
  },
  {
    description: '用户提交的风险举报',
    key: 'reports',
    title: '举报',
    value: overview.value.reports,
  },
  {
    description: '命中色情/违规等审核拒绝',
    key: 'review_rejected',
    title: '审核拒绝',
    value: overview.value.review_rejected,
  },
  {
    description: '供应商失败，等待重试',
    key: 'retry_pending',
    title: '待重试',
    value: overview.value.retry_pending,
  },
  {
    description: '限改、禁言、封禁等处置',
    key: 'punishments',
    title: '处罚',
    value: overview.value.punishments,
  },
  {
    description: '微信/IMS 调用失败',
    key: 'review_failed',
    title: '审核失败',
    value: overview.value.review_failed,
  },
]);

const riskRows = computed(() =>
  Object.entries(overview.value.risk_levels || {})
    .sort(([left], [right]) => left.localeCompare(right))
    .map(([level, count]) => ({ count, level })),
);

const hasAlert = computed(
  () =>
    overview.value.alerts.review_failure_spike ||
    overview.value.alerts.review_rejection_spike,
);

async function loadOverview() {
  loading.value = true;
  try {
    overview.value = await getAdminProductSafetyOverviewApi();
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  void loadOverview();
});
</script>

<template>
  <div class="space-y-4 p-5">
    <div class="flex items-center justify-between gap-3">
      <div class="space-y-1">
        <h1 class="text-2xl font-semibold text-slate-900">产品安全</h1>
        <p class="text-sm text-slate-500">
          查看头像、资料、举报和风控处置的 24 小时态势。
        </p>
      </div>
      <ElButton :loading="loading" type="primary" @click="loadOverview">
        刷新
      </ElButton>
    </div>

    <ElAlert
      v-if="hasAlert"
      :closable="false"
      show-icon
      title="产品安全告警"
      type="error"
    >
      <template #default>
        <span v-if="overview.alerts.review_failure_spike">
          审核失败量异常，请检查微信内容安全或 IMS 配置。
        </span>
        <span v-if="overview.alerts.review_rejection_spike">
          违规拒绝量异常，请关注新用户涌入和头像资料风险。
        </span>
      </template>
    </ElAlert>

    <ElSkeleton :loading="loading" animated>
      <template #template>
        <div class="grid grid-cols-1 gap-4 md:grid-cols-3">
          <div v-for="item in 6" :key="item" class="h-28 rounded-xl bg-slate-100" />
        </div>
      </template>

      <ElRow :gutter="16">
        <ElCol
          v-for="card in cards"
          :key="card.key"
          :lg="8"
          :md="12"
          :sm="12"
          :xs="24"
          class="mb-4"
        >
          <ElCard shadow="never" class="h-full rounded-2xl border-0">
            <ElStatistic
              :formatter="() => formatCompactNumber(card.value)"
              :title="card.title"
              :value="card.value"
            />
            <div class="mt-3 text-sm text-slate-500">
              {{ card.description }}
            </div>
          </ElCard>
        </ElCol>
      </ElRow>

      <ElCard shadow="never" class="rounded-2xl border-0">
        <template #header>
          <span class="font-semibold text-slate-900">用户风险等级</span>
        </template>
        <div class="flex flex-wrap gap-3">
          <ElTag
            v-for="row in riskRows"
            :key="row.level"
            :type="row.level === 'L0' ? 'success' : 'warning'"
            size="large"
          >
            {{ row.level }}：{{ formatCompactNumber(row.count) }}
          </ElTag>
          <span v-if="riskRows.length === 0" class="text-sm text-slate-500">
            暂无风险等级数据
          </span>
        </div>
      </ElCard>
    </ElSkeleton>
  </div>
</template>
