import {
  confirmMemberOrderPayment,
  getMemberOrderStatus,
  purchasePartner
} from '../api/payment'
import { refreshWechatSessionForPayment } from './payment-session'

function virtualPaymentErrorMessage(error) {
  const message = String(error?.errMsg || error?.message || '')
  const code = String(error?.errCode || error?.errno || '')
  const normalized = message.toLowerCase()
  if (code === '-15005' || normalized.includes('signature_invalid')) {
    return '微信登录态已失效，请重新登录后再支付'
  }
  if (code === '-15001' || message.includes('尚未开启iOS支付')) {
    return '当前小程序尚未开启 iOS 支付，请先在微信后台开启苹果 IAP 支付'
  }
  return message || '支付失败，请稍后重试'
}

async function payVirtualOrder(result) {
  const orderNo = String(result?.order_no || '').trim()
  const payment = result?.virtual_payment || {}
  const signData = payment.signData && typeof payment.signData === 'object'
    ? payment.signData
    : null
  if (!orderNo || !signData || !payment.paySig || !payment.signature || !payment.mode) {
    throw new Error('小程序虚拟支付参数异常')
  }
  const payResult = await new Promise((resolve, reject) => {
    uni.requestVirtualPayment({
      signData: String(payment.signDataJson || JSON.stringify(signData)),
      mode: String(payment.mode),
      paySig: String(payment.paySig),
      signature: String(payment.signature),
      success: (response) => resolve(response || {}),
      fail: (error) => reject({ ...(error || {}), order_no: orderNo })
    })
  })
  try {
    await confirmMemberOrderPayment(orderNo, {
      transaction_id: String(payResult?.transactionId || payResult?.transaction_id || '').trim(),
      ext: payResult
    })
  } catch (error) {
    const status = await getMemberOrderStatus(orderNo)
    if (!Boolean(status?.paid)) throw error
  }
}

export async function openPartnerIdentity(partnerType, payChannel = 'virtualpay') {
  if (!String(uni.getStorageSync('token') || '').trim()) {
    throw new Error('请先登录')
  }
  if (String(payChannel || '').trim() === 'virtualpay') {
    await refreshWechatSessionForPayment()
  }
  try {
    const result = await purchasePartner(partnerType, { pay_channel: payChannel })
    if (String(result?.action || '') === 'virtualpay_required') {
      await payVirtualOrder(result)
    }
    return result
  } catch (error) {
    const orderNo = String(error?.order_no || '').trim()
    if (orderNo && String(error?.errMsg || error?.message || '').toLowerCase().includes('cancel')) {
      try {
        const status = await getMemberOrderStatus(orderNo)
        if (Boolean(status?.paid)) return status
      } catch {
        // Keep the original payment cancellation.
      }
      throw new Error('已取消支付')
    }
    throw new Error(virtualPaymentErrorMessage(error))
  }
}
