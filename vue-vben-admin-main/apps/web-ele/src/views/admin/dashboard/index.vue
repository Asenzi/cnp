<script setup lang="ts">
import type { DashboardOverview } from '#/api/admin';

import { computed, onMounted, ref } from 'vue';

import {
  ElCard,
  ElCol,
  ElRow,
  ElSkeleton,
  ElStatistic,
  ElTable,
  ElTableColumn,
  ElTag,
} from 'element-plus';

import { getAdminDashboardOverviewApi } from '#/api/admin';
import {
  formatAmount,
  formatCompactNumber,
  formatDateTime,
  formatPostMode,
  resolveStatusTagType,
} from '#/utils/admin';

defineOptions({ name: 'AdminDashboardPage' });

const loading = ref(false);
const overview = ref<DashboardOverview>({
  recent_circles: [],
  recent_posts: [],
  recent_recharges: [],
  recent_users: [],
  summary: {
    active_circle_total: 0,
    active_resource_total: 0,
    active_user_total: 0,
    circle_total: 0,
    notice_total: 0,
    paid_recharge_total: 0,
    pending_recharge_total: 0,
    pending_verification_total: 0,
    recharge_amount_total: 0,
    resource_total: 0,
    user_total: 0,
    verified_user_total: 0,
  },
});

const statCards = computed(() => {
  const summary = overview.value.summary;
  return [
    {
      description: `活跃 ${formatCompactNumber(summary.active_user_total)} / 已认证 ${formatCompactNumber(summary.verified_user_total)}`,
      displayValue: formatCompactNumber(summary.user_total),
      key: 'users',
      title: '总用户数',
      value: summary.user_total,
    },
    {
      description: `活跃圈子 ${formatCompactNumber(summary.active_circle_total)}`,
      displayValue: formatCompactNumber(summary.circle_total),
      key: 'circles',
      title: '总圈子数',
      value: summary.circle_total,
    },
    {
      description: `在线资源 ${formatCompactNumber(summary.active_resource_total)}`,
      displayValue: formatCompactNumber(summary.resource_total),
      key: 'posts',
      title: '资源总量',
      value: summary.resource_total,
    },
    {
      description: `系统通知 ${formatCompactNumber(summary.notice_total)}`,
      displayValue: formatCompactNumber(summary.pending_verification_total),
      key: 'verify',
      title: '待审认证',
      value: summary.pending_verification_total,
    },
    {
      description: `待支付 ${formatCompactNumber(summary.pending_recharge_total)}`,
      displayValue: formatCompactNumber(summary.paid_recharge_total),
      key: 'recharge',
      title: '已支付充值单',
      value: summary.paid_recharge_total,
    },
    {
      description: '累计已支付充值金额',
      displayValue: formatAmount(summary.recharge_amount_total),
      key: 'money',
      title: '充值金额',
      value: Number(summary.recharge_amount_total || 0),
    },
  ];
});

async function loadOverview() {
  loading.value = true;
  try {
    overview.value = await getAdminDashboardOverviewApi();
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
    <div class="space-y-1">
      <h1 class="text-2xl font-semibold text-slate-900">仪表盘</h1>
      <p class="text-sm text-slate-500">
        快速查看平台规模、待处理事项和最新业务动态。
      </p>
    </div>

    <ElRow :gutter="16">
      <ElCol
        v-for="card in statCards"
        :key="card.key"
        :lg="8"
        :md="12"
        :sm="12"
        :xs="24"
        class="mb-4"
      >
        <ElCard shadow="never" class="h-full rounded-2xl border-0">
          <ElStatistic
            :formatter="() => card.displayValue"
            :title="card.title"
            :value="card.value"
          />
          <div class="mt-3 text-sm text-slate-500">
            {{ card.description }}
          </div>
        </ElCard>
      </ElCol>
    </ElRow>

    <ElRow :gutter="16">
      <ElCol :lg="12" :xs="24" class="mb-4">
        <ElCard shadow="never" class="rounded-2xl border-0">
          <template #header>
            <div class="flex items-center justify-between">
              <span class="font-semibold text-slate-900">最近注册用户</span>
              <span class="text-xs text-slate-400">最近 5 条</span>
            </div>
          </template>
          <ElSkeleton :loading="loading" animated>
            <template #template>
              <div class="space-y-3">
                <div class="h-10 rounded-xl bg-slate-100" />
                <div class="h-10 rounded-xl bg-slate-100" />
                <div class="h-10 rounded-xl bg-slate-100" />
              </div>
            </template>
            <ElTable :data="overview.recent_users" empty-text="暂无用户数据" stripe>
              <ElTableColumn label="用户" min-width="180">
                <template #default="{ row }">
                  <div class="font-medium text-slate-900">
                    {{ row.nickname || '--' }}
                  </div>
                  <div class="text-xs text-slate-500">{{ row.user_id }}</div>
                </template>
              </ElTableColumn>
              <ElTableColumn label="城市 / 行业" min-width="180">
                <template #default="{ row }">
                  {{ row.city_name || '--' }} / {{ row.industry_label || '--' }}
                </template>
              </ElTableColumn>
              <ElTableColumn label="认证" width="90">
                <template #default="{ row }">
                  <ElTag :type="row.is_verified ? 'success' : 'info'">
                    {{ row.is_verified ? '已认证' : '未认证' }}
                  </ElTag>
                </template>
              </ElTableColumn>
              <ElTableColumn label="注册时间" min-width="160">
                <template #default="{ row }">
                  {{ formatDateTime(row.created_at) }}
                </template>
              </ElTableColumn>
            </ElTable>
          </ElSkeleton>
        </ElCard>
      </ElCol>

      <ElCol :lg="12" :xs="24" class="mb-4">
        <ElCard shadow="never" class="rounded-2xl border-0">
          <template #header>
            <div class="flex items-center justify-between">
              <span class="font-semibold text-slate-900">最近发布圈子</span>
              <span class="text-xs text-slate-400">最近 5 条</span>
            </div>
          </template>
          <ElTable :data="overview.recent_circles" empty-text="暂无圈子数据" stripe>
            <ElTableColumn label="圈子" min-width="180">
              <template #default="{ row }">
                <div class="font-medium text-slate-900">
                  {{ row.name || '--' }}
                </div>
                <div class="text-xs text-slate-500">{{ row.circle_code }}</div>
              </template>
            </ElTableColumn>
            <ElTableColumn label="圈主" min-width="140">
              <template #default="{ row }">
                {{ row.owner_nickname || '--' }} ({{ row.owner_user_id || '--' }})
              </template>
            </ElTableColumn>
            <ElTableColumn label="成员 / 动态" min-width="110">
              <template #default="{ row }">
                {{ row.member_count }} / {{ row.post_count }}
              </template>
            </ElTableColumn>
            <ElTableColumn label="状态" width="100">
              <template #default="{ row }">
                <ElTag :type="resolveStatusTagType(row.status)">
                  {{ row.status }}
                </ElTag>
              </template>
            </ElTableColumn>
          </ElTable>
        </ElCard>
      </ElCol>
    </ElRow>

    <ElRow :gutter="16">
      <ElCol :lg="12" :xs="24" class="mb-4">
        <ElCard shadow="never" class="rounded-2xl border-0">
          <template #header>
            <div class="flex items-center justify-between">
              <span class="font-semibold text-slate-900">最近资源发布</span>
              <span class="text-xs text-slate-400">最近 5 条</span>
            </div>
          </template>
          <ElTable :data="overview.recent_posts" empty-text="暂无资源数据" stripe>
            <ElTableColumn label="标题" min-width="220">
              <template #default="{ row }">
                <div class="font-medium text-slate-900">{{ row.title || '--' }}</div>
                <div class="text-xs text-slate-500">{{ row.post_code }}</div>
              </template>
            </ElTableColumn>
            <ElTableColumn label="类型" width="90">
              <template #default="{ row }">
                {{ formatPostMode(row.mode) }}
              </template>
            </ElTableColumn>
            <ElTableColumn label="作者" min-width="140">
              <template #default="{ row }">
                {{ row.author_nickname || '--' }}
              </template>
            </ElTableColumn>
            <ElTableColumn label="浏览 / 点赞" min-width="110">
              <template #default="{ row }">
                {{ row.view_count }} / {{ row.like_count }}
              </template>
            </ElTableColumn>
          </ElTable>
        </ElCard>
      </ElCol>

      <ElCol :lg="12" :xs="24" class="mb-4">
        <ElCard shadow="never" class="rounded-2xl border-0">
          <template #header>
            <div class="flex items-center justify-between">
              <span class="font-semibold text-slate-900">最近充值订单</span>
              <span class="text-xs text-slate-400">最近 5 条</span>
            </div>
          </template>
          <ElTable :data="overview.recent_recharges" empty-text="暂无充值订单" stripe>
            <ElTableColumn label="订单号" min-width="190" prop="order_no" />
            <ElTableColumn label="用户" min-width="150">
              <template #default="{ row }">
                {{ row.nickname || '--' }} ({{ row.user_id || '--' }})
              </template>
            </ElTableColumn>
            <ElTableColumn label="金额" width="90">
              <template #default="{ row }">
                {{ formatAmount(row.amount) }}
              </template>
            </ElTableColumn>
            <ElTableColumn label="状态" width="100">
              <template #default="{ row }">
                <ElTag :type="resolveStatusTagType(row.status)">
                  {{ row.status }}
                </ElTag>
              </template>
            </ElTableColumn>
            <ElTableColumn label="创建时间" min-width="160">
              <template #default="{ row }">
                {{ formatDateTime(row.created_at) }}
              </template>
            </ElTableColumn>
          </ElTable>
        </ElCard>
      </ElCol>
    </ElRow>
  </div>
</template>
