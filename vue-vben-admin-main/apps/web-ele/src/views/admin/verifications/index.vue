<script setup lang="ts">
import type { AdminVerificationItem, PageResult } from '#/api/admin';

import { useAppConfig } from '@vben/hooks';
import { computed, onMounted, reactive, ref } from 'vue';
import { useAccessStore } from '@vben/stores';

import {
  ElButton,
  ElCard,
  ElDescriptions,
  ElDescriptionsItem,
  ElDialog,
  ElForm,
  ElFormItem,
  ElImage,
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
  listAdminVerificationsApi,
  reviewAdminVerificationApi,
} from '#/api/admin';
import {
  formatDateTime,
  formatVerificationType,
  resolveStatusTagType,
} from '#/utils/admin';

defineOptions({ name: 'AdminVerificationsPage' });

const { apiURL } = useAppConfig(import.meta.env, import.meta.env.PROD);
const accessStore = useAccessStore();

const loading = ref(false);
const submitLoading = ref(false);
const filters = reactive({
  page: 1,
  page_size: 12,
  status: 'pending',
  verify_type: '',
});
const pageData = ref<PageResult<AdminVerificationItem>>({
  items: [],
  page: 1,
  page_size: 12,
  total: 0,
});
const dialogVisible = ref(false);
const reviewAction = ref<'approve' | 'reject'>('approve');
const reviewItem = ref<AdminVerificationItem | null>(null);
const rejectReason = ref('');

const payloadText = computed(() => {
  try {
    return JSON.stringify(reviewItem.value?.submit_payload || {}, null, 2);
  } catch {
    return '{}';
  }
});

const realNameProfile = computed(() => reviewItem.value?.real_name_profile || null);
const isRealNameReview = computed(() => reviewItem.value?.type === 'real_name');

function resolvePreviewUrl(side: 'back' | 'front') {
  const verificationId = Number(reviewItem.value?.id || 0);
  const token = String(accessStore.accessToken || '').trim();
  if (!verificationId || !token) {
    return '';
  }
  const baseUrl = String(apiURL || '').replace(/\/$/, '');
  return `${baseUrl}/api/v1/admin/verifications/${verificationId}/real-name-files/${side}?access_token=${encodeURIComponent(token)}`;
}

async function loadVerifications(page = filters.page) {
  filters.page = page;
  loading.value = true;
  try {
    pageData.value = await listAdminVerificationsApi({
      page: filters.page,
      page_size: filters.page_size,
      status: filters.status || undefined,
      verify_type: filters.verify_type || undefined,
    });
  } finally {
    loading.value = false;
  }
}

function openReviewDialog(
  item: AdminVerificationItem,
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
    await reviewAdminVerificationApi(reviewItem.value.id, {
      action: reviewAction.value,
      reject_reason:
        reviewAction.value === 'reject' ? rejectReason.value.trim() : '',
    });
    ElMessage.success(
      reviewAction.value === 'approve' ? '认证已通过' : '认证已驳回',
    );
    closeReviewDialog();
    await loadVerifications(filters.page);
  } finally {
    submitLoading.value = false;
  }
}

onMounted(() => {
  void loadVerifications();
});
</script>

<template>
  <div class="space-y-4 p-5">
    <div class="space-y-1">
      <h1 class="text-2xl font-semibold text-slate-900">认证审核</h1>
      <p class="text-sm text-slate-500">
        集中处理实名认证、企业认证和名片认证申请。
      </p>
    </div>

    <ElCard shadow="never" class="rounded-2xl border-0">
      <ElForm inline class="flex flex-wrap gap-x-4">
        <ElFormItem label="状态">
          <ElSelect v-model="filters.status" clearable style="width: 160px">
            <ElOption label="全部" value="" />
            <ElOption label="pending" value="pending" />
            <ElOption label="approved" value="approved" />
            <ElOption label="rejected" value="rejected" />
          </ElSelect>
        </ElFormItem>
        <ElFormItem label="类型">
          <ElSelect v-model="filters.verify_type" clearable style="width: 180px">
            <ElOption label="全部" value="" />
            <ElOption label="实名认证" value="real_name" />
            <ElOption label="企业认证" value="enterprise" />
            <ElOption label="名片认证" value="business_card" />
          </ElSelect>
        </ElFormItem>
        <ElFormItem>
          <ElButton type="primary" @click="loadVerifications(1)">
            查询
          </ElButton>
        </ElFormItem>
      </ElForm>
    </ElCard>

    <ElCard shadow="never" class="rounded-2xl border-0">
      <ElTable
        v-loading="loading"
        :data="pageData.items"
        empty-text="暂无认证数据"
        row-key="id"
        stripe
      >
        <ElTableColumn label="记录ID" min-width="100" prop="id" />
        <ElTableColumn label="用户" min-width="200">
          <template #default="{ row }">
            {{ row.nickname || '--' }} ({{ row.user_id || '--' }})
          </template>
        </ElTableColumn>
        <ElTableColumn label="手机号" min-width="140" prop="phone" />
        <ElTableColumn label="实名信息" min-width="220">
          <template #default="{ row }">
            <template v-if="row.real_name_profile">
              {{ row.real_name_profile.real_name || '--' }}
              <span class="text-slate-400"> / </span>
              {{ row.real_name_profile.id_number_masked || '--' }}
            </template>
            <template v-else>
              --
            </template>
          </template>
        </ElTableColumn>
        <ElTableColumn label="类型" min-width="120">
          <template #default="{ row }">
            {{ formatVerificationType(row.type) }}
          </template>
        </ElTableColumn>
        <ElTableColumn label="状态" width="100">
          <template #default="{ row }">
            <ElTag :type="resolveStatusTagType(row.status)">
              {{ row.status }}
            </ElTag>
          </template>
        </ElTableColumn>
        <ElTableColumn label="提交时间" min-width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.submitted_at) }}
          </template>
        </ElTableColumn>
        <ElTableColumn label="审核时间" min-width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.reviewed_at) }}
          </template>
        </ElTableColumn>
        <ElTableColumn fixed="right" label="操作" width="150">
          <template #default="{ row }">
            <div class="flex items-center gap-3">
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
          @current-change="loadVerifications"
        />
      </div>
    </ElCard>

    <ElDialog
      v-model="dialogVisible"
      :title="reviewAction === 'approve' ? '通过认证' : '驳回认证'"
      destroy-on-close
      width="760px"
      @closed="closeReviewDialog"
    >
      <div class="space-y-4">
        <ElDescriptions :column="2" border>
          <ElDescriptionsItem label="认证记录">
            {{ reviewItem?.id || '--' }}
          </ElDescriptionsItem>
          <ElDescriptionsItem label="用户">
            {{ reviewItem?.nickname || '--' }} ({{ reviewItem?.user_id || '--' }})
          </ElDescriptionsItem>
          <ElDescriptionsItem label="手机号">
            {{ reviewItem?.phone || '--' }}
          </ElDescriptionsItem>
          <ElDescriptionsItem label="类型">
            {{ formatVerificationType(reviewItem?.type) }}
          </ElDescriptionsItem>
          <ElDescriptionsItem label="状态">
            <ElTag :type="resolveStatusTagType(reviewItem?.status)">
              {{ reviewItem?.status || '--' }}
            </ElTag>
          </ElDescriptionsItem>
          <ElDescriptionsItem label="驳回原因">
            {{ reviewItem?.reject_reason || '--' }}
          </ElDescriptionsItem>
        </ElDescriptions>

        <template v-if="isRealNameReview && realNameProfile">
          <ElDescriptions :column="2" border>
            <ElDescriptionsItem label="真实姓名">
              {{ realNameProfile.real_name || '--' }}
            </ElDescriptionsItem>
            <ElDescriptionsItem label="身份证号">
              {{ realNameProfile.id_number_masked || '--' }}
            </ElDescriptionsItem>
            <ElDescriptionsItem label="提交时间">
              {{ formatDateTime(realNameProfile.submitted_at) }}
            </ElDescriptionsItem>
            <ElDescriptionsItem label="认证时间">
              {{ formatDateTime(realNameProfile.verified_at) }}
            </ElDescriptionsItem>
          </ElDescriptions>

          <div class="grid grid-cols-2 gap-4">
            <div class="space-y-2">
              <div class="text-sm font-medium text-slate-700">身份证人像面</div>
              <ElImage
                v-if="realNameProfile?.id_front_url"
                :preview-src-list="[resolvePreviewUrl('front')]"
                :src="resolvePreviewUrl('front')"
                fit="cover"
                style="width: 100%; border-radius: 16px"
              />
              <div v-else class="rounded-2xl bg-slate-100 p-6 text-sm text-slate-500">
                未上传
              </div>
            </div>
            <div class="space-y-2">
              <div class="text-sm font-medium text-slate-700">身份证国徽面</div>
              <ElImage
                v-if="realNameProfile?.id_back_url"
                :preview-src-list="[resolvePreviewUrl('back')]"
                :src="resolvePreviewUrl('back')"
                fit="cover"
                style="width: 100%; border-radius: 16px"
              />
              <div v-else class="rounded-2xl bg-slate-100 p-6 text-sm text-slate-500">
                未上传
              </div>
            </div>
          </div>
        </template>

        <div class="space-y-2">
          <div class="text-sm font-medium text-slate-700">提交内容</div>
          <pre class="max-h-80 overflow-auto rounded-2xl bg-slate-950 p-4 text-xs text-slate-100">{{ payloadText }}</pre>
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
