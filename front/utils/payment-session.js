import { bindWechatMiniapp } from '../api/auth'
import { getMiniappLoginCode, getWechatDeviceId } from './wechat-auth'

export async function refreshWechatSessionForPayment() {
  // #ifdef MP-WEIXIN
  const code = await getMiniappLoginCode()
  await bindWechatMiniapp({
    code,
    device_id: getWechatDeviceId()
  })
  // #endif
}
