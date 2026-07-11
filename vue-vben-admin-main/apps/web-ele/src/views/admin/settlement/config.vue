<script setup lang="ts">
import type { AdminSplitConfig } from '#/api/admin';

import { onMounted, reactive, ref } from 'vue';

import {
  ElAlert,
  ElButton,
  ElCard,
  ElForm,
  ElFormItem,
  ElInputNumber,
  ElMessage,
  ElSwitch,
  ElTag,
} from 'element-plus';

import {
  getAdminSplitConfigApi,
  saveAdminSplitConfigApi,
} from '#/api/admin';
import { formatDateTime } from '#/utils/admin';

defineOptions({ name: 'AdminSplitConfigPage' });

const loading = ref(false);
const saving = ref(false);
const config = ref<AdminSplitConfig | null>(null);
const form = reactive({
  auto_settle_enabled: true,
  service_fee_percent: 10,
  wechat_profit_sharing_enabled: false,
});

function applyConfig(data: AdminSplitConfig) {
  config.value = data;
  form.service_fee_percent = Number((Number(data.service_fee_rate || 0) * 100).toFixed(2));
  form.auto_settle_enabled = Boolean(data.auto_settle_enabled);
  form.wechat_profit_sharing_enabled = Boolean(data.wechat_profit_sharing_enabled);
}

async function loadConfig() {
  loading.value = true;
  try {
    applyConfig(await getAdminSplitConfigApi());
  } finally {
    loading.value = false;
  }
}

async function saveConfig() {
  saving.value = true;
  try {
    const result = await saveAdminSplitConfigApi({
      auto_settle_enabled: form.auto_settle_enabled,
      service_fee_rate: Number((form.service_fee_percent / 100).toFixed(4)),
      wechat_profit_sharing_enabled: form.wechat_profit_sharing_enabled,
    });
    applyConfig(result);
    ElMessage.success('分账配置已保存');
  } finally {
    saving.value = false;
  }
}

onMounted(() => {
  void loadConfig();
});
</script>

<template>
  <div class="space-y-4 p-5">
    <div class="space-y-1">
      <h1 class="text-2xl font-semibold text-slate-900">分账配置</h1>
      <p class="text-sm text-slate-500">
        当前用于付费入圈场景：平台收取技术服务费，剩余金额结算给圈主。
      </p>
    </div>

    <ElAlert
      :closable="false"
      show-icon
      title="第一版为内部收益账本：支付成功后生成分账记录，通过入圈后自动计入圈主收益。微信支付真实分账接收方绑定与回退可在下一阶段接入。"
      type="info"
    />

    <ElCard v-loading="loading" shadow="never" class="max-w-3xl rounded-2xl border-0">
      <ElForm label-width="140px">
        <ElFormItem label="业务类型">
          <ElTag type="primary">付费入圈 circle_join</ElTag>
        </ElFormItem>
        <ElFormItem label="技术服务费">
          <ElInputNumber
            v-model="form.service_fee_percent"
            :max="99"
            :min="0"
            :precision="2"
            :step="1"
          />
          <span class="ml-2 text-sm text-slate-500">%</span>
        </ElFormItem>
        <ElFormItem label="圈主分账比例">
          <span class="text-base font-semibold text-slate-900">
            {{ (100 - form.service_fee_percent).toFixed(2) }}%
          </span>
        </ElFormItem>
        <ElFormItem label="通过后自动结算">
          <ElSwitch v-model="form.auto_settle_enabled" />
          <span class="ml-3 text-sm text-slate-500">关闭后订单会停留在 ready，等待后续人工/微信分账任务处理。</span>
        </ElFormItem>
        <ElFormItem label="微信真实分账">
          <ElSwitch v-model="form.wechat_profit_sharing_enabled" />
          <span class="ml-3 text-sm text-slate-500">开启后，付费入圈微信订单会带分账标识，并在通过入圈时请求微信分账。</span>
        </ElFormItem>
        <ElFormItem label="更新时间">
          <span class="text-slate-500">{{ formatDateTime(config?.updated_at) }}</span>
        </ElFormItem>
        <ElFormItem>
          <ElButton :loading="saving" type="primary" @click="saveConfig">
            保存配置
          </ElButton>
        </ElFormItem>
      </ElForm>
    </ElCard>
  </div>
</template>
