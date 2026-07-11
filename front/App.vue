<script>
	import { clearLocationSessionCache, getQqMapKeyInfo } from './pages/tab/discover/modules/location'
	import { connectRealtimeSocket, disconnectRealtimeSocket } from './utils/realtime'
	import { syncUserLocation } from './utils/location-sync'

	let lastSyncTime = 0
	const SYNC_THROTTLE_MS = 5 * 60 * 1000 // 5分钟节流

	export default {
		onLaunch: function() {
			console.log('App Launch')
      const mapKeyInfo = getQqMapKeyInfo()
      if (mapKeyInfo?.key && mapKeyInfo?.source === 'env' && !uni.getStorageSync('__QQ_MAP_KEY__')) {
        uni.setStorageSync('__QQ_MAP_KEY__', mapKeyInfo.key)
      }
      clearLocationSessionCache()
			connectRealtimeSocket()

			// 应用启动时必定同步位置
			const token = uni.getStorageSync('token')
			console.log('[App] onLaunch - 检查登录状态:', token ? '已登录' : '未登录')
			if (token) {
				console.log('[App] onLaunch - 用户已登录，立即同步位置')
				lastSyncTime = Date.now()
				syncUserLocation(true).then(() => {
					console.log('[App] onLaunch - 位置同步成功')
				}).catch(err => {
					console.error('[App] onLaunch - 位置同步失败:', err)
				})
			}
		},
		onShow: function() {
			console.log('App Show')
			connectRealtimeSocket()

			// 应用显示时，如果距离上次同步超过5分钟则同步
			const token = uni.getStorageSync('token')
			const now = Date.now()
			const timeSinceLastSync = now - lastSyncTime

			console.log('[App] onShow - 检查登录状态:', token ? '已登录' : '未登录')
			console.log('[App] onShow - 距离上次同步:', Math.floor(timeSinceLastSync / 1000), '秒')

			if (token && timeSinceLastSync > SYNC_THROTTLE_MS) {
				console.log('[App] onShow - 超过节流时间，开始同步位置')
				lastSyncTime = now
				syncUserLocation(true).then(() => {
					console.log('[App] onShow - 位置同步成功')
				}).catch(err => {
					console.error('[App] onShow - 位置同步失败:', err)
				})
			} else if (token) {
				console.log('[App] onShow - 未超过节流时间，跳过同步')
			}
		},
		onHide: function() {
			console.log('App Hide')
			disconnectRealtimeSocket()
		}
	}
</script>

<style>
	/*每个页面公共css */

	/* 禁止滚动条 */
	page {
		scrollbar-width: none; /* Firefox */
		-ms-overflow-style: none; /* IE */
	}

	page::-webkit-scrollbar {
		display: none; /* WebKit */
		width: 0;
		height: 0;
	}

	view::-webkit-scrollbar,
	scroll-view::-webkit-scrollbar {
		display: none;
		width: 0;
		height: 0;
	}
</style>
