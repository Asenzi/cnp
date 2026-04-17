<script>
	import { clearLocationSessionCache, getQqMapKeyInfo } from './pages/tab/discover/modules/location'

	export default {
		onLaunch: function() {
			console.log('App Launch')
      const mapKeyInfo = getQqMapKeyInfo()
      if (mapKeyInfo?.key && mapKeyInfo?.source === 'env' && !uni.getStorageSync('__QQ_MAP_KEY__')) {
        uni.setStorageSync('__QQ_MAP_KEY__', mapKeyInfo.key)
      }
      clearLocationSessionCache()
		},
		onShow: function() {
			console.log('App Show')
		},
		onHide: function() {
			console.log('App Hide')
		}
	}
</script>

<style>
	/*每个页面公共css */
</style>
