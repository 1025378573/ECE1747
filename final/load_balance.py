class LoadBalancer:
    def __init__(self):
        self.current_index = 0  # 用于Round Robin算法
        self.weighted_count = 0  # 用于Weighted Round Robin的计数器
        
    def round_robin(self, slaves):
        """Round Robin算法"""
        if not slaves:
            return None
            
        # 获取所有slave地址列表并排序，确保顺序一致
        slave_list = sorted(list(slaves.keys()))
        
        if not slave_list:
            return None
            
        # 确保current_index在有效范围内
        if self.current_index >= len(slave_list):
            self.current_index = 0
            
        # 选择当前索引的slave
        selected = slave_list[self.current_index]
        
        # 更新索引，循环使用
        self.current_index = (self.current_index + 1) % len(slave_list)
        
        return selected
    
    def weighted_round_robin(self, slaves):
        """Weighted Round Robin算法"""
        if not slaves:
            return None
            
        # 获取所有slave地址列表并排序
        slave_list = sorted(list(slaves.keys()))
        
        if not slave_list:
            return None
            
        if len(slave_list) < 2:
            return slave_list[0] if slave_list else None
            
        # 第一个节点权重为2，第二个节点权重为1
        if self.weighted_count < 2:
            # 前两次选择第一个节点
            selected = slave_list[0]
            self.weighted_count += 1
        else:
            # 第三次选择第二个节点
            selected = slave_list[1]
            self.weighted_count = 0  # 重置计数器
            
        return selected
    
    def least_loaded(self, slaves):
        """选择空闲线程最多的节点"""
        if not slaves:
            return None
        
        best_node = None
        max_idle_threads = -1
        
        for address, info in slaves.items():
            idle_threads = info['stats']['idle_cpu_threads']
            if idle_threads > max_idle_threads:
                max_idle_threads = idle_threads
                best_node = address
                
        return best_node

    def select_best_node(self, slaves, algorithm='least_loaded'):
        """根据指定的算法选择节点"""
        algorithms = {
            'round_robin': self.round_robin,
            'weighted_round_robin': self.weighted_round_robin,
            'least_loaded': self.least_loaded
        }
        
        if algorithm not in algorithms:
            raise ValueError(f"未知的负载均衡算法: {algorithm}")
            
        return algorithms[algorithm](slaves) 