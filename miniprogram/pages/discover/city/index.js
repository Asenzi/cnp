import { PROVINCE_CITY_OPTIONS } from '../../../utils/city-picker-data'
import {
  getLocationErrorMessage,
  loadLocationFilterCache,
  resolveCurrentCityByGps,
  saveCurrentCity
} from '../../../utils/location'

const DEFAULT_CITY = '全国'
const LOCATION_PAGE_RESULT_STORAGE_KEY = 'discover_location_page_result_v1'
const FALLBACK_HOT_CITIES = ['北京', '上海', '广州', '深圳', '杭州', '成都', '武汉', '苏州', '西安', '天津', '重庆', '南京']
const LOCATION_FILTER_CACHE = loadLocationFilterCache()

function normalizeText(value) {
  const raw = String(value || '')
  try {
    return decodeURIComponent(raw).trim()
  } catch (err) {
    return raw.trim()
  }
}

function buildCityEntries() {
  const cities = new Map()
  PROVINCE_CITY_OPTIONS.forEach((province) => {
    ;(province.cities || []).forEach((city) => {
      const label = normalizeText(city.label)
      const value = normalizeText(city.value)
      if (label && !cities.has(label)) cities.set(label, { label, value })
    })
  })
  return Array.from(cities.values())
}

const CITY_ENTRIES = buildCityEntries()

Page({
  data: {
    keyword: '',
    currentCity: DEFAULT_CITY,
    selectedCity: DEFAULT_CITY,
    locating: false,
    scrollIntoView: '',
    hotCities: [],
    visibleHotCities: [],
    groupedCities: [],
    indexedLetters: [],
    currentCitySelected: false
  },

  onLoad(query) {
    const currentCity = normalizeText(query && query.currentCity)
      || LOCATION_FILTER_CACHE.currentCity || DEFAULT_CITY
    const selectedCity = normalizeText(query && query.selectedCity)
      || (LOCATION_FILTER_CACHE.mode === 'national'
        ? DEFAULT_CITY
        : LOCATION_FILTER_CACHE.selectedCity || currentCity)
    const channel = this.getOpenerEventChannel ? this.getOpenerEventChannel() : null
    this._openerEventChannel = channel
    this._setCityState({
      currentCity,
      selectedCity,
      hotCities: this._buildHotCities(currentCity)
    })

    if (channel) {
      channel.on('locationPage:init', (payload = {}) => {
        const nextCurrentCity = normalizeText(payload.currentCity)
        this._setCityState({
          currentCity: nextCurrentCity || this.data.currentCity,
          selectedCity: normalizeText(payload.selectedCity) || nextCurrentCity || this.data.currentCity,
          hotCities: this._buildHotCities(
            nextCurrentCity || this.data.currentCity,
            payload.historyCities,
            payload.hotCities
          )
        })
      })
    }
  },

  _buildHotCities(...sources) {
    const values = []
    sources.forEach((source) => {
      if (Array.isArray(source)) values.push(...source)
      else values.push(source)
    })
    return Array.from(new Set(values.concat(FALLBACK_HOT_CITIES)
      .map(normalizeText).filter((city) => city && city !== DEFAULT_CITY))).slice(0, 12)
  },

  _setCityState(patch) {
    const next = Object.assign({}, patch)
    const selectedCity = next.selectedCity || this.data.selectedCity
    const keyword = String(next.keyword === undefined ? this.data.keyword : next.keyword).trim().toLowerCase()
    const currentCity = next.currentCity || this.data.currentCity
    const hotCities = next.hotCities || this.data.hotCities
    const activeCity = selectedCity || currentCity
    const visibleHotCities = Array.from(new Set(hotCities.map(normalizeText).filter(Boolean)))
      .filter((city) => !keyword || city.toLowerCase().includes(keyword))
      .map((label) => ({ label, active: label === activeCity }))
    const groups = new Map()
    CITY_ENTRIES.forEach((city) => {
      if (keyword && !city.label.toLowerCase().includes(keyword) && !city.value.toLowerCase().includes(keyword)) return
      const letter = (city.value.charAt(0) || '#').toUpperCase()
      if (!groups.has(letter)) groups.set(letter, [])
      groups.get(letter).push(Object.assign({}, city, { active: city.label === activeCity }))
    })
    const groupedCities = Array.from(groups.entries())
      .sort((a, b) => a[0].localeCompare(b[0]))
      .map(([letter, cities]) => ({ letter, cities: cities.sort((a, b) => a.value.localeCompare(b.value)) }))
    this.setData(Object.assign({}, next, {
      visibleHotCities,
      groupedCities,
      indexedLetters: groupedCities.map((group) => group.letter),
      currentCitySelected: currentCity === activeCity
    }))
  },

  onInputKeyword(event) {
    this._setCityState({ keyword: String(event.detail && event.detail.value || '') })
  },

  onTapIndex(event) {
    const letter = event.currentTarget.dataset.letter
    this.setData({ scrollIntoView: '' })
    setTimeout(() => this.setData({ scrollIntoView: `letter-${letter}` }), 0)
  },

  onSelectCurrentCity() {
    this._selectCity(this.data.currentCity)
  },

  onSelectCity(event) {
    this._selectCity(event.currentTarget.dataset.city)
  },

  onSelectAllCity() {
    this._selectCity(DEFAULT_CITY)
  },

  _selectCity(city) {
    const normalizedCity = normalizeText(city)
    if (!normalizedCity) return
    wx.setStorageSync(LOCATION_PAGE_RESULT_STORAGE_KEY, {
      type: 'select', city: normalizedCity, timestamp: Date.now()
    })
    if (this._openerEventChannel) this._openerEventChannel.emit('locationPage:select', { city: normalizedCity })
    setTimeout(() => wx.navigateBack(), 0)
  },

  async onRefreshLocation() {
    if (this.data.locating) return
    this.setData({ locating: true })
    try {
      const city = await resolveCurrentCityByGps()
      saveCurrentCity(city)
      wx.setStorageSync(LOCATION_PAGE_RESULT_STORAGE_KEY, {
        type: 'relocate', city, timestamp: Date.now()
      })
      if (this._openerEventChannel) this._openerEventChannel.emit('locationPage:relocate', { city })
      wx.showToast({ title: `已定位到：${city}`, icon: 'none' })
      this._setCityState({ currentCity: city, selectedCity: city })
    } catch (error) {
      wx.showToast({ title: getLocationErrorMessage(error), icon: 'none' })
    } finally {
      this.setData({ locating: false })
    }
  }
})
