# AI Knowledge Hub — 部署指南

本文档指导你将项目部署到云服务器，通过 Docker Compose 一键运行。

***

## 架构概览

```
用户浏览器 → Nginx (80端口)
                ├── /api/* → FastAPI 后端 (8000)
                └── /*     → Nuxt 前端 SSR (3000)
```

三个 Docker 容器：

- **nginx** — 反向代理，统一入口

- **backend** — FastAPI + APScheduler，数据拉取

- **frontend** — Nuxt 4 SSR 服务

***

## 第一步：购买云服务器

### 推荐配置

| 配置项 | 最低要求             | 推荐               |
| --- | ---------------- | ---------------- |
| CPU | 1 核              | 2 核              |
| 内存  | 1 GB             | 2 GB             |
| 硬盘  | 20 GB            | 40 GB SSD        |
| 带宽  | 1 Mbps           | 3-5 Mbps         |
| 系统  | Ubuntu 22.04 LTS | Ubuntu 22.04 LTS |

### 推荐平台

| 平台                                                         | 价格         | 特点         |
| ---------------------------------------------------------- | ---------- | ---------- |
| [阿里云轻量应用服务器](https://www.aliyun.com/product/swas)          | \~24-60元/月 | 国内速度快，备案方便 |
| [腾讯云轻量应用服务器](https://cloud.tencent.com/product/lighthouse) | \~24-60元/月 | 经常有新人优惠    |
| [雨云(RainYun)](https://www.rainyun.com)                     | \~15-30元/月 | 小众但性价比高    |

> **建议**：选择**国内节点**（如北京、上海、广州），访问速度快。国内服务器绑定域名需要备案。

### 购买后操作

1. 记下服务器**公网 IP**（如 `123.45.67.89`）
2. 在云控制台→安全组/防火墙→开放端口：

   - **80**（HTTP）

   - **443**（HTTPS，后续配 SSL 用）

   - **22**（SSH，一般默认开放）
3. 设置 SSH 密码或上传密钥

***

## 第二步：注册域名

### 推荐注册商

| 注册商                                      | .com 价格 | 特点                |
| ---------------------------------------- | ------- | ----------------- |
| [阿里云万网](https://wanwang.aliyun.com)      | \~55元/年 | 国内大厂，备案方便         |
| [腾讯云](https://dnspod.cloud.tencent.com)  | \~55元/年 | 经常有优惠             |
| [Cloudflare](https://www.cloudflare.com) | \~$9/年  | 国际大厂，自带 CDN 和 DNS |
| [NameSilo](https://www.namesilo.com)     | \~$9/年  | 便宜，免费隐私保护         |

### 域名选择建议

- `.com` 优先，通用且专业

- `.dev`、`.ai`、`.tech` 也可以，但价格较高

- 简短好记，与 AI 知识相关，如 `aiknowledge.com`、`aihub.dev`

### 域名备案（仅国内服务器需要）

如果服务器在国内（阿里云/腾讯云），域名必须完成 ICP 备案：

1. 在云控制台找到"ICP 备案"
2. 提交身份证、域名、服务器信息
3. 通常 7-20 个工作日
4. 备案通过后才能正常访问 80/443 端口

> **不想备案？** 购买**海外服务器**（如香港、新加坡节点），无需备案即可使用，但国内访问速度稍慢。

***

## 第三步：DNS 解析配置

在域名注册商的 DNS 管理页面，添加 A 记录：

| 记录类型 | 主机记录 | 记录值     | TTL |
| ---- | ---- | ------- | --- |
| A    | @    | 你的服务器IP | 600 |
| A    | www  | 你的服务器IP | 600 |

> `@` 表示根域名，`www` 表示带 www 前缀。两个都加，确保都能访问。

配置完成后等待 DNS 生效（通常几分钟到几小时）。可用以下命令验证：

```bash
# 在本地电脑执行
nslookup 你的域名.com
# 或
ping 你的域名.com
```

***

## 第四步：安装 Docker（在服务器上）

SSH 连接到服务器后执行：

```bash
# ── 安装 Docker ──
curl -fsSL https://get.docker.com | sh

# ── 启动 Docker 并设置开机自启 ──
systemctl start docker
systemctl enable docker

# ── 验证安装 ──
docker --version
docker compose version
```

> 如果 curl 下载慢，可用国内镜像：
>
> ```bash
> curl -fsSL https://get.docker.com | sh -s docker --mirror Aliyun
> ```

***

## 第五步：部署项目

### 1. 拉取代码

```bash
cd /opt
git clone https://github.com/homelore/ai-knowledge-hub.git
cd ai-knowledge-hub
```

> 如果 GitHub 下载慢，可用代理或手动上传代码包。

### 2. 配置环境变量

```bash
cp .env.example .env
nano .env
```

修改 `.env` 文件：

```env
# 填入你的 GitHub Token（提高 API 限额）
GITHUB_TOKEN=ghp_你的token

# 开启定时拉取
SCHEDULER_ENABLED=true

# CORS（同域名下不需要，留着默认即可）
CORS_ORIGINS=http://localhost:3000
```

### 3. 一键启动

```bash
docker compose up -d --build
```

首次构建约 5-10 分钟（需下载镜像和安装依赖）。构建完成后：

```bash
# 查看运行状态
docker compose ps

# 查看日志
docker compose logs -f

# 确认各服务正常
curl http://localhost/api/health
# 应返回 {"status":"ok","service":"ai-knowledge-hub"}
```

### 4. 触发首次数据拉取

```bash
curl -X POST http://localhost/api/agent/fetch
```

等待 1-2 分钟，然后访问 `http://你的域名` 或 `http://服务器IP` 即可看到网站。

***

## 第六步：配置 HTTPS（强烈建议）

使用免费的 Let's Encrypt 证书，通过 acme.sh 一键申请：

### 1. 安装 acme.sh

```bash
curl https://get.acme.sh | sh
source ~/.bashrc
```

### 2. 申请证书

```bash
# 将 your-domain.com 换成你的实际域名
acme.sh --issue -d your-domain.com -d www.your-domain.com --standalone
```

> 申请前确保 80 端口没有被 Nginx 占用，或先停止 Nginx：
>
> ```bash
> docker compose stop nginx
> ```
>
> 申请完再启动。

### 3. 安装证书

```bash
mkdir -p /opt/ssl
acme.sh --install-cert -d your-domain.com \
  --key-file /opt/ssl/key.pem \
  --fullchain-file /opt/ssl/cert.pem \
  --reloadcmd "docker compose -f /opt/ai-knowledge-hub/docker-compose.yml restart nginx"
```

### 4. 更新 Nginx 配置支持 HTTPS

编辑 `nginx/nginx.conf`，替换为：

```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    # HTTP 跳转 HTTPS
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name your-domain.com www.your-domain.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;

    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml text/javascript image/svg+xml;
    gzip_min_length 1000;
    gzip_vary on;

    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location / {
        proxy_pass http://frontend:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### 5. 更新 docker-compose.yml 挂载证书

在 `docker-compose.yml` 的 nginx 服务中添加 SSL 卷挂载和 443 端口：

```yaml
  nginx:
    image: nginx:alpine
    container_name: ai-hub-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/conf.d/default.conf:ro
      - /opt/ssl:/etc/nginx/ssl:ro
    depends_on:
      - backend
      - frontend
    restart: unless-stopped
    networks:
      - ai-hub-net
```

### 6. 重启 Nginx

```bash
docker compose up -d nginx
```

访问 `https://你的域名` 即可。

> acme.sh 会自动续期证书（60天一次），无需手动操作。

***

## 日常运维命令

```bash
# ── 查看服务状态 ──
docker compose ps

# ── 查看实时日志 ──
docker compose logs -f                    # 所有服务
docker compose logs -f backend             # 只看后端
docker compose logs -f frontend            # 只看前端

# ── 重启服务 ──
docker compose restart                     # 重启所有
docker compose restart backend             # 只重启后端

# ── 停止/启动 ──
docker compose down                        # 停止并删除容器
docker compose up -d                       # 重新启动

# ── 更新代码 ──
git pull
docker compose up -d --build              # 重新构建并启动

# ── 手动触发数据拉取 ──
curl -X POST http://localhost/api/agent/fetch

# ── 进入后端容器调试 ──
docker compose exec backend bash

# ── 查看数据库 ──
docker compose exec backend python -c "
from models.database import get_db_session
from models.repo import Repo
with get_db_session() as s:
    print(f'仓库总数: {s.query(Repo).count()}')
"
```

***

## 数据备份

### 备份数据库

```bash
# 备份到 /opt/backup/
docker compose exec backend cp /app/backend/data/ai_hub.db /dev/stdout > /opt/backup/ai_hub_$(date +%Y%m%d).db

# 自动备份（加到 crontab）
echo "0 2 * * * docker compose -f /opt/ai-knowledge-hub/docker-compose.yml exec -T backend cat /app/backend/data/ai_hub.db > /opt/backup/ai_hub_\$(date +\%Y\%m\%d).db" | crontab -
```

### 恢复数据库

```bash
docker compose stop backend
docker cp /opt/backup/ai_hub_20260903.db ai-hub-backend:/app/backend/data/ai_hub.db
docker compose start backend
```

***

## 常见问题

### Q: 构建很慢怎么办？

```bash
# 配置 Docker 国内镜像加速
mkdir -p /etc/docker
cat > /etc/docker/daemon.json << 'EOF'
{
  "registry-mirrors": ["https://mirror.ccs.tencentyun.com"]
}
EOF
systemctl restart docker
```

### Q: GitHub 拉取代码慢？

```bash
# 使用代理或镜像
git clone https://ghproxy.com/https://github.com/homelore/ai-knowledge-hub.git
```

### Q: Agent 拉取 GitHub 数据失败？

- 检查 `.env` 中 `GITHUB_TOKEN` 是否正确

- 查看 `docker compose logs backend` 排查

- 无 Token 时限额 60/h，可能被限流

### Q: 内存不够怎么办？

```bash
# 添加 swap
fallocate -l 1G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab
```

### Q: 如何修改前端代码后更新？

```bash
# 在服务器上
cd /opt/ai-knowledge-hub
git pull
docker compose up -d --build frontend
```

