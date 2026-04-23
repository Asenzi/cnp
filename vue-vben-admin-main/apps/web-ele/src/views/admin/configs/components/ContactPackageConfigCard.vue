<script setup lang="ts">
import type {
  AdminContactPackageConfig,
  AdminContactPackagePlanItem,
} from '#/api/admin';

import { onMounted, reactive, ref } from 'vue';

import {
  ElButton,
  ElCard,
  ElEmpty,
  ElForm,
  ElFormItem,
  ElInput,
  ElInputNumber,
  ElMessage,
  ElSwitch,
} from 'element-plus';

import {
  getAdminContactPackageConfigApi,
  saveAdminContactPackageConfigApi,
} from '#/api/admin';

defineOptions({ name: 'ContactPackageConfigCard' });

interface EditableContactPackagePlanItem extends AdminContactPackagePlanItem {
  _localId: string;
}

const loading = ref(false);
const saving = ref(false);
const formState = reactive<{
  display_enabled: boolean;
  plans: EditableContactPackagePlanItem[];
}>({
  display_enabled: false,
  plans: [],
});

function createLocalId() {
  return `contact-package-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

function createEditablePlan(
  plan?: Partial<AdminContactPackagePlanItem>,
): EditableContactPackagePlanItem {
  return {
    _localId: createLocalId(),
    enabled: Boolean(plan?.enabled ?? true),
    id: String(plan?.id || '').trim() || undefined,
    name: String(plan?.name || '').trim(),
    price: Number(plan?.price || 0),
    view_count: Number(plan?.view_count || 0),
  };
}

function normalizePayload(
  payload?: Partial<AdminContactPackageConfig> | null,
): EditableContactPackagePlanItem[] {
  if (!Array.isArray(payload?.plans)) {
    return [];
  }
  return payload.plans.map((item) => createEditablePlan(item));
}

async function loadConfig() {
  loading.value = true;
  try {
    const result = await getAdminContactPackageConfigApi();
    formState.display_enabled = Boolean(result?.display_enabled);
    formState.plans = normalizePayload(result);
  } finally {
    loading.value = false;
  }
}

function addPlan() {
  formState.plans.push(createEditablePlan());
}

function removePlan(localId: string) {
  formState.plans = formState.plans.filter((item) => item._localId !== localId);
}

function validatePlans() {
  for (const [index, item] of formState.plans.entries()) {
    const order = index + 1;
    if (!String(item.name || '').trim()) {
      ElMessage.error(`请填写第 ${order} 个人群包名称`);
      return false;
    }
    if (Number(item.view_count || 0) <= 0) {
      ElMessage.error(`请填写第 ${order} 个人群包的查看次数`);
      return false;
    }
    if (Number(item.price || 0) <= 0) {
      ElMessage.error(`请填写第 ${order} 个人群包的金额`);
      return false;
    }
  }
  return true;
}

async function saveConfig() {
  if (!validatePlans()) {
    return;
  }

  saving.value = true;
  try {
    const payload: AdminContactPackageConfig = {
      display_enabled: Boolean(formState.display_enabled),
      plans: formState.plans.map(({ _localId: _ignore, ...item }) => ({
        enabled: Boolean(item.enabled),
        id: String(item.id || '').trim() || undefined,
        name: String(item.name || '').trim(),
        price: Number(item.price || 0),
        view_count: Number(item.view_count || 0),
      })),
    };
    const result = await saveAdminContactPackageConfigApi(payload);
    formState.display_enabled = Boolean(result?.display_enabled);
    formState.plans = normalizePayload(result);
    ElMessage.success('人群包配置已保存');
  } finally {
    saving.value = false;
  }
}

onMounted(() => {
  void loadConfig();
});
</script>

<template>
  <ElCard shadow="never" class="rounded-2xl border-0">
    <template #header>
      <div class="flex items-center justify-between gap-4">
        <div>
          <div class="text-base font-semibold text-slate-900">人群包配置</div>
          <div class="mt-1 text-sm text-slate-500">
            在这里维护“查看别人联系方式”的人群包方案，支持新增多个方案。
          </div>
        </div>
        <div class="flex items-center gap-3">
          <span class="text-sm text-slate-600">前端显示</span>
          <ElSwitch v-model="formState.display_enabled" />
        </div>
      </div>
    </template>

    <div v-loading="loading" class="space-y-4">
      <div class="flex items-center justify-between">
        <div class="text-sm font-medium text-slate-700">方案列表</div>
        <ElButton type="primary" plain @click="addPlan">新增人群包</ElButton>
      </div>

      <div v-if="formState.plans.length" class="space-y-4">
        <ElCard
          v-for="(item, index) in formState.plans"
          :key="item._localId"
          shadow="never"
          class="rounded-2xl border border-slate-200 bg-slate-50/60"
        >
          <template #header>
            <div class="flex items-center justify-between">
              <div class="text-sm font-semibold text-slate-800">
                人群包 {{ index + 1 }}
              </div>
              <div class="flex items-center gap-3">
                <div class="flex items-center gap-2 text-sm text-slate-600">
                  <span>启用</span>
                  <ElSwitch v-model="item.enabled" />
                </div>
                <ElButton link type="danger" @click="removePlan(item._localId)">
                  删除
                </ElButton>
              </div>
            </div>
          </template>

          <ElForm label-position="top">
            <div class="grid gap-4 md:grid-cols-3">
              <ElFormItem label="人群包名称">
                <ElInput v-model="item.name" placeholder="例如：人群包A" />
              </ElFormItem>
              <ElFormItem label="查看联系方式次数">
                <ElInputNumber
                  v-model="item.view_count"
                  :max="100000"
                  :min="1"
                  class="!w-full"
                  controls-position="right"
                />
              </ElFormItem>
              <ElFormItem label="金额">
                <ElInputNumber
                  v-model="item.price"
                  :max="1000000"
                  :min="0.01"
                  :precision="2"
                  :step="1"
                  class="!w-full"
                  controls-position="right"
                />
              </ElFormItem>
            </div>
          </ElForm>
        </ElCard>
      </div>

      <ElEmpty
        v-else
        description="暂无人群包方案，点击右上角“新增人群包”开始配置"
      />

      <div class="flex justify-end">
        <ElButton :loading="saving" type="primary" @click="saveConfig">
          保存人群包配置
        </ElButton>
      </div>
    </div>
  </ElCard>
</template>
