import random
from collections import defaultdict

class LoadBalancer:
    def __init__(self):
        self.algorithms = {
            'round_robin': self.round_robin,
            'random': self.random_distribution,
            'least_connections': self.least_connections,
            'weighted_round_robin': self.weighted_round_robin,
            'ip_hash': self.ip_hash,
            'custom': self.custom_algorithm
        }
        self.current_index = 0
        self.connections = defaultdict(int)
        self.node_performance = defaultdict(list)
        
    def round_robin(self, tasks, slaves):
        """轮询算法"""
        distributed_tasks = defaultdict(list)
        for i, task in enumerate(tasks):
            slave_index = (i + self.current_index) % len(slaves)
            slave = slaves[slave_index]  # 获取实际的slave节点
            distributed_tasks[slave].append(task)
            print(f"分配任务 {task} 到节点 {slave}")  # 调试信息
            
        self.current_index = (self.current_index + len(tasks)) % len(slaves)
        
        # 打印任务分配情况
        for slave, tasks in distributed_tasks.items():
            print(f"节点 {slave} 分配到 {len(tasks)} 个任务")
            
        return distributed_tasks

    def random_distribution(self, tasks, slaves):
        """随机分配算法"""
        distributed_tasks = defaultdict(list)
        for task in tasks:
            slave = random.choice(slaves)
            distributed_tasks[slave].append(task)
            print(f"分配任务 {task} 到节点 {slave}")  # 调试信息
        return distributed_tasks

    def least_connections(self, tasks, slaves):
        """最少连接数算法"""
        distributed_tasks = defaultdict(list)
        for task in tasks:
            slave = min(slaves, key=lambda s: self.connections[s])
            distributed_tasks[slave].append(task)
            self.connections[slave] += 1
            print(f"分配任务 {task} 到节点 {slave}")  # 调试信息
        return distributed_tasks

    def weighted_round_robin(self, tasks, slaves, weights=None):
        """加权轮询算法"""
        if weights is None:
            weights = [1] * len(slaves)
        
        distributed_tasks = defaultdict(list)
        total_weight = sum(weights)
        
        for task in tasks:
            slave_index = (self.current_index) % total_weight
            for i, weight in enumerate(weights):
                if slave_index < weight:
                    distributed_tasks[slaves[i]].append(task)
                    print(f"分配任务 {task} 到节点 {slaves[i]}")  # 调试信息
                    break
                slave_index -= weight
            self.current_index = (self.current_index + 1) % total_weight
        
        return distributed_tasks

    def ip_hash(self, tasks, slaves):
        """IP哈希算法"""
        distributed_tasks = defaultdict(list)
        for task in tasks:
            hash_value = hash(task)
            slave_index = hash_value % len(slaves)
            slave = slaves[slave_index]
            distributed_tasks[slave].append(task)
            print(f"分配任务 {task} 到节点 {slave}")  # 调试信息
        return distributed_tasks

    def custom_algorithm(self, tasks, slaves):
        """
        自定义负载均衡算法
        可以根据需要实现自己的逻辑，例如：
        - 基于节点的历史处理时间
        - 基于节点的当前负载
        - 基于任务的特征
        """
        distributed_tasks = defaultdict(list)
        
        # 这里实现你的算法逻辑
        # 例如：基于节点的平均处理时间分配任务
        for task in tasks:
            # 获取性能最好的节点
            if self.node_performance:
                # 计算每个节点的平均处理时间
                avg_times = {
                    node: sum(times)/len(times) if times else float('inf')
                    for node, times in self.node_performance.items()
                }
                # 选择平均处理时间最短的节点
                selected_slave = min(avg_times.items(), key=lambda x: x[1])[0]
            else:
                # 如果没有性能数据，随机选择节点
                selected_slave = random.choice(slaves)
            
            distributed_tasks[selected_slave].append(task)
            print(f"分配任务 {task} 到节点 {selected_slave}")
            
        return distributed_tasks

    def update_node_performance(self, node, processing_time):
        """更新节点性能记录"""
        self.node_performance[node].append(processing_time)
        # 只保留最近的10个记录
        if len(self.node_performance[node]) > 10:
            self.node_performance[node].pop(0)

    def distribute_tasks(self, algorithm_name, tasks, slaves):
        """使用指定的算法分配任务"""
        if not tasks:
            raise ValueError("没有任务需要分配")
        if not slaves:
            raise ValueError("没有可用的从节点")
            
        print(f"\n使用算法 {algorithm_name} 分配 {len(tasks)} 个任务到 {len(slaves)} 个节点")
        
        if algorithm_name not in self.algorithms:
            raise ValueError(f"未知的算法: {algorithm_name}")
            
        return self.algorithms[algorithm_name](tasks, slaves)

    # 其他负载均衡算法的实现... 