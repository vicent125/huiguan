#!/bin/bash
# ==================== 环境初始化脚本 ====================
# 在ECS上执行，安装所有运行环境

set -e

echo "========== 1. 安装系统依赖 =========="
apt-get update -y
apt-get install -y python3 python3-pip python3-venv nginx mysql-client unzip curl wget git

echo "========== 2. 安装Node.js 18 =========="
if ! command -v node &> /dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
    apt-get install -y nodejs
fi
echo "Node.js版本: $(node -v)"
echo "npm版本: $(npm -v)"

echo "========== 3. 创建项目目录 =========="
mkdir -p /opt/huiguan
mkdir -p /opt/huiguan/frontend/shouye
mkdir -p /opt/huiguan/frontend/denglu
mkdir -p /opt/huiguan/frontend/xietong
mkdir -p /opt/huiguan/frontend/report
mkdir -p /opt/huiguan/frontend/yuce
mkdir -p /opt/huiguan/frontend/nongyeguanlipingtai
mkdir -p /opt/huiguan/frontend/zhineng_shuifei
mkdir -p /etc/nginx/ssl

echo "========== 4. 安装Gunicorn =========="
pip3 install gunicorn

echo "========== 5. 配置环境变量 =========="
cat > /etc/profile.d/huiguan.sh << 'ENVEOF'
# ====== 请修改为实际值 ======
export MYSQL_HOST="172.16.0.123"
export MYSQL_PORT="3306"
export MYSQL_USER="huiguan"
export MYSQL_PASSWORD="YourStrongPassword123!"
export MYSQL_DB="huiguan_yunkong"
export DATABASE_URL="mysql+pymysql://huiguan:YourStrongPassword123!@172.16.0.123:3306/huiguan_yunkong?charset=utf8mb4"
export SHUIFEI_DB="mysql://huiguan:YourStrongPassword123!@172.16.0.123:3306/huiguan_yunkong"
# ============================
ENVEOF
source /etc/profile.d/huiguan.sh
echo "环境变量配置完成: /etc/profile.d/huiguan.sh"

echo "========== 6. 安装obsutil（OBS命令行工具） =========="
if ! command -v obsutil &> /dev/null; then
    wget -q https://obs-community.obs.cn-north-1.myhuaweicloud.com/obsutil/current/obsutil_linux_amd64.tar.gz
    tar xzf obsutil_linux_amd64.tar.gz
    mv obsutil_linux_amd64_*/obsutil /usr/local/bin/
    rm -rf obsutil_linux_amd64*
fi
echo "obsutil安装完成"

echo "========== 环境初始化完成 =========="
echo "请编辑 /etc/profile.d/huiguan.sh 修改数据库连接信息"
echo "然后执行: source /etc/profile.d/huiguan.sh"