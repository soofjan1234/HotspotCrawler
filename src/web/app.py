import sys
import os
import queue

# 添加项目根目录到sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, Response, stream_with_context, request
import threading
import time
from datetime import datetime
from utils.log_utils import print_to_queue, LogQueue

# 导入爬虫
from crawlers.toutiao_crawler import ToutiaoCrawler

app = Flask(__name__)
# 使用共享的日志队列
q = LogQueue.get_queue()

# 全局爬虫实例
crawler = None

# 爬虫是否正在运行
crawler_running = False

# 爬虫线程
crawler_thread = None

def print_to_queue(*args, sep=" ", end="\n"):
    q.put(sep.join(map(str, args)) + ("" if end == "" else end))

def sse_encode(text: str) -> str:
    lines = text.splitlines() or [""]
    return "".join(f"data: {line}\n" for line in lines) + "\n"

@app.route("/sse")
def sse():
    def gen():
        import json
        while True:
            try:
                item = q.get(timeout=15)
                # 构造前端期望的JSON格式
                message = json.dumps({
                    "type": "log",
                    "log": {
                        "message": item,
                        "type": "info",
                        "timestamp": datetime.now().strftime("%H:%M:%S")
                    }
                })
                yield sse_encode(message)
            except queue.Empty:
                # 发送心跳
                yield ":\n\n"
    return Response(stream_with_context(gen()), mimetype="text/event-stream")

@app.route("/run-crawler")
def run_crawler():
    global crawler, crawler_running, crawler_thread
    
    if crawler_running:
        return {"status": "error", "message": "爬虫正在运行中"}
    
    def crawler_task():
        global crawler_running
        import json
        try:
            crawler_running = True
            # 发送运行状态更新
            status_message = json.dumps({
                "type": "status",
                "is_running": True
            })
            q.put(status_message)
            print_to_queue("开始运行爬虫...")
            # 创建爬虫实例
            crawler = ToutiaoCrawler()
            # 运行爬虫
            crawler.run()
            print_to_queue("爬虫运行完成")
        except Exception as e:
            print_to_queue(f"爬虫运行出错: {str(e)}")
        finally:
            crawler_running = False
            # 发送运行状态更新
            status_message = json.dumps({
                "type": "status",
                "is_running": False
            })
            q.put(status_message)
    
    # 在新线程中运行爬虫
    crawler_thread = threading.Thread(target=crawler_task, daemon=True)
    crawler_thread.start()
    
    return {"status": "success", "message": "爬虫已开始运行"}

@app.route("/")
def index():
    return open("index.html", "r", encoding="utf-8").read()

if __name__ == "__main__":
    # 启动Flask服务器
    app.run(host="0.0.0.0", port=5000, threaded=True)