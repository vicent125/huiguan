#!/bin/bash
# ==================== Systemd服务配置生成脚本 ====================
# 在ECS上执行，创建6个systemd服务

cat > /etc/systemd/system/huiguan-m1.service << 'EOF'
[Unit]
Description=Huiguan M1 - DengluShouyeXietong (Port 5010)
After=network.target

[Service]
Type=exec
User=root
WorkingDirectory=/opt/huiguan/denglu_shouye_xietong/backend
EnvironmentFile=/etc/profile.d/huiguan.sh
ExecStart=/usr/local/bin/gunicorn -w 4 -b 0.0.0.0:5010 --timeout 120 app:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/huiguan-m2a.service << 'EOF'
[Unit]
Description=Huiguan M2a - NongyeGuanli Jiance (Port 5001)
After=network.target

[Service]
Type=exec
User=root
WorkingDirectory=/opt/huiguan/nongyeguanlipingtai/houduan
EnvironmentFile=/etc/profile.d/huiguan.sh
ExecStart=/usr/local/bin/gunicorn -w 4 -b 0.0.0.0:5001 --timeout 120 houduan_shujuluruyujiance:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/huiguan-m2b.service << 'EOF'
[Unit]
Description=Huiguan M2b - NongyeGuanli Jichu (Port 5002)
After=network.target

[Service]
Type=exec
User=root
WorkingDirectory=/opt/huiguan/nongyeguanlipingtai/houduan
EnvironmentFile=/etc/profile.d/huiguan.sh
ExecStart=/usr/local/bin/gunicorn -w 4 -b 0.0.0.0:5002 --timeout 120 houduan_jichuxinxiguanli:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/huiguan-m3.service << 'EOF'
[Unit]
Description=Huiguan M3 - SystemReportWhether (Port 5030)
After=network.target

[Service]
Type=exec
User=root
WorkingDirectory=/opt/huiguan/system_report_whether/backend
EnvironmentFile=/etc/profile.d/huiguan.sh
ExecStart=/usr/local/bin/gunicorn -w 4 -b 0.0.0.0:5030 --timeout 120 app:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/huiguan-m4.service << 'EOF'
[Unit]
Description=Huiguan M4 - YuceFenxiShuifeiJuece (Port 5041)
After=network.target

[Service]
Type=exec
User=root
WorkingDirectory=/opt/huiguan/yucefenxi_shuifeijuece/backend
EnvironmentFile=/etc/profile.d/huiguan.sh
ExecStart=/usr/local/bin/gunicorn -w 4 -b 0.0.0.0:5041 --timeout 120 app:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/huiguan-m5.service << 'EOF'
[Unit]
Description=Huiguan M5 - ZhinengShuifei (Port 5050)
After=network.target

[Service]
Type=exec
User=root
WorkingDirectory=/opt/huiguan/zhineng_shuifei/backend
EnvironmentFile=/etc/profile.d/huiguan.sh
ExecStart=/usr/local/bin/gunicorn -w 4 -b 0.0.0.0:5050 --timeout 120 yingyong:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
echo "6个systemd服务已创建"
echo "启动: systemctl start huiguan-m1 huiguan-m2a huiguan-m2b huiguan-m3 huiguan-m4 huiguan-m5"
echo "开机自启: systemctl enable huiguan-m1 huiguan-m2a huiguan-m2b huiguan-m3 huiguan-m4 huiguan-m5"