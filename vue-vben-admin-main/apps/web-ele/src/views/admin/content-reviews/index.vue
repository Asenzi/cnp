<script setup lang="ts">
import type { AdminContentReviewItem, PageResult } from '#/api/admin';

import { computed, onMounted, reactive, ref } from 'vue';
import { useRoute } from 'vue-router';

import {
  ElButton,
  ElCard,
  ElDescriptions,
  ElDescriptionsItem,
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
  listAdminContentReviewsApi,
  reviewAdminContentReviewApi,
} from '#/api/admin';
import {
  formatAmount,
  formatContentReviewType,
  formatDateTime,
  formatReviewActionType,
  formatReviewTriggerReason,
  resolveStatusTagType,
} from '#/utils/admin';

defineOptions({ name: 'AdminContentReviewsPage' });

const route = useRoute();
const reviewType = computed(() => String(route.meta.reviewType || 'profile'));
const pageTitle = computed(() => String(route.meta.title || '内容审核'));
const pageDescriptionMap: Record<string, string> = {
  circle: '处理圈主修改圈子资料后触发的系统风控和人工复核。',
  post: '处理系统命中风险词的资源发帖与资源修改申请。',
  profile: '处理用户修改个人资料后触发的系统风控和人工复核。',
};

const loading = ref(false);
const submitLoading = ref(false);
const filters = reactive({
  page: 1,
  page_size: 12,
  status: 'pending',
});
const pageData = ref<PageResult<AdminContentReviewItem>>({
  items: [],
  page: 1,
  page_size: 12,
  total: 0,
});
const dialogVisible = ref(false);
const reviewAction = ref<'approve' | 'reject'>('approve');
const reviewItem = ref<AdminContentReviewItem | null>(null);
const rejectReason = ref('');

const submitPayloadText = computed(() => {
  try {
    return JSON.stringify(reviewItem.value?.submit_payload || {}, null, 2);
  } catch {
    return '{}';
  }
});

const currentPayloadText = computed(() => {
  try {
    return JSON.stringify(reviewItem.value?.current_payload || {}, null, 2);
  } catch {
    return '{}';
  }
});

async function loadReviews(page = filters.page) {
  filters.page = page;
  loading.value = true;
  try {
    pageData.value = await listAdminContentReviewsApi({
      page: filters.page,
      page_size: filters.page_size,
      review_type: reviewType.value,
      status: filters.status || undefined,
    });
  } catch (error: any) {
    ElMessage.error(error?.message || '加载审核列表失败');
    pageData.value = {
      items: [],
      page: filters.page,
      page_size: filters.page_size,
      total: 0,
    };
  } finally {
    loading.value = false;
  }
}

function openReviewDialog(
  item: AdminContentReviewItem,
  action: 'approve' | 'reject',
) {
  reviewAction.value = action;
  reviewItem.value = item;
  rejectReason.value = '';
  dialogVisible.value = true;
}

function closeReviewDialog() {
  dialogVisible.value = false;
  reviewItem.value = null;
  reviewAction.value = 'approve';
  rejectReason.value = '';
}

async function submitReview() {
  if (!reviewItem.value) {
    return;
  }
  if (reviewAction.value === 'reject' && !rejectReason.value.trim()) {
    ElMessage.error('请输入驳回原因');
    return;
  }
  submitLoading.value = true;
  try {
    await reviewAdminContentReviewApi(reviewItem.value.id, {
      action: reviewAction.value,
      reject_reason:
        reviewAction.value === 'reject' ? rejectReason.value.trim() : '',
    });
    ElMessage.success(
      reviewAction.value === 'approve' ? '审核已通过' : '审核已驳回',
    );
    closeReviewDialog();
    await loadReviews(filters.page);
  } catch (error: any) {
    ElMessage.error(error?.message || '审核提交失败');
  } finally {
    submitLoading.value = false;
  }
}

onMounted(() => {
  void loadReviews();
});
</script>

<template>
  <div class="space-y-4 p-5">
    <div class="space-y-1">
      <h1 class="text-2xl font-semibold text-slate-900">{{ pageTitle }}</h1>
      <p class="text-sm text-slate-500">
        {{ pageDescriptionMap[reviewType] || '处理系统识别后需要人工确认的内容申请。' }}
      </p>
    </div>

    <ElCard shadow="never" class="rounded-2xl border-0">
      <ElForm inline class="flex flex-wrap gap-x-4">
        <ElFormItem label="状态">
          <ElSelect v-model="filters.status" clearable style="width: 180px">
            <ElOption label="全部" value="" />
            <ElOption label="pending" value="pending" />
            <ElOption label="approved" value="approved" />
            <ElOption label="rejected" value="rejected" />
            <ElOption label="auto_approved" value="auto_approved" />
          </ElSelect>
        </ElFormItem>
        <ElFormItem>
          <ElButton type="primary" @click="loadReviews(1)">查询</ElButton>
        </ElFormItem>
      </ElForm>
    </ElCard>

    <ElCard shadow="never" class="rounded-2xl border-0">
      <ElTable
        v-loading="loading"
        :data="pageData.items"
        empty-text="暂无审核数据"
        row-key="id"
        stripe
      >
        <ElTableColumn label="记录ID" min-width="100" prop="id" />
        <ElTableColumn label="提交人" min-width="180">
          <template #default="{ row }">
            {{ row.submitter_nickname || '--' }} ({{ row.submitter_user_id || '--' }})
          </template>
        </ElTableColumn>
        <ElTableColumn label="目标" min-width="200">
          <template #default="{ row }">
            {{ row.target_label || '--' }}
          </template>
        </ElTableColumn>
        <ElTableColumn label="动作" width="90">
          <template #default="{ row }">
            {{ formatReviewActionType(row.action_type) }}
          </template>
        </ElTableColumn>
        <ElTableColumn label="状态" width="120">
          <template #default="{ row }">
            <ElTag :type="resolveStatusTagType(row.status)">
              {{ row.status }}
            </ElTag>
          </template>
        </ElTableColumn>
        <ElTableColumn label="触发原因" min-width="150">
          <template #default="{ row }">
            {{ formatReviewTriggerReason(row.trigger_reason) }}
          </template>
        </ElTableColumn>
        <ElTableColumn label="审核费" width="110">
          <template #default="{ row }">
            {{ row.fee_paid ? formatAmount(row.review_fee_amount) : '--' }}
          </template>
        </ElTableColumn>
        <ElTableColumn label="提交时间" min-width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </ElTableColumn>
        <ElTableColumn label="审核时间" min-width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.reviewed_at) }}
          </template>
        </ElTableColumn>
        <ElTableColumn fixed="right" label="操作" width="170">
          <template #default="{ row }">
            <div v-if="row.status === 'pending'" class="flex items-center gap-3">
              <ElButton
                link
                type="primary"
                @click="openReviewDialog(row, 'approve')"
              >
                通过
              </ElButton>
              <ElButton
                link
                type="danger"
                @click="openReviewDialog(row, 'reject')"
              >
                驳回
              </ElButton>
            </div>
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
          @current-change="loadReviews"
        />
      </div>
    </ElCard>

    <ElDialog
      v-model="dialogVisible"
      :title="reviewAction === 'approve' ? '通过审核' : '驳回审核'"
      destroy-on-close
      width="820px"
      @closed="closeReviewDialog"
    >
      <div class="space-y-4">
        <ElDescriptions :column="2" border>
          <ElDescriptionsItem label="审核类型">
            {{ formatContentReviewType(reviewItem?.review_type) }}
          </ElDescriptionsItem>
          <ElDescriptionsItem label="动作">
            {{ formatReviewActionType(reviewItem?.action_type) }}
          </ElDescriptionsItem>
          <ElDescriptionsItem label="提交人">
            {{ reviewItem?.submitter_nickname || '--' }} ({{ reviewItem?.submitter_user_id || '--' }})
          </ElDescriptionsItem>
          <ElDescriptionsItem label="目标">
            {{ reviewItem?.target_label || '--' }}
          </ElDescriptionsItem>
          <ElDescriptionsItem label="状态">
            <ElTag :type="resolveStatusTagType(reviewItem?.status)">
              {{ reviewItem?.status || '--' }}
            </ElTag>
          </ElDescriptionsItem>
          <ElDescriptionsItem label="触发原因">
            {{ formatReviewTriggerReason(reviewItem?.trigger_reason) }}
          </ElDescriptionsItem>
          <ElDescriptionsItem label="风险标签" :span="2">
            <div class="flex flex-wrap gap-2">
              <ElTag
                v-for="tag in reviewItem?.risk_tags || []"
                :key="tag"
                type="warning"
              >
                {{ tag }}
              </ElTag>
              <span v-if="!(reviewItem?.risk_tags || []).length" class="text-slate-400">--</span>
            </div>
          </ElDescriptionsItem>
        </ElDescriptions>

        <div class="space-y-2">
          <div class="text-sm font-medium text-slate-700">当前内容</div>
          <pre class="max-h-56 overflow-auto rounded-2xl bg-slate-950 p-4 text-xs text-slate-100">{{ currentPayloadText }}</pre>
        </div>

        <div class="space-y-2">
          <div class="text-sm font-medium text-slate-700">提交内容</div>
          <pre class="max-h-56 overflow-auto rounded-2xl bg-slate-950 p-4 text-xs text-slate-100">{{ submitPayloadText }}</pre>
        </div>

        <div v-if="reviewAction === 'reject'" class="space-y-2">
          <div class="text-sm font-medium text-slate-700">驳回原因</div>
          <ElInput
            v-model="rejectReason"
            :rows="4"
            maxlength="255"
            placeholder="请输入驳回原因"
            show-word-limit
            type="textarea"
          />
        </div>
      </div>

      <template #footer>
        <div class="flex justify-end gap-3">
          <ElButton @click="closeReviewDialog">取消</ElButton>
          <ElButton :loading="submitLoading" type="primary" @click="submitReview">
            {{ reviewAction === 'approve' ? '确认通过' : '确认驳回' }}
          </ElButton>
        </div>
      </template>
    </ElDialog>
  </div>
</template>
