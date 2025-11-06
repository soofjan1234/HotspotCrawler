import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from config.config_manager import ConfigManager
from crawlers.toutiao_crawler import ToutiaoCrawler
from utils.log_utils import print_to_queue

class SchedulerManager:
    """定时任务管理器"""
    
    def __init__(self):
        # 配置日志
        logging.basicConfig(level=logging.INFO,
                           format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger('SchedulerManager')
        
        # 创建后台调度器
        self.scheduler = BackgroundScheduler()
        self.is_running = False
        self.config_manager = ConfigManager()
    
    def job_wrapper(self):
        """任务包装器，处理异常和日志"""
        try:
            print_to_queue(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 定时任务开始执行...")
            crawler = ToutiaoCrawler()
            crawler.run()
            print_to_queue(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 定时任务执行完成")
        except Exception as e:
            error_msg = f"定时任务执行失败: {str(e)}"
            self.logger.error(error_msg)
            print_to_queue(error_msg)
    
    def start(self):
        """启动定时任务调度器
        
        设置为每天12点执行一次爬取任务
        """
        if not self.is_running:
            # 添加定时任务，每天12点执行一次
            self.scheduler.add_job(
                func=self.job_wrapper,
                trigger=CronTrigger(hour=12, minute=0, second=0),
                id='crawler_job',
                name='定时爬取任务',
                replace_existing=True
            )
            
            # 启动调度器
            self.scheduler.start()
            self.is_running = True
            
            print_to_queue("定时任务调度器已启动，将每天12点执行一次爬取")
            self.logger.info("定时任务调度器已启动，每天12点执行")
    
    def stop(self):
        """停止定时任务调度器"""
        if self.is_running:
            self.scheduler.shutdown(wait=True)
            self.is_running = False
            print_to_queue("定时任务调度器已停止")
            self.logger.info("定时任务调度器已停止")
    
    def pause_job(self):
        """暂停定时任务"""
        try:
            self.scheduler.pause_job('crawler_job')
            print_to_queue("定时任务已暂停")
            self.logger.info("定时任务已暂停")
        except Exception as e:
            self.logger.error(f"暂停任务失败: {str(e)}")
    
    def resume_job(self):
        """恢复定时任务"""
        try:
            self.scheduler.resume_job('crawler_job')
            print_to_queue("定时任务已恢复")
            self.logger.info("定时任务已恢复")
        except Exception as e:
            self.logger.error(f"恢复任务失败: {str(e)}")

# 创建全局调度器实例
scheduler_manager = None

def get_scheduler():
    """获取全局调度器实例"""
    global scheduler_manager
    if scheduler_manager is None:
        scheduler_manager = SchedulerManager()
    return scheduler_manager