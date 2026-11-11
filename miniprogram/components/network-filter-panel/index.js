import { INDUSTRY_OPTIONS } from '../../utils/industry-options'

Component({
  properties: {
    visible: { type: Boolean, value: false },
    value: { type: Object, value: {} },
    options: { type: Object, value: {} }
  },

  data: {
    draftIndustry: '',
    industryOptions: INDUSTRY_OPTIONS
  },

  observers: {
    'visible, value, options': function (visible, value, options) {
      const industries = options && Array.isArray(options.industries) && options.industries.length
        ? options.industries
        : INDUSTRY_OPTIONS
      const patch = { industryOptions: industries }
      if (visible) patch.draftIndustry = String(value && value.industry_label || '').trim()
      this.setData(patch)
    }
  },

  methods: {
    setIndustry(event) {
      this.setData({ draftIndustry: String(event.currentTarget.dataset.industry || '').trim() })
    },

    onPanelTap() {},

    onClose() {
      this.triggerEvent('close')
    },

    onReset() {
      this.setData({ draftIndustry: '' })
      this.triggerEvent('reset', { industry_label: '' })
    },

    onApply() {
      this.triggerEvent('apply', { industry_label: this.data.draftIndustry })
    }
  }
})
