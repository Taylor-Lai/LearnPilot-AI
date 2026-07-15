# LearnPilot Web

Web 是 Vue 3 单页应用，提供学生画像、学习路径、多智能体资源生成、资源中心、智能辅导、学习评估和管理后台。前端只访问 Backend，不直接调用 ML Service，也不在浏览器中保存评测标准答案或服务密钥。

## 代码结构

```text
web/
├─ src/
│  ├─ api/          Backend 接口适配
│  ├─ components/   通用界面组件
│  ├─ router/       路由与权限守卫
│  ├─ stores/       用户会话状态
│  ├─ styles/       主题、令牌与布局
│  ├─ utils/        领域数据转换
│  └─ views/        学生端和管理端页面
├─ public/          静态资源
├─ nginx.conf       Docker 同源反向代理
└─ package.json     依赖与命令
```

## 本地开发

```powershell
cd web
npm ci
npm run dev
```

开发地址默认是 <http://127.0.0.1:5173>。Vite 将业务请求代理到 `http://127.0.0.1:8001`；如需修改，复制 `.env.example` 为 `.env.local` 并设置 `VITE_DEV_API_TARGET`。

Docker Compose 使用 Nginx 将 `/api`、`/resources`、`/admin`、`/path`、`/profile`、`/profile-builder` 和 `/producer` 同源代理到 Backend，因此 `VITE_API_BASE_URL` 保持为空。

## 验证

```powershell
npm run lint
npm run build
```

接口定义见[统一 API 参考](../docs/api-reference.md)，整体服务边界见[工程架构](../docs/architecture.md)。
