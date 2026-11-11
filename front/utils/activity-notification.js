import { request } from './request'
export function reportActivity(targetType, targetId, action) {
  if (!targetId || !uni.getStorageSync('token')) return
  request({url:'/api/v1/notifications/activity',method:'POST',data:{target_type:targetType,target_id:String(targetId),action}}).catch(() => {})
}
