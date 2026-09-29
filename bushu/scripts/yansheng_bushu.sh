#!/bin/bash
# ==================== 部署验证脚本 ====================

echo "========== 慧灌云控部署验证 =========="

# 1. 检查服务状态
echo "========== [1/4] 服务状态 =========="
services=("huiguan-m1" "huiguan-m2a" "huiguan-m2b" "huiguan-m3" "huiguan-m4" "huiguan-m5")
ports=("5010" "5001" "5002" "5030" "5041" "5050")
all_ok=true

for i in ${!services[@]}; do
    status=$(systemctl is-active ${services[$i]})
    if [ "$status" = "active" ]; then
        echo "[OK] ${services[$i]} (端口 ${ports[$i]})"
    else
        echo "[FAIL] ${services[$i]} (端口 ${ports[$i]}) - $status"
        all_ok=false
    fi
done

# 2. 检查端口监听
echo ""
echo "========== [2/4] 端口监听 =========="
for port in 5010 5001 5002 5030 5041 5050; do
    if ss -tlnp | grep -q ":$port "; then
        echo "[OK] 端口 $port"
    else
        echo "[FAIL] 端口 $port"
        all_ok=false
    fi
done

# 3. 测试API接口
echo ""
echo "========== [3/4] API接口测试 =========="

# 模块5
if curl -s http://127.0.0.1:5050/api/zonglan | grep -q "code"; then
    echo "[OK] 5050 /api/zonglan"
else
    echo "[FAIL] 5050 /api/zonglan"
    all_ok=false
fi

if curl -s http://127.0.0.1:5050/api/jichu/zuowu | grep -q "code"; then
    echo "[OK] 5050 /api/jichu/zuowu"
else
    echo "[FAIL] 5050 /api/jichu/zuowu"
    all_ok=false
fi

if curl -s http://127.0.0.1:5050/api/tianqi | grep -q "code"; then
    echo "[OK] 5050 /api/tianqi"
else
    echo "[FAIL] 5050 /api/tianqi"
    all_ok=false
fi

# 模块1
if curl -s http://127.0.0.1:5010/ | grep -q "code"; then
    echo "[OK] 5010 /"
else
    echo "[FAIL] 5010 /"
    all_ok=false
fi

# 模块3
if curl -s http://127.0.0.1:5030/api/health | grep -q "code"; then
    echo "[OK] 5030 /api/health"
else
    echo "[FAIL] 5030 /api/health"
    all_ok=false
fi

# 模块4
if curl -s http://127.0.0.1:5041/ | grep -q "code"; then
    echo "[OK] 5041 /"
else
    echo "[FAIL] 5041 /"
    all_ok=false
fi

# 模块2
if curl -s http://127.0.0.1:5002/api/zuowuguanli | grep -q "code"; then
    echo "[OK] 5002 /api/zuowuguanli"
else
    echo "[FAIL] 5002 /api/zuowuguanli"
    all_ok=false
fi

# 4. 检查Nginx
echo ""
echo "========== [4/4] Nginx状态 =========="
if systemctl is-active nginx | grep -q "active"; then
    echo "[OK] Nginx运行中"
else
    echo "[FAIL] Nginx未运行"
    all_ok=false
fi

# 总结
echo ""
echo "=========================================="
if $all_ok; then
    echo "所有验证通过！部署成功！"
    echo "访问地址: http://$(curl -s ifconfig.me 2>/dev/null || echo '服务器IP')/"
else
    echo "部分验证失败，请检查上述[FAIL]项"
fi
echo "=========================================="