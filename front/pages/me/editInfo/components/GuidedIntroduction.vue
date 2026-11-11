<template>
  <view class="intro-guide">
    <text class="guide-tip">按以下问题介绍自己，可选填；合计最多255字。</text>
    <view v-if="legacy" class="guide-field"><text class="guide-label">原有简介</text><textarea :value="legacy" class="guide-input" :maxlength="-1" placeholder="原有内容会保留，可在这里编辑" @input="updateLegacy"/></view>
    <view v-for="(question,index) in questions" :key="question.label" class="guide-field">
      <text class="guide-label">{{index + 1}}. {{question.label}}？</text>
      <textarea :value="answers[index]" class="guide-input" :maxlength="-1" :placeholder="question.placeholder" @input="updateAnswer(index,$event)"/>
    </view>
    <text class="guide-count" :class="{'over-limit':modelValue.length>255}">{{modelValue.length}} / 255</text>
  </view>
</template>
<script setup>
import {ref,watch} from 'vue'
const props=defineProps({modelValue:{type:String,default:''}})
const emit=defineEmits(['update:modelValue'])
const questions=[
 {label:'来自哪里',placeholder:'例如：来自深圳，目前生活在广州'},
 {label:'做什么的',placeholder:'介绍你的职业、专业领域或正在做的事'},
 {label:'为谁',placeholder:'你主要服务或希望连接哪些人群'},
 {label:'提供什么',placeholder:'你能提供哪些产品、服务或资源'},
 {label:'解决什么问题',placeholder:'你擅长解决哪些具体难题'},
 {label:'带来什么价值',placeholder:'你的服务能带来哪些成果或改变'},
 {label:'有什么爱好',placeholder:'分享兴趣爱好，让大家更了解你'}
]
const answers=ref(questions.map(()=>''))
const legacy=ref('')
let lastEmitted=null
watch(()=>props.modelValue,value=>{
 if(value===lastEmitted)return
 const next=questions.map(()=>'');const other=[]
 for(const line of String(value||'').split('\n')){
  const index=questions.findIndex(q=>line.startsWith(q.label+'：'))
  if(index>=0)next[index]=line.slice(questions[index].label.length+1)
  else if(line.trim())other.push(line)
 }
 answers.value=next;legacy.value=other.join('\n')
},{immediate:true})
function publish(){
 const lines=questions.map((q,i)=>answers.value[i].trim()?q.label+'：'+answers.value[i].trim():'').filter(Boolean)
 lastEmitted=[legacy.value.trim(),...lines].filter(Boolean).join('\n')
 emit('update:modelValue',lastEmitted)
}
function updateAnswer(index,event){answers.value[index]=String(event.detail.value||'').replace(/\n/g,' ');publish()}
function updateLegacy(event){legacy.value=event.detail.value||'';publish()}
</script>
<style scoped>
.intro-guide{width:100%}.guide-tip{display:block;font-size:26rpx;line-height:38rpx;color:#788295;margin-bottom:20rpx}.guide-field{margin-bottom:20rpx}.guide-label{display:block;font-size:28rpx;line-height:40rpx;color:#334155;margin-bottom:10rpx}.guide-input{box-sizing:border-box;width:100%;height:120rpx;padding:16rpx 20rpx;border:1rpx solid #e2e8f0;border-radius:8rpx;background:#f8fafc;font-size:28rpx;line-height:40rpx;color:#172033}.guide-count{display:block;text-align:right;font-size:26rpx;color:#788295}.over-limit{color:#dc2626}
</style>
