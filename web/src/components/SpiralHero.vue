<template>
  <section
    ref="heroRef"
    class="hero"
    @pointermove="handlePointerMove"
    @pointerleave="handlePointerLeave"
  >
    <canvas ref="canvasRef" class="hero-canvas"></canvas>

    <div class="hero-content">
      <p class="eyebrow">
        INTELLIGENT COLLABORATION PLATFORM
      </p>

      <h1>汇知灵创</h1>

      <p class="description">
        用自然的知识组织方式，把内容、协作和知识沉淀放在同一个空间里。
      </p>

      <div class="actions">
        <RouterLink
          class="primary-action"
          to="/guide"
        >
          快速上手
        </RouterLink>

        <RouterLink
          class="secondary-action"
          to="/feedback"
        >
          我要反馈
        </RouterLink>
      </div>
    </div>
  </section>
</template>

<script setup>
import {
  onBeforeUnmount,
  onMounted,
  ref,
} from 'vue'

import { RouterLink } from 'vue-router'

const heroRef = ref(null)
const canvasRef = ref(null)

let ctx = null
let width = 0
let height = 0
let dpr = 1
let animationFrameId = 0
let resizeObserver = null

const pointer = {
  x: 0.5,
  y: 0.5,
  tx: 0.5,
  ty: 0.5,
}

const points = []

const ROWS = 14
const COLS = 34

const GAP_X = 66
const GAP_Z = 64

function resizeCanvas() {
  if (
    !canvasRef.value ||
    !heroRef.value
  ) {
    return
  }

  const rect =
    heroRef.value.getBoundingClientRect()

  width = rect.width
  height = rect.height

  dpr =
    window.devicePixelRatio || 1

  canvasRef.value.width =
    width * dpr

  canvasRef.value.height =
    height * dpr

  canvasRef.value.style.width =
    `${width}px`

  canvasRef.value.style.height =
    `${height}px`

  ctx =
    canvasRef.value.getContext(
      '2d',
    )

  ctx.setTransform(
    dpr,
    0,
    0,
    dpr,
    0,
    0,
  )

  generateTerrain()
}

function generateTerrain() {
  points.length = 0

  const totalWidth =
    (COLS - 1) * GAP_X

  const startX =
    width * 0.62 -
    totalWidth / 2

  for (
    let row = 0;
    row < ROWS;
    row += 1
  ) {
    const rowPoints = []

    for (
      let col = 0;
      col < COLS;
      col += 1
    ) {
      const x =
        startX + col * GAP_X

      const z =
        row * GAP_Z

      const y =
        Math.sin(
          col * 0.34 +
            row * 0.18,
        ) *
          18 +
        Math.cos(row * 0.72) *
          10 +
        Math.sin(col * 0.12) *
          6

      rowPoints.push({
        x,
        y,
        z,
        baseY: y,
      })
    }

    points.push(rowPoints)
  }
}

function project(point) {
  const rotateY =
    (pointer.x - 0.5) * 0.28

  const rotateX =
    1.03 +
    (pointer.y - 0.5) * 0.08

  const dx =
    point.x - width / 2

  const dy = point.y

  const dz =
    point.z - 360

  const cosY =
    Math.cos(rotateY)

  const sinY =
    Math.sin(rotateY)

  const rx =
    dx * cosY -
    dz * sinY

  const rz =
    dx * sinY +
    dz * cosY

  const cosX =
    Math.cos(rotateX)

  const sinX =
    Math.sin(rotateX)

  const ry =
    dy * cosX -
    rz * sinX

  const finalZ =
    dy * sinX +
    rz * cosX

  const perspective =
    1200 / (1200 + finalZ)

  return {
    x:
      width / 2 +
      rx * perspective,

    y:
      height * 0.53 +
      ry * perspective,

    scale: perspective,
  }
}

function drawBackground() {
  const gradient =
    ctx.createLinearGradient(
      0,
      0,
      0,
      height,
    )

  gradient.addColorStop(
    0,
    '#2d3550',
  )

  gradient.addColorStop(
    0.48,
    '#283149',
  )

  gradient.addColorStop(
    1,
    '#222a3e',
  )

  ctx.fillStyle = gradient

  ctx.fillRect(
    0,
    0,
    width,
    height,
  )

  ctx.strokeStyle =
    'rgba(87, 150, 220, 0.08)'

  ctx.lineWidth = 1

  for (
    let x = -80;
    x <= width + 120;
    x += 74
  ) {
    ctx.beginPath()

    ctx.moveTo(
      x +
        (pointer.x - 0.5) *
          10,
      0,
    )

    ctx.lineTo(
      x -
        150 +
        (pointer.x - 0.5) *
          20,
      height,
    )

    ctx.stroke()
  }
}

function drawTerrain() {
  const projected = []

  for (
    let row = 0;
    row < ROWS;
    row += 1
  ) {
    projected[row] = []

    for (
      let col = 0;
      col < COLS;
      col += 1
    ) {
      projected[row][col] =
        project(
          points[row][col],
        )
    }
  }

  for (
    let row = 0;
    row < ROWS;
    row += 1
  ) {
    ctx.beginPath()

    for (
      let col = 0;
      col < COLS;
      col += 1
    ) {
      const p =
        projected[row][col]

      if (col === 0) {
        ctx.moveTo(
          p.x,
          p.y,
        )
      } else {
        ctx.lineTo(
          p.x,
          p.y,
        )
      }
    }

    const alpha =
      0.12 + row * 0.013

    ctx.strokeStyle = `rgba(71,214,248,${alpha})`

    ctx.lineWidth =
      1 + row * 0.03

    ctx.stroke()
  }

  for (
    let col = 0;
    col < COLS;
    col += 1
  ) {
    ctx.beginPath()

    for (
      let row = 0;
      row < ROWS;
      row += 1
    ) {
      const p =
        projected[row][col]

      if (row === 0) {
        ctx.moveTo(
          p.x,
          p.y,
        )
      } else {
        ctx.lineTo(
          p.x,
          p.y,
        )
      }
    }

    ctx.strokeStyle =
      'rgba(71,214,248,0.14)'

    ctx.lineWidth = 1

    ctx.stroke()
  }

  for (
    let row = 0;
    row < ROWS;
    row += 1
  ) {
    for (
      let col = 0;
      col < COLS;
      col += 1
    ) {
      const p =
        projected[row][col]

      const size =
        0.85 + row * 0.045

      ctx.beginPath()

      ctx.fillStyle =
        'rgba(118,241,255,0.82)'

      ctx.arc(
        p.x,
        p.y,
        size,
        0,
        Math.PI * 2,
      )

      ctx.fill()
    }
  }

  drawLeftDots()
}

function drawLeftDots() {
  const centerX =
    width * 0.08

  const centerY =
    height * 0.5

  for (
    let i = 0;
    i < 34;
    i += 1
  ) {
    const t = i / 33

    const angle =
      Math.PI *
      (0.72 + t * 0.7)

    const x =
      centerX +
      Math.cos(angle) *
        width *
        0.16 +
      (pointer.x - 0.5) *
        12

    const y =
      centerY +
      Math.sin(angle) *
        height *
        0.3 +
      (pointer.y - 0.5) *
        10

    ctx.beginPath()

    ctx.fillStyle = `rgba(98,232,255,${0.2 + t * 0.45})`

    ctx.arc(
      x,
      y,
      1 + (i % 3) * 0.3,
      0,
      Math.PI * 2,
    )

    ctx.fill()
  }
}

function animateTerrain(time) {
  for (
    let row = 0;
    row < ROWS;
    row += 1
  ) {
    for (
      let col = 0;
      col < COLS;
      col += 1
    ) {
      const point =
        points[row][col]

      point.y =
        point.baseY +
        Math.sin(
          time * 0.00085 +
            col * 0.38 +
            row * 0.1,
        ) *
          7 +
        Math.cos(
          time * 0.0007 +
            row * 0.46,
        ) *
          5
    }
  }
}

function render(time = 0) {
  if (!ctx) {
    return
  }

  pointer.x +=
    (pointer.tx -
      pointer.x) *
    0.05

  pointer.y +=
    (pointer.ty -
      pointer.y) *
    0.05

  ctx.clearRect(
    0,
    0,
    width,
    height,
  )

  drawBackground()

  animateTerrain(time)

  drawTerrain()

  animationFrameId =
    requestAnimationFrame(
      render,
    )
}

function handlePointerMove(event) {
  if (!heroRef.value) {
    return
  }

  const rect =
    heroRef.value.getBoundingClientRect()

  pointer.tx =
    (event.clientX -
      rect.left) /
    rect.width

  pointer.ty =
    (event.clientY -
      rect.top) /
    rect.height
}

function handlePointerLeave() {
  pointer.tx = 0.5
  pointer.ty = 0.5
}

onMounted(() => {
  resizeCanvas()

  render()

  resizeObserver =
    new ResizeObserver(() => {
      resizeCanvas()
    })

  if (heroRef.value) {
    resizeObserver.observe(
      heroRef.value,
    )
  }
})

onBeforeUnmount(() => {
  if (animationFrameId) {
    cancelAnimationFrame(
      animationFrameId,
    )
  }

  if (resizeObserver) {
    resizeObserver.disconnect()
  }
})
</script>

<style scoped>
.hero {
  position: relative;
  width: 100%;
  min-height: clamp(420px, 72vh, 680px);
  background: #263149;
  overflow: hidden;
}

.hero-canvas {
  position: absolute;
  inset: 0;
  display: block;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.hero-content {
  position: relative;
  z-index: 1;
  width: min(100%, 860px);
  min-height: clamp(420px, 72vh, 680px);
  margin: 0 auto;
  padding: 48px 24px 56px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  box-sizing: border-box;
}

.eyebrow {
  margin-bottom: 16px;
  color: rgba(220, 230, 255, 0.72);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.22em;
  text-transform: uppercase;
}

h1 {
  margin: 0 0 18px;
  color: #ffffff;
  font-size: clamp(40px, 7vw, 88px);
  font-weight: 700;
  line-height: 1.08;
  letter-spacing: 0.02em;
  word-break: break-word;
}

.description {
  max-width: 620px;
  color: rgba(226, 235, 248, 0.78);
  font-size: clamp(14px, 2vw, 16px);
  line-height: 1.85;
  text-align: center;
}

.actions {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  gap: 14px;
  margin-top: 30px;
  width: 100%;
}

.primary-action,
.secondary-action {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 138px;
  min-height: 48px;
  padding: 0 24px;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 700;
  text-decoration: none;
  transition: transform 0.25s ease, background 0.25s ease, border-color 0.25s ease;
}

.primary-action {
  color: #ffffff;
  background: #5c4cff;
}

.primary-action:hover {
  transform: translateY(-2px);
  background: #5344ef;
}

.secondary-action {
  color: #ffffff;
  border: 1px solid rgba(255, 255, 255, 0.14);
  background: rgba(255, 255, 255, 0.05);
}

.secondary-action:hover {
  transform: translateY(-2px);
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.18);
}

@media (max-width: 768px) {
  .hero,
  .hero-content {
    min-height: auto;
  }

  .hero-content {
    padding: 36px 16px 40px;
  }

  .actions {
    flex-direction: column;
  }

  .primary-action,
  .secondary-action {
    width: 100%;
    max-width: 280px;
  }
}
</style>