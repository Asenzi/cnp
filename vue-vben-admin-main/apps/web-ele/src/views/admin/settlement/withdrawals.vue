<script setup lang="ts">
import type { AdminWithdrawalItem, PageResult } from '#/api/admin';

import { onMounted, reactive, ref } from 'vue';

import {
  ElButton,
  ElCard,
  ElForm,
  ElFormItem,
  ElInput,
  ElMessage,
  ElMessageBox,
  ElOption,
  ElPagination,
  ElSelect,
  ElTable,
  ElTableColumn,
  ElTag,
} from 'element-plus';

import {
  listAdminWithdrawalsApi,
  reviewAdminWithdrawalApi,
} from '#/api/admin';
import { formatAmount, formatDateTime, resolveStatusTagType } from '#/utils/admin';

defineOptions({ name: 'AdminWithdrawalsPage' });

const loading = ref(false);
const filters = reactive({
  keyword: '',
  page: 1,
  page_size: 12,
  status: '',
});
const pageData = ref<PageResult<AdminWithdrawalItem>>({
  items: [],
  page: 1,
  page_size: 12,
  total: 0,
});

async function loadWithdrawals(page = filters.page) {
  filters.page = page;
  loading.value = true;
  try {
    pageData.value = await listAdminWithdrawalsApi({
      keyword: filters.keyword.trim() || undefined,
      page: filters.page,
      page_size: filters.page_size,
      status: filters.status || undefined,
    });
  } finally {
    loading.value = false;
  }
}

async function approveWithdrawal(row: AdminWithdrawalItem) {
  const { value } = await ElMessageBox.prompt(
    '确认已完成线下/商户打款后再通过。可填写第三方流水号。',
    '确认提现成功',
    {
      confirmButtonText: '确认已打款',
      cancelButtonText: '取消',
      inputPlaceholder: '打款流水号，可留空',
    },
  );
  loading.value = true;
  try {
    await reviewAdminWithdrawalApi(Number(row.id), {
      action: 'approve',
      transaction_id: String(value || '').trim() || undefined,
    });
    ElMessage.success('提现已确认成功');
    await loadWithdrawals(filters.page);
  } finally {
    loading.value = false;
  }
}

async function rejectWithdrawal(row: AdminWithdrawalItem) {
  const { value } = await ElMessageBox.prompt('请填写驳回原因，金额会退回用户可提现余额。', '驳回提现', {
    confirmButtonText: '确认驳回',
    cancelButtonText: '取消',
    inputPlaceholder: '驳回原因',
  });
  loading.value = true;
  try {
    await reviewAdminWithdrawalApi(Number(row.id), {
      action: 'reject',
      remark: String(value || '').trim() || undefined,
    });
    ElMessage.success('提现已驳回');
    await loadWithdrawals(filters.page);
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  void loadWithdrawals();
});
</script>

<template>
  <div class="space-y-4 p-5">
    <div class="space-y-1">
      <h1 class="text-2xl font-semibold text-slate-900">提现审核</h1>
      <p class="text-sm text-slate-500">
        用户提交提现后先冻结余额，后台确认打款成功或驳回退回余额。
      </p>
    </div>

    <ElCard shadow="never" class="rounded-2xl border-0">
      <ElForm inline class="flex flex-wrap gap-x-4">
        <ElFormItem label="关键词">
          <ElInput
            v-model="filters.keyword"
            clearable
            placeholder="搜索订单号 / 用户 / 手机"
            style="width: 320px"
            @keyup.enter="loadWithdrawals(1)"
          />
        </ElFormItem>
        <ElFormItem label="状态">
          <ElSelect v-model="filters.status" clearable style="width: 160px">
            <ElOption label="全部" value="" />
            <ElOption label="待处理" value="pending" />
            <ElOption label="成功" value="success" />
            <ElOption label="失败/驳回" value="failed" />
          </ElSelect>
        </ElFormItem>
        <ElFormItem>
          <ElButton type="primary" @click="loadWithdrawals(1)">查询</ElButton>
        </ElFormItem>
      </ElForm>
    </ElCard>

    <ElCard shadow="never" class="rounded-2xl border-0">
      <ElTable
        v-loading="loading"
        :data="pageData.items"
        empty-text="暂无提现申请"
        row-key="id"
        stripe
      >
        <ElTableColumn label="提现单号" min-width="180" prop="order_no" />
        <ElTableColumn label="用户" min-width="160">
          <template #default="{ row }">
            {{ row.nickname || '--' }} ({{ row.user_id || '--' }})
          </template>
        </ElTableColumn>
        <ElTableColumn label="手机号" min-width="130" prop="phone" />
        <ElTableColumn label="金额" width="110">
          <template #default="{ row }">¥{{ formatAmount(row.amount) }}</template>
        </ElTableColumn>
        <ElTableColumn label="到账" width="110">
          <template #default="{ row }">¥{{ formatAmount(row.actual_amount) }}</template>
        </ElTableColumn>
        <ElTableColumn label="方式" width="100" prop="withdraw_type" />
        <ElTableColumn label="状态" width="110">
          <template #default="{ row }">
            <ElTag :type="resolveStatusTagType(row.status)">
              {{ row.status }}
            </ElTag>
          </template>
        </ElTableColumn>
        <ElTableColumn label="流水号" min-width="160" prop="transaction_id" />
        <ElTableColumn label="备注" min-width="220" prop="remark" />
        <ElTableColumn label="申请时间" min-width="150">
          <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
        </ElTableColumn>
        <ElTableColumn label="处理时间" min-width="150">
          <template #default="{ row }">{{ formatDateTime(row.processed_at) }}</template>
        </ElTableColumn>
        <ElTableColumn fixed="right" label="操作" width="150">
          <template #default="{ row }">
            <div v-if="row.status === 'pending'" class="flex gap-2">
              <ElButton link type="primary" @click="approveWithdrawal(row)">通过</ElButton>
              <ElButton link type="danger" @click="rejectWithdrawal(row)">驳回</ElButton>
            </div>
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
          @current-change="loadWithdrawals"
        />
      </div>
    </ElCard>
  </div>
</template>
