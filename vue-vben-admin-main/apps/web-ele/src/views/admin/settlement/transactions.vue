<script setup lang="ts">
import type { AdminSplitTransactionItem, PageResult } from '#/api/admin';

import { onMounted, reactive, ref } from 'vue';

import {
  ElButton,
  ElCard,
  ElForm,
  ElFormItem,
  ElInput,
  ElMessage,
  ElOption,
  ElPagination,
  ElSelect,
  ElTable,
  ElTableColumn,
  ElTag,
} from 'element-plus';

import {
  listAdminSplitTransactionsApi,
  retryAdminSplitTransactionApi,
} from '#/api/admin';
import { formatAmount, formatDateTime, resolveStatusTagType } from '#/utils/admin';

defineOptions({ name: 'AdminSplitTransactionsPage' });

const loading = ref(false);
const filters = reactive({
  keyword: '',
  page: 1,
  page_size: 12,
  status: '',
});
const pageData = ref<PageResult<AdminSplitTransactionItem>>({
  items: [],
  page: 1,
  page_size: 12,
  total: 0,
});

async function loadTransactions(page = filters.page) {
  filters.page = page;
  loading.value = true;
  try {
    pageData.value = await listAdminSplitTransactionsApi({
      keyword: filters.keyword.trim() || undefined,
      page: filters.page,
      page_size: filters.page_size,
      status: filters.status || undefined,
    });
  } finally {
    loading.value = false;
  }
}

function canRetry(row: AdminSplitTransactionItem) {
  return ['external_failed', 'pending', 'ready'].includes(String(row.split_status || ''));
}

async function retrySplit(row: AdminSplitTransactionItem) {
  loading.value = true;
  try {
    await retryAdminSplitTransactionApi(Number(row.id));
    ElMessage.success('分账重试已发起');
    await loadTransactions(filters.page);
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  void loadTransactions();
});
</script>

<template>
  <div class="space-y-4 p-5">
    <div class="space-y-1">
      <h1 class="text-2xl font-semibold text-slate-900">分账订单</h1>
      <p class="text-sm text-slate-500">
        查看付费入圈订单的技术服务费、圈主分账金额和结算状态。
      </p>
    </div>

    <ElCard shadow="never" class="rounded-2xl border-0">
      <ElForm inline class="flex flex-wrap gap-x-4">
        <ElFormItem label="关键词">
          <ElInput
            v-model="filters.keyword"
            clearable
            placeholder="搜索订单号 / 用户 / 圈主"
            style="width: 320px"
            @keyup.enter="loadTransactions(1)"
          />
        </ElFormItem>
        <ElFormItem label="状态">
          <ElSelect v-model="filters.status" clearable style="width: 160px">
            <ElOption label="全部" value="" />
            <ElOption label="pending" value="pending" />
            <ElOption label="ready" value="ready" />
            <ElOption label="success" value="success" />
            <ElOption label="cancelled" value="cancelled" />
            <ElOption label="returned" value="returned" />
          </ElSelect>
        </ElFormItem>
        <ElFormItem>
          <ElButton type="primary" @click="loadTransactions(1)">查询</ElButton>
        </ElFormItem>
      </ElForm>
    </ElCard>

    <ElCard shadow="never" class="rounded-2xl border-0">
      <ElTable
        v-loading="loading"
        :data="pageData.items"
        empty-text="暂无分账订单"
        row-key="id"
        stripe
      >
        <ElTableColumn label="订单号" min-width="180" prop="order_no" />
        <ElTableColumn label="圈子" min-width="180">
          <template #default="{ row }">
            <div>{{ row.circle_name || '--' }}</div>
            <div class="text-xs text-slate-400">{{ row.circle_code || '--' }}</div>
          </template>
        </ElTableColumn>
        <ElTableColumn label="付款用户" min-width="150">
          <template #default="{ row }">
            {{ row.payer_nickname || '--' }} ({{ row.payer_user_id || '--' }})
          </template>
        </ElTableColumn>
        <ElTableColumn label="圈主" min-width="150">
          <template #default="{ row }">
            {{ row.receiver_nickname || '--' }} ({{ row.receiver_user_id || '--' }})
          </template>
        </ElTableColumn>
        <ElTableColumn label="订单金额" width="110">
          <template #default="{ row }">¥{{ formatAmount(row.total_amount) }}</template>
        </ElTableColumn>
        <ElTableColumn label="服务费" width="110">
          <template #default="{ row }">¥{{ formatAmount(row.platform_fee) }}</template>
        </ElTableColumn>
        <ElTableColumn label="圈主收益" width="120">
          <template #default="{ row }">¥{{ formatAmount(row.split_amount) }}</template>
        </ElTableColumn>
        <ElTableColumn label="状态" width="110">
          <template #default="{ row }">
            <ElTag :type="resolveStatusTagType(row.split_status)">
              {{ row.split_status }}
            </ElTag>
          </template>
        </ElTableColumn>
        <ElTableColumn label="微信分账" min-width="180">
          <template #default="{ row }">
            <div>{{ row.external_status || '--' }}</div>
            <div class="text-xs text-slate-400">{{ row.external_order_no || '--' }}</div>
          </template>
        </ElTableColumn>
        <ElTableColumn label="失败原因" min-width="220">
          <template #default="{ row }">
            <span class="text-xs text-slate-500">{{ row.external_error || '--' }}</span>
          </template>
        </ElTableColumn>
        <ElTableColumn label="结算时间" min-width="150">
          <template #default="{ row }">{{ formatDateTime(row.executed_at) }}</template>
        </ElTableColumn>
        <ElTableColumn label="创建时间" min-width="150">
          <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
        </ElTableColumn>
        <ElTableColumn fixed="right" label="操作" width="110">
          <template #default="{ row }">
            <ElButton
              v-if="canRetry(row)"
              link
              type="primary"
              @click="retrySplit(row)"
            >
              重试
            </ElButton>
            <span v-else class="text-xs text-slate-400">--</span>
          </template>
        </ElTableColumn>
      </ElTable>

      <div class="mt-4 flex justify-end">
        <ElPagination
          :current-page="pageData.page"
          :page-size="pageData.page_size"
          :total="pageData.total"
          background
          layout="total, prev, pager, next"
          @current-change="loadTransactions"
        />
      </div>
    </ElCard>
  </div>
</template>
