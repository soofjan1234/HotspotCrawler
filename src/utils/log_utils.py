import queue

# 创建全局日志队列
log_queue = queue.Queue()

def print_to_queue(*args, sep=" ", end="\n"):
    """将日志消息放入队列"""
    log_queue.put(sep.join(map(str, args)) + ("" if end == "" else end))

class LogQueue:
    """日志队列类，提供队列访问接口"""
    @staticmethod
    def get_queue():
        return log_queue
    
    @staticmethod
    def put(item):
        log_queue.put(item)
    
    @staticmethod
    def get(timeout=None):
        return log_queue.get(timeout=timeout)
    
    @staticmethod
    def empty():
        return log_queue.empty()