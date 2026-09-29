#!/bin/bash
# ==================== 一键部署脚本 ====================
# 在ECS上执行，完成从环境初始化到服务启动的全流程

set -e

BASE_DIR="/opt/huiguan"
echo "========== 慧灌云控一键部署开始 =========="

# ====== 1. 环境初始化 ======
echo "========== [1/7] 环境初始化 =========="
bash bushu_huanjing.sh
source /etc/profile.d/huiguan.sh

# ====== 2. 安装Python依赖 ======
echo "========== [2/7] 安装Python依赖 =========="

cd $BASE_DIR/denglu_shouye_xietong/backend
pip3 install -r requirements.txt

cd $BASE_DIR/nongyeguanlipingtai/houduan
pip3 install flask flask_sqlalchemy flask_cors pandas openpyxl pymysql

cd $BASE_DIR/system_report_whether/backend
pip3 install -r requirements.txt

cd $BASE_DIR/yucefenxi_shuifeijuece/backend
pip3 install -r requirements.txt

cd $BASE_DIR/zhineng_shuifei/backend
pip3 install -r requirements.txt

# ====== 3. 数据库建表 ======
echo "========== [3/7] 数据库建表 =========="
mysql -h $MYSQL_HOST -u $MYSQL_USER -p$MYSQL_PASSWORD $MYSQL_DB < $BASE_DIR/zhineng_shuifei/backend/mysql_chushihua.sql
echo "MySQL建表完成"

# ====== 4. 构建Vue前端 ======
echo "========== [4/7] 构建Vue前端 =========="

# 模块1 - shouye
cd $BASE_DIR/denglu_shouye_xietong/frontend/shouye
npm install && npm run build
cp -r dist/* /opt/huiguan/frontend/shouye/

# 模块1 - denglu
cd $BASE_DIR/denglu_shouye_xietong/frontend/denglu
npm install && npm run build
cp -r dist/* /opt/huiguan/frontend/denglu/

# 模块1 - xietong
cd $BASE_DIR/denglu_shouye_xietong/frontend/xietong
npm install && npm run build
cp -r dist/* /opt/huiguan/frontend/xietong/

# 模块3
cd $BASE_DIR/system_report_whether/frontend
npm install && npm run build
cp -r dist/* /opt/huiguan/frontend/report/

# 模块4
cd $BASE_DIR/yucefenxi_shuifeijuece/frontend
npm install && npm run build
cp -r dist/* /opt/huiguan/frontend/yuce/

# ====== 5. 部署原生HTML前端 ======
echo "========== [5/7] 部署原生HTML前端 =========="
cp -r $BASE_DIR/nongyeguanlipingtai/index.html /opt/huiguan/frontend/nongyeguanlipingtai/
cp -r $BASE_DIR/nongyeguanlipingtai/jiankong.html /opt/huiguan/frontend/nongyeguanlipingtai/
cp -r $BASE_DIR/nongyeguanlipingtai/js /opt/huiguan/frontend/nongyeguanlipingtai/
cp -r $BASE_DIR/zhineng_shuifei/web/* /opt/huiguan/frontend/zhineng_shuifei/

# ====== 6. 配置Systemd + Nginx ======
echo "========== [6/7] 配置Systemd和Nginx =========="
bash peizhi_systemd.sh
cp nginx_huiguan.conf /etc/nginx/conf.d/default.conf
nginx -t
systemctl enable huiguan-m1 huiguan-m2a huiguan-m2b huiguan-m3 huiguan-m4 huiguan-m5
systemctl start huiguan-m1 huiguan-m2a huiguan-m2b huiguan-m3 huiguan-m4 huiguan-m5
systemctl reload nginx

# ====== 7. 验证 ======
echo "========== [7/7] 部署验证 =========="
sleep 3
for port in 5010 5001 5002 5030 5041 5050; do
    if ss -tlnp | grep -q ":$port "; then
        echo "[OK] 端口 $port 监听中"
    else
        echo "[FAIL] 端口 $port 未监听"
    fi
done

echo ""
echo "========== 部署完成 =========="
echo "访问地址: http://$(curl -s ifconfig.me)/"
echo "服务状态: systemctl status huiguan-m1 huiguan-m2a huiguan-m2b huiguan-m3 huiguan-m4 huiguan-m5"