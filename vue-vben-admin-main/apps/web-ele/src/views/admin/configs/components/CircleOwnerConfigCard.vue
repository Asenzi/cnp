<script setup lang="ts">
import type { AdminConfigItem } from '#/api/admin';

import { onMounted, reactive, ref } from 'vue';

import {
  ElButton,
  ElCard,
  ElForm,
  ElFormItem,
  ElInput,
  ElInputNumber,
  ElMessage,
  ElSwitch,
} from 'element-plus';

import { listAdminConfigsApi, saveAdminConfigApi } from '#/api/admin';

defineOptions({ name: 'CircleOwnerConfigCard' });

const loading = ref(false);
const saving = ref(false);
const formState = reactive({
  enabled: true,
  name: '永久圈主',
  originalPrice: 298,
  price: 198,
  subtitle: '一次开通，永久有效',
});

const configMeta = {
  enabled: {
    description: '永久圈主商品是否启用',
    key: 'circle_owner.enabled',
  },
  name: {
    description: '永久圈主商品名称',
    key: 'circle_owner.name',
  },
  originalPrice: {
    description: '永久圈主原价',
    key: 'circle_owner.original_price',
  },
  price: {
    description: '永久圈主售价',
    key: 'circle_owner.price',
  },
  subtitle: {
    description: '永久圈主商品副标题',
    key: 'circle_owner.subtitle',
  },
} as const;

function toMoney(value: unknown, fallback: number) {
  const amount = Number(value);
  return Number.isFinite(amount) && amount >= 0 ? amount : fallback;
}

function applyConfig(items: AdminConfigItem[]) {
  const values = new Map(items.map((item) => [item.config_key, item.config_value]));
  formState.enabled = String(values.get(configMeta.enabled.key) ?? '1') !== '0';
  formState.name =
    String(values.get(configMeta.name.key) || '').trim() || '永久圈主';
  formState.subtitle =
    String(values.get(configMeta.subtitle.key) || '').trim() ||
    '一次开通，永久有效';
  formState.price = toMoney(values.get(configMeta.price.key), 198);
  formState.originalPrice = toMoney(
    values.get(configMeta.originalPrice.key),
    298,
  );
}

async function loadConfig() {
  loading.value = true;
  try {
    const result = await listAdminConfigsApi({
      keyword: 'circle_owner.',
      page: 1,
      page_size: 20,
    });
    applyConfig(result.items);
  } finally {
    loading.value = false;
  }
}

async function saveConfig() {
  const name = formState.name.trim();
  const subtitle = formState.subtitle.trim();
  const price = Number(formState.price);
  const originalPrice = Number(formState.originalPrice);
  if (!name) {
    ElMessage.error('请输入商品名称');
    return;
  }
  if (!Number.isFinite(price) || price <= 0) {
    ElMessage.error('售价必须大于 0 元');
    return;
  }
  if (!Number.isFinite(originalPrice) || originalPrice < price) {
    ElMessage.error('原价不能低于售价');
    return;
  }

  saving.value = true;
  try {
    const rows = [
      [configMeta.enabled, formState.enabled ? '1' : '0'],
      [configMeta.name, name],
      [configMeta.subtitle, subtitle],
      [configMeta.price, price.toFixed(2)],
      [configMeta.originalPrice, originalPrice.toFixed(2)],
    ] as const;
    await Promise.all(
      rows.map(([meta, configValue]) =>
        saveAdminConfigApi(meta.key, {
          config_group: 'payment',
          config_value: configValue,
          description: meta.description,
        }),
      ),
    );
    ElMessage.success('永久圈主商品配置已保存，新的支付订单将使用最新价格');
    await loadConfig();
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
          <div class="text-base font-semibold text-slate-900">
            永久圈主商品
          </div>
          <div class="mt-1 text-sm text-slate-500">
            配置小程序“成为圈主”页面展示与实际支付金额，保存后对新订单立即生效。
          </div>
        </div>
        <div class="flex items-center gap-3">
          <span class="text-sm text-slate-600">允许开通</span>
          <ElSwitch v-model="formState.enabled" />
        </div>
      </div>
    </template>

    <ElForm v-loading="loading" label-position="top">
      <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <ElFormItem label="商品名称">
          <ElInput v-model="formState.name" maxlength="40" />
        </ElFormItem>
        <ElFormItem label="商品副标题">
          <ElInput v-model="formState.subtitle" maxlength="80" />
        </ElFormItem>
        <ElFormItem label="实际售价（元）">
          <ElInputNumber
            v-model="formState.price"
            :max="1000000"
            :min="0.01"
            :precision="2"
            :step="1"
            class="!w-full"
            controls-position="right"
          />
        </ElFormItem>
        <ElFormItem label="划线原价（元）">
          <ElInputNumber
            v-model="formState.originalPrice"
            :max="1000000"
            :min="0.01"
            :precision="2"
            :step="1"
            class="!w-full"
            controls-position="right"
          />
        </ElFormItem>
      </div>

      <div class="flex items-center justify-between gap-4">
        <div class="text-sm text-slate-500">
          当前开通按钮将显示：支付 ¥{{ Number(formState.price || 0).toFixed(2) }}
          永久开通
        </div>
        <ElButton :loading="saving" type="primary" @click="saveConfig">
          保存圈主商品配置
        </ElButton>
      </div>
    </ElForm>
  </ElCard>
</template>
