/**
 * 城市查询候选词构造
 *
 * 原实现依赖完整的省市字典（city-picker-data，数千行），只为在
 * "深圳 / 深圳市" 这类写法之间做变体匹配。P1 阶段不引入该字典，
 * 退化为「原值 + 去后缀」，语义等价且体积可控。
 * 后续若需要精确的省份归属匹配，再接入字典。
 */

const normalizeText = (value) => String(value || '').trim()

const uniqueList = (items = []) => {
  const seen = new Set()
  const result = []
  for (const item of items) {
    const normalized = normalizeText(item)
    if (!normalized) {
      continue
    }
    const key = normalized.toLowerCase()
    if (seen.has(key)) {
      continue
    }
    seen.add(key)
    result.push(normalized)
  }
  return result
}

export function buildCityQueryCandidates(cityText) {
  const normalized = normalizeText(cityText)
  if (!normalized) {
    return []
  }

  const stripped = normalized.replace(/(市|地区)$/, '')
  return uniqueList([normalized, stripped])
}
