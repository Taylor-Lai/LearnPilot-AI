# LearnPilot Web

LearnPilot AI 的 Vue 3 前端，覆盖学生画像、个性化路径、多智能体资源生成、智能辅导、学习评估、资源中心和管理后台。

反馈、评测历史、后台任务和平台设置均连接真实后端持久化接口；评测标准答案不会进入浏览器，由 Backend 完成判分。

## 本地开发

```powershell
cd web
npm ci
npm run dev
```

开发服务器默认将 `/api`、`/resources`、`/admin`、`/path`、`/profile`、`/profile-builder` 和 `/producer` 代理到 `http://127.0.0.1:8001`。如需覆盖，复制 `.env.example` 为 `.env.local` 并设置 `VITE_DEV_API_TARGET`。

## 质量检查

```powershell
npm run lint
npm run build
```

生产环境使用 `VITE_API_BASE_URL` 指向后端公开地址。Docker Compose 下由 Nginx 反向代理后端，因此构建时保持该值为空。

## 目录

```text
src/
├─ api/          后端接口适配
├─ components/   通用界面组件
├─ router/       路由与权限守卫
├─ stores/       用户会话状态
├─ styles/       主题与布局样式
├─ utils/        领域数据转换与会话工具
└─ views/        学生端和管理端页面
```

前端只访问 Backend，不直接调用 ML Service。Backend 负责将数据库课程数据和用户画像传给 ML Service，并保持现有页面接口稳定。
