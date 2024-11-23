# Image Processing System with Load Balancing

A distributed system for image processing with multiple load balancing algorithms implementation. The system consists of a master node, multiple slave nodes, and a real-time monitoring interface.

## System Architecture

### Core Components

1. **Master Node (master.py)**
   - Manages slave node registration and status
   - Receives client task requests
   - Uses load balancer to select appropriate slave nodes
   - Forwards tasks and returns results
   - Handles node failure through heartbeat mechanism

2. **Slave Nodes (slave.py)**
   - Register with master node
   - Execute image processing tasks:
     - Crop: Random crop with Gaussian and median blur
     - Noise: Multi-layer noise with salt-and-pepper effect
     - Grayscale: Conversion with histogram equalization
   - Send heartbeat messages
   - Maintain task statistics

3. **Load Balancer (load_balancer.py)**
   Implements four load balancing algorithms:
   - Round Robin: Sequential task distribution
   - Least Connections: Selects node with fewest tasks
   - Random Selection: Random node selection
   - Weighted Response Time: Dynamic weight based on response time

4. **Client (client.py)**
   - Reads image folder
   - Creates image processing tasks
   - Records execution time and statistics
   - Generates summary logs for each algorithm

5. **Monitor System (monitor.py)**
   - Real-time cluster status display
   - Node information display
   - Algorithm statistics display

### Message Format

1. **Task Message**
```json
{
    "type": "task",
    "data": {
        "type": "image",
        "operation": "noise",
        "image_path": "image/test.jpg",
        "algorithm": "round_robin"
    }
}
```

2. **Heartbeat Message**
```json
{
    "type": "heartbeat",
    "port": 5009,
    "tasks": 10,
    "total_execution_time": 25.5,
    "algorithm_stats": {
        "round_robin": {
            "count": 5,
            "total_time": 12.5,
            "avg_time": 2.5
        }
    }
}
```
### Image Processing Operations

1. **Crop**
   - Random crop with preprocessing
   - Multiple Gaussian and median blur passes
   - Output format: `{original_name}_cropped.{ext}`

2. **Noise**
   - Multi-layer noise addition
   - Salt-and-pepper noise effect
   - Output format: `{original_name}_noisy.{ext}`

3. **Grayscale**
   - Conversion with enhancement
   - Histogram equalization
   - Morphological operations
   - Output format: `{original_name}_gray.{ext}`

### Load Balancing Algorithms

1. **Round Robin**
   - Sequential task distribution
   - Fair distribution for similar node performance
   - Simple and predictable

2. **Least Connections**
   - Selects node with fewest current tasks
   - Prevents single node overload
   - Adaptive to node workload

3. **Random Selection**
   - Random node selection
   - Long-term balanced distribution
   - Simple implementation

4. **Weighted Response Time**
   - Dynamic weight based on node response time
   - Adapts to node performance differences
   - Best for heterogeneous environments
### Error Handling

1. **Node Failure Detection**
   - Heartbeat timeout: 30 seconds
   - Automatic node removal
   - Task redistribution

2. **Resource Management**
   - Socket reuse (SO_REUSEADDR)
   - Graceful shutdown
   - Memory cleanup

### Monitoring Interface

Access the web monitoring interface at `http://localhost:5005` to view:
- Master node status
- Connected slave nodes
- Task statistics
- Algorithm performance metrics

### Deployment

1. **Local Testing**

## Startup Commands

Execute the following commands in different terminals:

### Terminal 1 - Start Master Node
```bash
# Start master server (default port 5008)
python master.py
```

### Terminal 2 - Start Slave Node 1
```bash
# Parameters: master_ip master_port slave_port
python slave.py localhost 5008 5009
```

### Terminal 3 - Start Slave Node 2
```bash
# Parameters: master_ip master_port slave_port
python slave.py localhost 5008 5010
```

### Terminal 4 - Start Monitor
```bash
# Launch system monitor
python monitor.py
```

### Terminal 5 - Start Client
```bash
# Start client and send tasks
python client.py
```

### Parameter Description
- `localhost`: Master node IP address
- `5008`: Master node port
- `5009`/`5010`: Slave node ports

### Notes
- Ensure all ports are available before starting
- Start the master node first
- Start slave nodes after master node is running
- Monitor can be started at any time
- Client should be started after at least one slave node is running

## Dependencies

### Required Packages
Create a `requirements.txt` file with the following content:

```txt
opencv-python
numpy
flask
```

## Project Structure

```
project/
├── master.py           # Master node implementation
├── slave.py           # Slave node implementation
├── client.py          # Client for submitting tasks
├── monitor.py         # System monitoring interface
├── load_balancer.py   # Load balancing algorithms
├── health_check.py    # Node health checking module
├── deploy_master.sh   # Master node deployment script
├── deploy_slave.sh    # Slave node deployment script
├── requirements.txt   # Python package dependencies
├── README.md         # Project documentation
├── image/            # Input image directory
├── templates/        # Web interface templates
│   └── monitor.html  # Monitor page template
└── output_slave_/    # Processed image output directory
```

### Directory Description

#### Core Components
- `master.py`: Master node that manages task distribution
- `slave.py`: Slave nodes that process images
- `client.py`: Client interface for task submission
- `monitor.py`: Real-time system monitoring

#### Support Modules
- `load_balancer.py`: Load balancing strategy implementation
- `health_check.py`: Node health monitoring system




