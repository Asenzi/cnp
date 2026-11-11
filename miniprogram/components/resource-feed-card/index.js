Component({
  properties: {
    item: {
      type: Object,
      value: {}
    }
  },

  methods: {
    onTap() {
      this.triggerEvent('detail', { item: this.data.item })
    }
  }
})
