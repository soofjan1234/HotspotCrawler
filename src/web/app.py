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
    接收文件上传，读取文件内容，生成新文案并保存到generate文件夹
    按日期分类存储：YYYYMMDD/时间戳_标题/内容
    """
    try:
        # 检查是否有文件上传
        if 'file' not in request.files:
            return jsonify({"status": "error", "message": "没有文件上传"}), 400
        
        file = request.files['file']
        
        # 检查文件名是否为空
        if file.filename == '':
            return jsonify({"status": "error", "message": "未选择文件"}), 400
        
        # 验证文件类型
        if not file.filename.endswith('.txt'):
            return jsonify({"status": "error", "message": "请上传.txt文件"}), 400
        
        # 获取上传的文件名
        original_filename = file.filename
        print(f"Received file: {original_filename}")
        
        # 记录日志
        print_to_queue(f"开始生成AI文案，文件: {original_filename}")
        
        # 创建基础generate文件夹（如果不存在）
        base_generate_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'generate')
        os.makedirs(base_generate_dir, exist_ok=True)
        
        # 获取当前日期和时间
        now = datetime.now()
        date_folder = now.strftime("%Y%m%d")  # YYYYMMDD格式的日期文件夹
        time_part = now.strftime("%H%M%S")    # HHMMSS格式的时间部分
        
        # 创建日期文件夹
        date_dir = os.path.join(base_generate_dir, date_folder)
        os.makedirs(date_dir, exist_ok=True)
        
        article_dir = os.path.join(date_dir, f"{time_part}")
        os.makedirs(article_dir, exist_ok=True)
        
        # 保存上传的文件到临时位置
        temp_file_path = os.path.join(article_dir, f"temp_{now.strftime('%Y%m%d_%H%M%S_%f')}.txt")
        file.save(temp_file_path)
        
        # 读取原始内容
        with open(temp_file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        # 创建AI生成器实例
        try:
            ai_generator = create_ai_generator(config_manager)
        except Exception as e:
            # 清理临时文件
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            return jsonify({"status": "error", "message": f"创建AI生成器失败: {str(e)}"}), 500
        
        # 生成AI文案
        try:
            generated_content = ai_generator.generate_from_file(temp_file_path)
        except Exception as e:
            # 清理临时文件
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            return jsonify({"status": "error", "message": f"生成AI文案失败: {str(e)}"}), 500
        
        if not generated_content:
            # 清理临时文件
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            return jsonify({"status": "error", "message": "AI文案生成失败"}), 500
        
        # 生成最终内容（原内容 + 生成的文案）
        final_content = f"# 原始内容\n{original_content}\n\n# AI生成文案\n{generated_content}"
        
        # 生成输出文件名
        output_file_name = f"content_ai.txt"
        output_file_path = os.path.join(article_dir, output_file_name)
        
        # 保存生成的文案（包含原内容）
        with open(output_file_path, 'w', encoding='utf-8') as f:
            f.write(final_content)
        
        # 清理临时文件
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        
        # 记录日志
        relative_path = os.path.join(date_folder, time_part, output_file_name)
        print_to_queue(f"AI文案生成成功，已保存到: {relative_path}")
        
        # 返回结果
        return jsonify({
            "status": "success",
            "message": "AI文案生成成功",
            "output_file": output_file_name,
            "content": final_content,
            "path": relative_path
        })
        
    except Exception as e:
        error_message = f"生成AI文案时发生错误: {str(e)}"
        print_to_queue(error_message)
        return jsonify({"status": "error", "message": error_message}), 500




if __name__ == "__main__":
    # 启动Flask服务器，使用端口5001以避免与系统AirPlay Receiver冲突
    app.run(host="0.0.0.0", port=5001, threaded=True)