# 分布式图像处理系统

## 项目概述
这是一个基于master-slave架构的分布式图像处理系统。系统通过socket通信,实现了多节点的任务分发和处理。

## 系统架构

### Master节点
- 负责生成和分发任务
- 维护slave节点的状态信息 
- 调用负载均衡算法分配任务
- 统计任务完成情况和处理时间

### Slave节点
- 自动连接到master节点
- 定期发送心跳信息
- 多线程处理图像任务
- 统计本地任务处理情况

## 功能特性

### 负载均衡算法
1. Round Robin
   - 轮询方式分配任务
   - 保证任务均匀分配

2. Weighted Round Robin  
   - 基于权重的轮询
   - 第一个节点处理2个任务
   - 第二个节点处理1个任务

3. Least Loaded
   - 选择空闲线程最多的节点
   - 基于CPU使用率动态分配

### 图像处理任务
- 高斯模糊处理
- 边缘检测
- 颜色量化

## 运行流程

### 启动流程
1. Master节点启动
   - 生成1000个随机图像处理任务
   - 等待slave连接
   - 开始任务分发

2. Slave节点启动
   - 尝试连接master
   - 连接失败则定期重试
   - 成功后启动心跳线程
   - 接收任务并处理

### 任务处理
- Master根据选定的负载均衡算法分发任务
- Slave接收任务并创建新线程处理
- 处理完成后通知master

### 状态监控
- Master显示任务分发和完成进度
- Slave显示本地任务处理统计
- 系统显示总体处理时间和效率

## 使用方法

### 启动Master
```bash
python master.py --lb_algorithm <algorithm>
```

### 不同节点上启动Slave
```bash
python slave.py
```

## EC2集群
- 使用AWS EC2创建3个t3.small实例
- 在master节点上运行master.py
- 在slave节点上运行slave.py

