import socket
import json
import threading
import time
from load_balancer import LoadBalancer
import logging
import signal
import sys

logging.basicConfig(filename='master.log', level=logging.INFO)

class Master:
    """
    分布式系统的主节点类，负责管理从节点、任务分发和负载均衡。
    
    属性:
        host (str): 主节点监听的IP地址
        port (int): 主节点监听的端口号
        slaves (list): 存储所有已注册的从节点信息
        load_balancer (LoadBalancer): 负载均衡器实例
        heartbeat_timeout (float): 心跳超时时间（秒）
    """

    def __init__(self, host='0.0.0.0', port=5008):
        self.host = host
        self.port = port
        self.slaves = []
        self.load_balancer = LoadBalancer()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # 创建socket对象
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # 设置socket选项
        self.socket.bind((self.host, self.port)) # 绑定地址和端口
        self.socket.listen(5) # 设置监听队列大小
        self.running = True # 运行标志
        signal.signal(signal.SIGINT, self._signal_handler) # 捕获Ctrl+C信号
        signal.signal(signal.SIGTERM, self._signal_handler) # 捕获kill信号
        
    def _signal_handler(self, signum, frame): # 信号处理函数
        print("\n正在关闭主节点...")
        self.running = False
        try:
            self.socket.shutdown(socket.SHUT_RDWR)
        except:
            pass
        self.socket.close()
        logging.info("主节点已关闭")
        sys.exit(0)
        
    def start(self): # 启动主节点
        """
        启动主节点服务。
        
        功能：
        1. 创建并配置服务器socket
        2. 启动心跳检查线程
        3. 开始监听连接请求
        4. 为每个新连接创建处理线程
        """
        logging.info(f"主节点启动于 {self.host}:{self.port}")
        heartbeat_thread = threading.Thread(target=self._heartbeat_check, daemon=True) # 创建心跳检查线程
        heartbeat_thread.start()
        
        try: 
            while self.running:
                try:
                    self.socket.settimeout(1.0) # 设置超时时间
                    client_socket, address = self.socket.accept() # 接受连接
                    threading.Thread(target=self._handle_connection, 
                                  args=(client_socket, address)).start() # 创建线程处理连接
                except socket.timeout:
                    continue # 超时继续
                except Exception as e:
                    if self.running:
                        logging.error(f"接受连接错误: {e}")
        except KeyboardInterrupt:
            self._signal_handler(signal.SIGINT, None) # 捕获Ctrl+C信号
        finally:
            self._cleanup()
    
    def _cleanup(self):
        try:
            self.socket.shutdown(socket.SHUT_RDWR)
        except:
            pass
        self.socket.close()
        logging.info("主节点资源已清理")
    
    def _handle_connection(self, client_socket, address):
        """
        处理新的socket连接。
        
        Args:
            client_socket (socket): 新建立的客户端socket连接
            address (tuple): 客户端地址信息
            
        根据消息类型分发到不同的处理函数：
        - register: 节点注册
        - heartbeat: 心跳更新
        - task: 任务处理
        """
        try:
            data = client_socket.recv(1024).decode() # 接收数据
            message = json.loads(data) # 解析JSON数据
            
            if message['type'] == 'register':
                self._handle_register(message, address) # 处理注册请求
            elif message['type'] == 'task':
                self._handle_task(message, client_socket) # 处理任务请求
            elif message['type'] == 'health_check':
                self._handle_health_check(client_socket) # 处理健康检查请求
            elif message['type'] == 'status_request':
                self._handle_status_request(client_socket) # 处理状态请求
            elif message['type'] == 'heartbeat':
                self._handle_heartbeat(message, address) # 处理心跳请求
            
        except Exception as e:
            logging.error(f"处理连接错误: {e}")
        finally:
            try:
                client_socket.shutdown(socket.SHUT_RDWR)
            except:
                pass
            client_socket.close()
    
    def _handle_register(self, message, address): # 处理新节点注册请求
        """
        处理从节点的注册请求。
        
        Args:
            message (dict): 包含注册信息的消息字典，必须包含'port'键
            address (tuple): 发送注册请求的节点地址元组 (ip, port)
        
        注册信息包含：
        - 节点地址信息
        - 初始任务数 0
        - 心跳时间戳
        - 总执行时间
        - 算法统计信息
        """
        slave_info = {
            'address': (address[0], message['port']), # 节点地址
            'tasks': 0, # 任务数
            'last_heartbeat': time.time(), # 最后一次心跳时间
            'total_execution_time': 0, # 总执行时间
            'algorithm_stats': {} # 算法统计信息
        }
        self.slaves.append(slave_info)
        logging.info(f"新从节点注册: {address[0]}:{message['port']}")
    
    def _handle_task(self, message, client_socket): # 处理任务请求
        """
        处理客户端发来的任务请求。
        
        Args:
            message (dict): 任务信息字典, 包含任务详情和算法类型, 详见client.py
            client_socket (socket): 客户端的socket连接
            
        流程：
        1. 通过负载均衡器选择合适的从节点
        2. 建立与选中从节点的连接
        3. 转发任务并等待响应
        4. 将结果返回给客户端
        """
        selected_slave = self.load_balancer.select_slave(
            self.slaves, # 从节点列表
            algorithm=message['data']['algorithm']
        ) # load_balancer 选择从节点
        
        if not selected_slave: 
            response = {'status': 'error', 'message': '无可用从节点'}
            client_socket.send(json.dumps(response).encode())
            return
            
        slave_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # 创建socket对象将任务转发给选中的从节点
        try:
            slave_socket.connect(selected_slave['address']) # 连接到选中的从节点
            slave_socket.send(json.dumps(message).encode()) # 发送任务请求  
            response = json.loads(slave_socket.recv(1024).decode()) # 接收从节点响应
            response['slave'] = f"{selected_slave['address'][0]}:{selected_slave['address'][1]}" # 添加从节点信息
            client_socket.send(json.dumps(response).encode()) # 发送响应给客户端
            
        except Exception as e:
            logging.error(f"任务分发错误: {e}")
            self.remove_slave(selected_slave['address'])
            response = {'status': 'error', 'message': '从节点连接失败'}
            try:
                client_socket.send(json.dumps(response).encode())
            except:
                pass
        finally:
            try:
                slave_socket.shutdown(socket.SHUT_RDWR) 
            except:
                pass
            slave_socket.close()
    
    def _heartbeat_check(self): 
        """
        定期检查从节点的心跳状态。
        
        功能：
        - 检查所有从节点的最后心跳时间
        - 移除超时的从节点
        - 每隔一定时间执行一次
        """
        while self.running:
            current_time = time.time()
            offline_slaves = []
            for slave in self.slaves:
                if current_time - slave['last_heartbeat'] > 30:  # 30秒超时
                    offline_slaves.append(slave['address'])
            
            # 移除超时的从节点
            for address in offline_slaves:
                self.remove_slave(address)
                logging.info(f"从节点心跳超时，已移除: {address[0]}:{address[1]}")
            
            time.sleep(10)
    
    def _handle_health_check(self, client_socket): 
        response = {
            'status': 'ok',
            'time': time.time()
        }
        client_socket.send(json.dumps(response).encode())
    
    def _handle_status_request(self, client_socket):
        status = {
            'master_status': 'running',
            'slaves': self.slaves,
            'time': time.time()
        }
        client_socket.send(json.dumps(status).encode()) # 发送状态响应给monitor
    
    def _handle_heartbeat(self, message, address):
        """
        处理从节点的心跳消息。
        
        Args:
            message (dict): 心跳消息字典，包含节点状态信息
            address (tuple): 发送心跳的节点地址
            
        更新内容：
        - 最后心跳时间
        - 当前任务数
        - 总执行时间
        - 算法统计信息
        """
        for slave in self.slaves:
            if slave['address'][1] == message['port']: # message['port'] 是从节点在发送心跳消息时带上的自己的端口号
                slave['last_heartbeat'] = time.time() 
                slave['tasks'] = message.get('tasks', 0) 
                slave['total_execution_time'] = message.get('total_execution_time', 0)
                slave['algorithm_stats'] = message.get('algorithm_stats', {})
                break
    
    def remove_slave(self, address):
        """移除指定地址的从节点"""
        self.slaves = [s for s in self.slaves if s['address'] != address]
        logging.info(f"从节点已移除: {address[0]}:{address[1]}")

if __name__ == '__main__':
    master = Master()
    master.start() 