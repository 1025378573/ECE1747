#!/bin/bash
echo "正在部署主节点..."

# 安装依赖
pip3 install -r requirements.txt

# 启动主节点
python3 master.py 