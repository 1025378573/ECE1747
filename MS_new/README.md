# 分布式图像处理系统

一个基于master-slave架构的分布式图像处理系统，支持多种负载均衡算法和图像处理方法。

## 系统架构

### 核心组件
1. **Master节点** (`master.py`)
   - 负责任务分发和调度
   - 实现动态任务队列
   - 维护slave节点状态
   - 收集性能数据

2. **Slave节点** (`slave.py`)
   - 接收图像处理任务
   - 执行随机图像处理
   - 返回处理状态

3. **负载均衡器** (`load_balancer.py`)
   - 实现多种负载均衡算法
   - 记录节点性能数据
   - 支持自定义算法

4. **监控系统** (`monitor.py`)
   - 跟踪CPU和内存使用
   - 记录处理时间
   - 生成性能报告

5. **图像处理** (`image_processing.py`)
   - 随机裁剪
   - 添加噪声
   - 实例分割

## 代码逻辑

### 1. 任务分发流程
```
Master节点
↓ 1. 扫描图像目录
↓ 2. 创建任务队列
↓ 3. 启动工作线程
↓ 4. 动态分配任务
↓ 5. 监控处理状态
Slave节点
↓ 1. 等待任务
↓ 2. 接收图像数据
↓ 3. 随机处理
↓ 4. 返回状态
```

### 2. 负载均衡算法
- Round Robin: 轮询分配
- Random: 随机分配
- Least Connections: 最少连接优先
- Weighted Round Robin: 加权轮询
- IP Hash: 基于IP的哈希分配
- Custom: 自定义算法（基于节点性能）

### 3. 运行步骤
终端1：启动第一个slave节点
```bash
python slave.py --host localhost --port 5001
```
终端2：启动第二个slave节点
```bash
python slave.py --host localhost --port 5002
```
终端3：启动第三个slave节点
```bash
python slave.py --host localhost --port 5003
```
终端4：启动master节点
```bash
python master.py --slaves localhost:5001 localhost:5002 localhost:5003 --input images --algorithm round_robin
```

## 注意事项

1. 确保所有端口未被占用
2. 图像目录必须存在且包含图片
3. Slave节点需要先于Master节点启动
4. 支持的图像格式：jpg, png, jpeg