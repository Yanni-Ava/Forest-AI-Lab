<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'

type Detection = {
  class_name: string
  confidence: number
  box: { x1: number; y1: number; x2: number; y2: number }
}

type DetectionResponse = {
  filename: string
  width: number
  height: number
  detection_count: number
  detections: Detection[]
  vegetation?: {
    method: string
    coverage: number
    coverage_pct: number
    threshold: number
    vegetation_pixels: number
    total_pixels: number
    note: string
  }
  inference_ms: number
  result_url: string
  vegetation_url?: string
}

const API_BASE = (import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/$/, '')
const MAX_FILE_SIZE = 10 * 1024 * 1024
const fileInput = ref<HTMLInputElement | null>(null)
const videoElement = ref<HTMLVideoElement | null>(null)
const selectedFile = ref<File | null>(null)
const previewUrl = ref('')
const result = ref<DetectionResponse | null>(null)
const resultImageUrl = ref('')
const vegetationImageUrl = ref('')
const isDragging = ref(false)
const isDetecting = ref(false)
const serviceOnline = ref<boolean | null>(null)
const errorMessage = ref('')
const inputMode = ref<'upload' | 'camera'>('upload')
const cameraStream = ref<MediaStream | null>(null)
const cameraReady = ref(false)

const groupedDetections = computed(() => {
  const groups = new Map<string, { count: number; bestConfidence: number }>()
  for (const detection of result.value?.detections || []) {
    const current = groups.get(detection.class_name) || { count: 0, bestConfidence: 0 }
    groups.set(detection.class_name, {
      count: current.count + 1,
      bestConfidence: Math.max(current.bestConfidence, detection.confidence),
    })
  }
  return [...groups.entries()].map(([name, value]) => ({ name, ...value }))
})

const apiEndpoint = (path: string) => `${API_BASE}${path}`

function resolveResultUrl(path: string) {
  if (/^https?:\/\//.test(path)) return path
  if (/^https?:\/\//.test(API_BASE)) return new URL(path, API_BASE).toString()
  return path
}

function clearPreview() {
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
  previewUrl.value = ''
}

function selectFile(file?: File) {
  errorMessage.value = ''
  result.value = null
  resultImageUrl.value = ''
  vegetationImageUrl.value = ''
  if (!file) return
  if (!file.type.startsWith('image/')) {
    errorMessage.value = '请选择 JPG、PNG、BMP 或 WebP 图片。'
    return
  }
  if (file.size > MAX_FILE_SIZE) {
    errorMessage.value = '图片不能超过 10 MB。'
    return
  }
  clearPreview()
  selectedFile.value = file
  previewUrl.value = URL.createObjectURL(file)
}

function onFileChange(event: Event) {
  selectFile((event.target as HTMLInputElement).files?.[0])
}

function onDrop(event: DragEvent) {
  isDragging.value = false
  selectFile(event.dataTransfer?.files?.[0])
}

async function checkHealth() {
  try {
    serviceOnline.value = (await fetch(apiEndpoint('/health'))).ok
  } catch {
    serviceOnline.value = false
  }
}

async function detectFile(file: File) {
  if (isDetecting.value) return
  errorMessage.value = ''
  result.value = null
  resultImageUrl.value = ''
  vegetationImageUrl.value = ''
  isDetecting.value = true
  const formData = new FormData()
  formData.append('file', file)
  try {
    const response = await fetch(apiEndpoint('/detect'), { method: 'POST', body: formData })
    const body = await response.json()
    if (!response.ok) throw new Error(body.detail || '识别失败，请稍后重试。')
    result.value = body as DetectionResponse
    resultImageUrl.value = resolveResultUrl(result.value.result_url)
    vegetationImageUrl.value = result.value.vegetation_url ? resolveResultUrl(result.value.vegetation_url) : ''
    serviceOnline.value = true
  } catch (error) {
    serviceOnline.value = false
    errorMessage.value = error instanceof Error ? error.message : '无法连接视觉服务。'
  } finally {
    isDetecting.value = false
  }
}

async function detectImage() {
  if (selectedFile.value) await detectFile(selectedFile.value)
}

function stopCamera() {
  cameraStream.value?.getTracks().forEach((track) => track.stop())
  cameraStream.value = null
  cameraReady.value = false
  if (videoElement.value) videoElement.value.srcObject = null
}

async function startCamera() {
  errorMessage.value = ''
  if (!navigator.mediaDevices?.getUserMedia) {
    errorMessage.value = '当前浏览器不支持摄像头访问。'
    return
  }
  try {
    cameraStream.value = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: 'environment', width: { ideal: 1280 }, height: { ideal: 720 } },
      audio: false,
    })
    await nextTick()
    if (videoElement.value) {
      videoElement.value.srcObject = cameraStream.value
      await videoElement.value.play()
      cameraReady.value = true
    }
  } catch {
    stopCamera()
    errorMessage.value = '摄像头开启失败，请检查 Windows 和浏览器权限。'
  }
}

async function captureCameraFrame() {
  const video = videoElement.value
  if (!video || !cameraReady.value || !video.videoWidth || isDetecting.value) return
  const canvas = document.createElement('canvas')
  canvas.width = video.videoWidth
  canvas.height = video.videoHeight
  canvas.getContext('2d')?.drawImage(video, 0, 0, canvas.width, canvas.height)
  const blob = await new Promise<Blob | null>((resolve) => canvas.toBlob(resolve, 'image/jpeg', 0.9))
  if (!blob) {
    errorMessage.value = '无法截取摄像头画面。'
    return
  }
  await detectFile(new File([blob], `camera-${Date.now()}.jpg`, { type: 'image/jpeg' }))
}

function switchMode(mode: 'upload' | 'camera') {
  if (inputMode.value === mode) return
  if (mode === 'upload') stopCamera()
  reset()
  inputMode.value = mode
}

function reset() {
  selectedFile.value = null
  result.value = null
  resultImageUrl.value = ''
  vegetationImageUrl.value = ''
  errorMessage.value = ''
  clearPreview()
  if (fileInput.value) fileInput.value.value = ''
}

onMounted(checkHealth)
onBeforeUnmount(() => {
  clearPreview()
  stopCamera()
})
</script>

<template>
  <div class="app-shell">
    <header class="topbar">
      <a class="brand" href="#">
        <span class="brand-mark"><svg viewBox="0 0 32 32"><path d="M16 3 5 15h7l-5 7h7v7h4v-7h7l-5-7h7L16 3Z" /></svg></span>
        <span>Forest AI Lab</span>
      </a>
      <div class="status" :class="{ online: serviceOnline, offline: serviceOnline === false }">
        <span class="status-dot"></span>
        {{ serviceOnline === null ? '正在连接' : serviceOnline ? '视觉服务在线' : '视觉服务离线' }}
      </div>
    </header>

    <main>
      <section class="hero-copy">
        <p class="eyebrow">YOLO26 · 本地智能识别</p>
        <h1>让每一张图片<br /><span>看得见，也看得懂。</span></h1>
        <p class="intro">上传一张图片，由本机视觉模型识别常见物体。图片不会离开这台电脑。</p>
      </section>

      <section class="workspace">
        <div class="panel upload-panel">
          <div class="panel-heading">
            <div><span class="step-number">01</span><h2>{{ inputMode === 'upload' ? '选择图片' : '摄像头画面' }}</h2></div>
            <button v-if="inputMode === 'upload' && selectedFile" class="text-button" type="button" @click="reset">重新选择</button>
            <button v-if="inputMode === 'camera' && cameraReady" class="text-button" type="button" @click="stopCamera">关闭摄像头</button>
          </div>

          <div class="mode-switch" role="tablist" aria-label="识别输入方式">
            <button type="button" :class="{ active: inputMode === 'upload' }" @click="switchMode('upload')">上传图片</button>
            <button type="button" :class="{ active: inputMode === 'camera' }" @click="switchMode('camera')">使用摄像头</button>
          </div>

          <template v-if="inputMode === 'upload'">
            <input ref="fileInput" class="sr-only" type="file" accept="image/jpeg,image/png,image/bmp,image/webp" @change="onFileChange" />
            <button
              v-if="!selectedFile"
              class="dropzone"
              :class="{ dragging: isDragging }"
              type="button"
              @click="fileInput?.click()"
              @dragenter.prevent="isDragging = true"
              @dragover.prevent="isDragging = true"
              @dragleave.prevent="isDragging = false"
              @drop.prevent="onDrop"
            >
              <span class="upload-icon"><svg viewBox="0 0 24 24"><path d="M12 16V4m0 0L7 9m5-5 5 5M5 14v5h14v-5" /></svg></span>
              <strong>拖放图片到这里</strong>
              <span>或点击浏览文件</span>
              <small>JPG、PNG、BMP、WebP · 最大 10 MB</small>
            </button>
            <div v-else class="preview-card">
              <img :src="previewUrl" :alt="selectedFile.name" />
              <div class="file-meta"><span class="file-name">{{ selectedFile.name }}</span><span>{{ (selectedFile.size / 1024).toFixed(1) }} KB</span></div>
            </div>
          </template>

          <div v-else class="camera-stage" :class="{ ready: cameraReady }">
            <video ref="videoElement" autoplay muted playsinline></video>
            <div v-if="!cameraReady" class="camera-placeholder">
              <span class="camera-icon"><svg viewBox="0 0 24 24"><path d="M4 7h3l2-2h6l2 2h3v12H4V7Zm8 9a4 4 0 1 0 0-8 4 4 0 0 0 0 8Z" /></svg></span>
              <strong>摄像头尚未开启</strong>
              <span>画面只在本机浏览器中显示</span>
            </div>
          </div>

          <p v-if="errorMessage" class="error-message" role="alert">{{ errorMessage }}</p>
          <button v-if="inputMode === 'upload'" class="primary-button" type="button" :disabled="!selectedFile || isDetecting || serviceOnline === false" @click="detectImage">
            <span v-if="isDetecting" class="spinner"></span>
            {{ isDetecting ? '正在识别…' : '开始智能识别' }}
            <svg v-if="!isDetecting" viewBox="0 0 24 24"><path d="m9 18 6-6-6-6" /></svg>
          </button>
          <button v-else class="primary-button" type="button" :disabled="isDetecting || serviceOnline === false" @click="cameraReady ? captureCameraFrame() : startCamera()">
            <span v-if="isDetecting" class="spinner"></span>
            {{ isDetecting ? '正在识别…' : cameraReady ? '识别当前画面' : '开启摄像头' }}
            <svg v-if="!isDetecting" viewBox="0 0 24 24"><path d="m9 18 6-6-6-6" /></svg>
          </button>
        </div>

        <div class="panel result-panel">
          <div class="panel-heading">
            <div><span class="step-number">02</span><h2>识别结果</h2></div>
            <div v-if="result" class="result-actions">
              <a :href="resultImageUrl" target="_blank" rel="noopener">打开结果图</a>
              <span class="complete-badge">识别完成</span>
            </div>
          </div>

          <div v-if="!result" class="empty-state">
            <div class="scan-frame">
              <span></span><span></span><span></span><span></span>
              <svg viewBox="0 0 48 48"><path d="M10 33 20 22l7 7 5-5 6 7M16 17a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z" /></svg>
            </div>
            <strong>等待识别</strong>
            <p>选择图片并开始识别后，检测结果将显示在这里。</p>
          </div>

          <template v-else>
            <div class="result-image-wrap"><img :src="resultImageUrl" alt="带有识别框的结果图片" /></div>
            <div class="metrics">
              <div><strong>{{ result.detection_count }}</strong><span>识别目标</span></div>
              <div><strong>{{ result.vegetation ? `${result.vegetation.coverage_pct.toFixed(1)}%` : '—' }}</strong><span>植被覆盖率</span></div>
              <div><strong>{{ result.inference_ms.toFixed(1) }}</strong><span>推理毫秒</span></div>
              <div><strong>{{ result.width }}×{{ result.height }}</strong><span>图片尺寸</span></div>
            </div>
            <div v-if="result.vegetation" class="vegetation-card">
              <div>
                <span>植被分析</span>
                <strong>{{ result.vegetation.coverage_pct.toFixed(2) }}%</strong>
              </div>
              <p>{{ result.vegetation.method }}，用于 Alpha Demo 展示；正式论文指标后续使用真实标注数据重新计算。</p>
              <a v-if="vegetationImageUrl" :href="vegetationImageUrl" target="_blank" rel="noopener">打开植被叠加图</a>
            </div>
            <div class="detection-list">
              <div v-for="item in groupedDetections" :key="item.name" class="detection-row">
                <div class="detection-name"><span class="class-dot"></span><strong>{{ item.name }}</strong><span>× {{ item.count }}</span></div>
                <div class="confidence"><span :style="{ width: `${item.bestConfidence * 100}%` }"></span></div>
                <strong>{{ (item.bestConfidence * 100).toFixed(1) }}%</strong>
              </div>
            </div>
          </template>
        </div>
      </section>
    </main>

    <footer><span>所有推理均在本机完成</span><span>Forest-AI-Lab · Vision Module</span></footer>
  </div>
</template>
