import sys
import os
import queue
import requests
from datetime import datetime

# 添加项目根目录到sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, Response, stream_with_context, request, render_template, jsonify
import threading
import time
from utils.log_utils import print_to_queue, LogQueue
from config.config_manager import ConfigManager
from utils.scheduler_manager import get_scheduler
from utils.ai_generator import AIGenerator, create_ai_generator

# 导入爬虫
from crawlers.toutiao_crawler import ToutiaoCrawler

app = Flask(__name__)
# 使用共享的日志队列
q = LogQueue.get_queue()

# 配置管理器
config_manager = ConfigManager()

# 全局爬虫实例
crawler = None

# 爬虫是否正在运行
crawler_running = False

# 爬虫线程
crawler_thread = None

# 定时任务调度器
@app.before_first_request
def startup():
    """应用启动时初始化定时任务"""
    scheduler = get_scheduler()
    scheduler.start()  # 启动定时任务

# 在Flask应用关闭时停止定时任务
import atexit

@atexit.register
def cleanup():
    """应用完全关闭时清理资源"""
    scheduler = get_scheduler()
    scheduler.stop()

# 使用从utils.log_utils导入的print_to_queue函数

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

@app.route("/generate-ai-content", methods=["POST"])
def generate_ai_content():
    """
    生成AI文案接口
    接收文件路径参数，读取文件内容，生成新文案并保存
    """
    try:
        # 获取请求参数
        data = request.get_json()
        if not data or "file_path" not in data:
            return jsonify({"status": "error", "message": "缺少文件路径参数"}), 400
        
        file_path = data["file_path"]
        print(f"Received file_path: {file_path}")
        # 验证文件是否存在
        if not os.path.exists(file_path):
            return jsonify({"status": "error", "message": f"文件不存在: {file_path}"}), 404
        
        # 记录日志
        print_to_queue(f"开始生成AI文案，文件路径: {file_path}")
        
        # 创建AI生成器实例
        try:
            ai_generator = create_ai_generator(config_manager)
        except Exception as e:
            return jsonify({"status": "error", "message": f"创建AI生成器失败: {str(e)}"}), 500
        
        # 生成AI文案
        generated_content = ai_generator.generate_from_file(file_path)
        
        if not generated_content:
            return jsonify({"status": "error", "message": "AI文案生成失败"}), 500
        
        # 生成带时间戳的输出文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = os.path.basename(file_path)
        name_without_ext = os.path.splitext(base_name)[0]
        output_file_name = f"generate_{name_without_ext}_{timestamp}.txt"
        output_file_path = os.path.join(os.path.dirname(file_path), output_file_name)
        
        # 保存生成的文案
        with open(output_file_path, 'w', encoding='utf-8') as f:
            f.write(generated_content)
        
        # 记录日志
        print_to_queue(f"AI文案生成成功，已保存到: {output_file_path}")
        
        # 返回结果
        return jsonify({
            "status": "success",
            "message": "AI文案生成成功",
            "output_file": output_file_path,
            "content": generated_content
        })
        
    except Exception as e:
        error_message = f"生成AI文案时发生错误: {str(e)}"
        print_to_queue(error_message)
        return jsonify({"status": "error", "message": error_message}), 500




if __name__ == "__main__":
    # 启动Flask服务器，使用端口5001以避免与系统AirPlay Receiver冲突
    app.run(host="0.0.0.0", port=5001, threaded=True)