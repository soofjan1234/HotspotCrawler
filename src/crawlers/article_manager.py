import os
import time
from datetime import datetime, timedelta

class ArticleManager:
    """文章管理器类"""
    
    def __init__(self, article_id_file):
        self.article_id_file = article_id_file
    
    def read_article_ids(self):
        article_ids = set()
        try:
            if os.path.exists(self.article_id_file):
                # 检查文件最后修改时间，两周前的记录需要清理
                file_mod_time = os.path.getmtime(self.article_id_file)
                two_weeks_ago = (datetime.now() - timedelta(days=14)).timestamp()
                
                with open(self.article_id_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        parts = line.strip().split(',')
                        if len(parts) == 2:
                            article_id, timestamp = parts
                            # 只保留两周内的记录
                            if float(timestamp) >= two_weeks_ago:
                                article_ids.add(article_id)
                
                # 如果清理了旧记录，需要更新文件
                if len(article_ids) < len(open(self.article_id_file, 'r').readlines()):
                    with open(self.article_id_file, 'w', encoding='utf-8') as f:
                        current_timestamp = str(time.time())
                        for article_id in article_ids:
                            f.write(f"{article_id},{current_timestamp}\n")
        except Exception as e:
            print(f"读取文章ID文件时出错: {str(e)}")
        return article_ids
    
    def save_article_id(self, article_id):
        try:
            with open(self.article_id_file, 'a', encoding='utf-8') as f:
                timestamp = str(time.time())
                f.write(f"{article_id},{timestamp}\n")
        except Exception as e:
            print(f"保存文章ID时出错: {str(e)}")