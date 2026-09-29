# 慧灌云控 - 华为云部署文件说明

## 文件清单

```
bushu/
├── codearts/
│   └── pipeline.yml              # CodeArts流水线配置（4阶段：后端构建→前端构建→数据库→部署）
├── docker/
│   ├── docker-compose.yml         # Docker Compose一键编排（6后端+Nginx）
│   ├── .env                       # 环境变量配置（需修改为实际值）
│   ├── zhineng_shuifei_Dockerfile          # 模块5 Dockerfile
│   ├── denglu_shouye_xietong_Dockerfile    # 模块1 Dockerfile
│   ├── nongyeguanlipingtai_jiance_Dockerfile  # 模块2a Dockerfile
│   ├── nongyeguanlipingtai_jichu_Dockerfile   # 模块2b Dockerfile
│   ├── system_report_whether_Dockerfile    # 模块3 Dockerfile
│   └── yucefenxi_shuifeijuece_Dockerfile   # 模块4 Dockerfile
├── nginx/
│   └── nginx_huiguan.conf         # Nginx反向代理配置
└── scripts/
    ├── bushu_huanjing.sh          # 环境初始化脚本
    ├── peizhi_systemd.sh          # Systemd服务配置脚本
    ├── yijian_bushu.sh            # 一键部署脚本
    └── yansheng_bushu.sh          # 部署验证脚本
```

## 快速使用

### 方式一：CodeArts流水线（推荐）

1. 将代码推送到CodeArts代码仓库
2. 在CodeArts中创建流水线，导入 `bushu/codearts/pipeline.yml`
3. 配置流水线环境变量：
   - `MYSQL_HOST` / `MYSQL_USER` / `MYSQL_PASSWORD` / `MYSQL_DB`
   - `ECS_IP` / `OBS_BUCKET`
4. 触发流水线自动构建部署

### 方式二：Docker Compose

```bash
cd bushu/docker
# 修改.env中的数据库连接信息
docker-compose up -d --build
```

### 方式三：手动部署

```bash
# 1. 上传bushu/scripts/到ECS
scp -r bushu/scripts/ root@ECS_IP:/opt/huiguan/

# 2. 上传项目代码到ECS
scp -r .arts/ root@ECS_IP:/opt/huiguan/

# 3. SSH登录ECS执行一键部署
ssh root@ECS_IP
cd /opt/huiguan/scripts
chmod +x *.sh
./yijian_bushu.sh

# 4. 验证
./yansheng_bushu.sh
```

## 部署前必须修改的配置

| 文件 | 修改内容 |
|------|---------|
| `docker/.env` | 数据库IP、密码、ECS_IP、OBS桶名 |
| `scripts/bushu_huanjing.sh` | 环境变量中的数据库连接信息 |
| `nginx/nginx_huiguan.conf` | 如有域名，修改server_name |

## 端口映射

| 端口 | 模块 | 说明 |
|------|------|------|
| 80 | Nginx | 对外统一入口 |
| 5010 | denglu_shouye_xietong | 登录首页协同 |
| 5001 | nongyeguanlipingtai | 数据录入与检测 |
| 5002 | nongyeguanlipingtai | 基础信息管理 |
| 5030 | system_report_whether | 系统报表天气 |
| 5041 | yucefenxi_shuifeijuece | 预测分析水肥决策 |
| 5050 | zhineng_shuifei | 智能水肥主模块 |