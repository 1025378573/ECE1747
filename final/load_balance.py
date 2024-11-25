class LoadBalancer:
    @staticmethod
    def select_best_node(slaves):
        if not slaves:
            return None
        
        # 根据空闲线程数选择最佳节点
        best_node = None
        max_idle_threads = -1
        
        for address, info in slaves.items():
            idle_threads = info['stats']['idle_cpu_threads']
            if idle_threads > max_idle_threads:
                max_idle_threads = idle_threads
                best_node = address
                
        return best_node 