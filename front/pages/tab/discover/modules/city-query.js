import { PROVINCE_CITY_OPTIONS } from '../../../me/editInfo/modules/city-picker-data'

const CITY_ENTRIES = PROVINCE_CITY_OPTIONS.flatMap((province) => {
  const cities = Array.isArray(province?.cities) ? province.cities : []
  return cities.map((city) => ({
    label: String(city?.label || '').trim(),
    value: String(city?.value || '').trim()
  }))
})

const normalizeText = (value) => String(value || '').trim()

const toTitleCase = (value) => {
  const normalized = normalizeText(value)
  if (!normalized) {
    return ''
  }
  return normalized.charAt(0).toUpperCase() + normalized.slice(1)
}

const uniqueList = (items = []) => {
  const seen = new Set()
  const result = []
  for (const item of items) {
    const normalized = normalizeText(item)
    if (!normalized || seen.has(normalized.toLowerCase())) {
      continue
    }
    seen.add(normalized.toLowerCase())
    result.push(normalized)
  }
  return result
}

function findCityEntry(cityText) {
  const normalized = normalizeText(cityText)
  if (!normalized) {
    return null
  }
  const normalizedLower = normalized.toLowerCase()
  return CITY_ENTRIES.find((item) => {
    const label = normalizeText(item.label)
    const value = normalizeText(item.value)
    return (
      label === normalized
      || value === normalized
      || label.toLowerCase() === normalizedLower
      || value.toLowerCase() === normalizedLower
    )
  }) || null
}

export function buildCityQueryCandidates(cityText) {
  const normalized = normalizeText(cityText)
  if (!normalized) {
    return []
  }

  const entry = findCityEntry(normalized)
  if (entry) {
    return uniqueList([
      normalized,
      entry.label,
      entry.value,
      toTitleCase(entry.value)
    ])
  }

  const stripped = normalized.replace(/市$/, '')
  return uniqueList([
    normalized,
    stripped,
    toTitleCase(stripped)
  ])
}

