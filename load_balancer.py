import random
import time
import socket
import json

class LoadBalancer:
    def __init__(self):
        self.current_index = 0 
        
    def round_robin(self, slaves):
        if not slaves:
            return None
        selected = slaves[self.current_index]
        self.current_index = (self.current_index + 1) % len(slaves)
        return selected
        
    def least_connections(self, slaves):
        if not slaves:
            return None
        return min(slaves, key=lambda x: x['tasks'])
        
    def random_selection(self, slaves):
        if not slaves:
            return None
        return random.choice(slaves)
        
    def weighted_response_time(self, slaves):
        """
        基于响应时间的加权选择算法
        
        工作流程：
        1. 计算每个节点的权重: weight = 1/(response_time + 0.1)
           - response_time 越小，权重越大
           - +0.1 是为了避免除以零
        
        2. 归一化权重: normalized_weight = weight/total_weight
           - 使所有权重之和为1
        
        3. 按照归一化后的权重随机选择节点
        """
        if not slaves:
            return None

        # 计算每个节点的权重
        weights = []
        for slave in slaves:
            response_time = self._get_response_time(slave['address'])  # 获取响应时间
            weight = 1.0 / (response_time + 0.1)  # 响应时间越短，权重越大
            weights.append(weight)
        
        # 计算总权重    
        total_weight = sum(weights)
        if total_weight == 0:  # 如果所有权重都是0
            return random.choice(slaves)  # 随机选择一个节点
        
        # 归一化权重
        normalized_weights = [w/total_weight for w in weights]
        
        # 根据权重随机选择一个节点,引入随机性，避免负载集中
        return random.choices(slaves, weights=normalized_weights)[0]
    
    def _get_response_time(self, address):
        """
        测量从节点的响应时间
        
        Args:
            address (tuple): 从节点的地址元组 (ip, port)
        
        Returns:
            float: 响应时间（秒），如果连接失败则返回无穷大
        """
        try:
            # 记录开始时间
            start_time = time.time()
            
            # 创建新的socket连接
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)  # 设置2秒超时，避免长时间等待
            
            # 尝试连接到从节点
            sock.connect(address)
            
            # 发送ping消息
            sock.send(json.dumps({'type': 'ping'}).encode())
            
            # 等待从节点响应
            sock.recv(1024)
            
            # 计算总响应时间
            response_time = time.time() - start_time
            
            # 关闭连接
            sock.close()
            
            return response_time
            
        except:
            # 如果发生任何错误（连接超时、连接拒绝等）
            # 返回无穷大，表示该节点当前不可用
            return float('inf')
            
    def select_slave(self, slaves, algorithm='round_robin'):
        algorithms = {
            'round_robin': self.round_robin,
            'least_connections': self.least_connections,
            'random': self.random_selection,
            'weighted_response_time': self.weighted_response_time
        }
        
        return algorithms.get(algorithm, self.round_robin)(slaves) 