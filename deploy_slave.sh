#!/bin/bash
MASTER_IP=$1
PORT=$2

if [ -z "$MASTER_IP" ] || [ -z "$PORT" ]; then
    echo "使用方法: ./deploy_slave.sh <master_ip> <port>"
    exit 1
fi

echo "正在部署从节点..."

# 安装依赖
pip3 install -r requirements.txt

# 启动从节点
python3 slave.py $MASTER_IP $PORT 