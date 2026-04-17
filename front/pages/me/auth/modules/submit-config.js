import { VERIFICATION_TYPE } from './verification-types'

const TYPE_CONFIG_MAP = {
  [VERIFICATION_TYPE.REAL_NAME]: {
    title: '实名认证',
    desc: '请填写真实身份信息，提交后将用于平台身份核验。',
    submitText: '提交实名认证',
    successText: '实名认证提交成功'
  },
  [VERIFICATION_TYPE.ENTERPRISE]: {
    title: '企业认证',
    desc: '请填写企业主体信息并上传营业执照。',
    submitText: '提交企业认证',
    successText: '企业认证提交成功'
  },
  [VERIFICATION_TYPE.BUSINESS_CARD]: {
    title: '名片认证',
    desc: '请上传名片并补全信息，帮助平台完成职业身份核验。',
    submitText: '提交名片认证',
    successText: '名片认证提交成功'
  }
}

export function getSubmitTypeConfig(type) {
  return TYPE_CONFIG_MAP[type] || TYPE_CONFIG_MAP[VERIFICATION_TYPE.BUSINESS_CARD]
}

export function validateSubmitForm(type, form) {
  const normalize = (value) => String(value || '').trim()

  if (type === VERIFICATION_TYPE.BUSINESS_CARD) {
    if (!normalize(form.card_holder_name)) {
      return '请输入名片姓名'
    }
    if (!normalize(form.card_file_url)) {
      return '请先上传名片文件'
    }
    return ''
  }

  return ''
}

export function buildSubmitPayload(type, form) {
  const normalize = (value, maxLen = 255) => {
    const text = String(value || '').trim()
    return text ? text.slice(0, maxLen) : ''
  }

  if (type === VERIFICATION_TYPE.BUSINESS_CARD) {
    return {
      card_holder_name: normalize(form.card_holder_name, 32),
      company_name: normalize(form.company_name, 128) || null,
      card_title: normalize(form.card_title, 64) || null,
      card_file_url: normalize(form.card_file_url, 255)
    }
  }

  return {}
}
