<script setup lang="ts">
import type {
  AdminCircleOwnerApplicationItem,
  PageResult,
} from '#/api/admin';

import { onMounted, reactive, ref } from 'vue';

import {
  ElButton,
  ElCard,
  ElDialog,
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
  listAdminCircleOwnerApplicationsApi,
  reviewAdminCircleOwnerApplicationApi,
} from '#/api/admin';
import { formatDateTime, resolveStatusTagType } from '#/utils/admin';

defineOptions({ name: 'AdminCircleOwnerApplicationsPage' });

const loading = ref(false);
const submitLoading = ref(false);
const dialogVisible = ref(false);
const reviewAction = ref<'approve' | 'reject'>('approve');
const reviewItem = ref<AdminCircleOwnerApplicationItem | null>(null);
const rejectReason = ref('');
const filters = reactive({
  page: 1,
  page_size: 12,
  status: 'pending',
});
const pageData = ref<PageResult<AdminCircleOwnerApplicationItem>>({
  items: [],
  page: 1,
  page_size: 12,
  total: 0,
});

async function loadApplications(page = filters.page) {
  filters.page = page;
  loading.value = true;
  try {
    pageData.value = await listAdminCircleOwnerApplicationsApi({
      page: filters.page,
      page_size: filters.page_size,
      status: filters.status || undefined,
    });
  } finally {
    loading.value = false;
  }
}

function openReview(
  item: AdminCircleOwnerApplicationItem,
  action: 'approve' | 'reject',
) {
  reviewItem.value = item;
  reviewAction.value = action;
  rejectReason.value = '';
  dialogVisible.value = true;
}

async function submitReview() {
  if (!reviewItem.value) return;
  if (reviewAction.value === 'reject' && !rejectReason.value.trim()) {
    ElMessage.error('请输入驳回原因');
    return;
  }

  submitLoading.value = true;
  try {
    await reviewAdminCircleOwnerApplicationApi(reviewItem.value.id, {
      action: reviewAction.value,
      reject_reason:
        reviewAction.value === 'reject' ? rejectReason.value.trim() : '',
    });
    ElMessage.success(reviewAction.value === 'approve' ? '已通过申请' : '已驳回申请');
    dialogVisible.value = false;
    await loadApplications(filters.page);
  } finally {
    submitLoading.value = false;
  }
}

onMounted(() => {
  void loadApplications();
});
</script>

<template>
  <div class="space-y-4 p-5">
    <div class="space-y-1">
      <h1 class="text-2xl font-semibold text-slate-900">圈主申请</h1>
      <p class="text-sm text-slate-500">
        审核年度会员提交的圈主资格申请，通过后用户才可创建圈子。
      </p>
    </div>

    <ElCard shadow="never" class="rounded-2xl border-0">
      <ElForm inline>
        <ElFormItem label="状态">
          <ElSelect v-model="filters.status" clearable style="width: 180px">
            <ElOption label="全部" value="" />
            <ElOption label="待审核" value="pending" />
            <ElOption label="已通过" value="approved" />
            <ElOption label="已驳回" value="rejected" />
          </ElSelect>
        </ElFormItem>
        <ElFormItem>
          <ElButton type="primary" @click="loadApplications(1)">查询</ElButton>
        </ElFormItem>
      </ElForm>
    </ElCard>

    <ElCard shadow="never" class="rounded-2xl border-0">
      <ElTable
        v-loading="loading"
        :data="pageData.items"
        empty-text="暂无圈主申请"
        row-key="id"
        stripe
      >
        <ElTableColumn label="用户" min-width="190">
          <template #default="{ row }">
            {{ row.nickname || '--' }} ({{ row.user_id || '--' }})
          </template>
        </ElTableColumn>
        <ElTableColumn label="申请理由" min-width="300" prop="reason" show-overflow-tooltip />
        <ElTableColumn label="相关经验" min-width="260" prop="experience" show-overflow-tooltip />
        <ElTableColumn label="状态" width="110">
          <template #default="{ row }">
            <ElTag :type="resolveStatusTagType(row.status)">
              {{ row.status }}
            </ElTag>
          </template>
        </ElTableColumn>
        <ElTableColumn label="提交时间" min-width="170">
          <template #default="{ row }">
            {{ formatDateTime(row.submitted_at) }}
          </template>
        </ElTableColumn>
        <ElTableColumn fixed="right" label="操作" width="150">
          <template #default="{ row }">
            <template v-if="row.status === 'pending'">
              <ElButton link type="primary" @click="openReview(row, 'approve')">
                通过
              </ElButton>
              <ElButton link type="danger" @click="openReview(row, 'reject')">
                驳回
              </ElButton>
            </template>
            <span v-else class="text-slate-400">已处理</span>
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
          @current-change="loadApplications"
        />
      </div>
    </ElCard>

    <ElDialog
      v-model="dialogVisible"
      :title="reviewAction === 'approve' ? '通过圈主申请' : '驳回圈主申请'"
      width="620px"
    >
      <div class="space-y-4">
        <div>
          <div class="text-sm text-slate-500">申请用户</div>
          <div class="mt-1 text-base text-slate-900">
            {{ reviewItem?.nickname || '--' }} ({{ reviewItem?.user_id || '--' }})
          </div>
        </div>
        <div>
          <div class="text-sm text-slate-500">申请理由</div>
          <div class="mt-1 whitespace-pre-wrap text-sm text-slate-800">
            {{ reviewItem?.reason || '--' }}
          </div>
        </div>
        <ElInput
          v-if="reviewAction === 'reject'"
          v-model="rejectReason"
          :rows="4"
          maxlength="500"
          placeholder="请输入驳回原因"
          show-word-limit
          type="textarea"
        />
      </div>

      <template #footer>
        <ElButton @click="dialogVisible = false">取消</ElButton>
        <ElButton
          :loading="submitLoading"
          :type="reviewAction === 'approve' ? 'primary' : 'danger'"
          @click="submitReview"
        >
          确认{{ reviewAction === 'approve' ? '通过' : '驳回' }}
        </ElButton>
      </template>
    </ElDialog>
  </div>
</template>
