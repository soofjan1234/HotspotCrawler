# HotspotCrawler - 热点内容爬取与处理系统

## 项目简介

HotspotCrawler是一个热点内容爬取与处理系统，能够爬取网络热点内容，提供Web界面进行管理，并支持AI辅助生成内容。本系统基于Python开发，使用Flask作为Web框架，APScheduler处理定时任务。

## 系统要求

- Python
- pip (Python包管理器)
- Chrome浏览器 (用于Selenium爬虫)

## 快速开始

### 0. 准备

1. . 下载chormeDriver， 复制地址到浏览器
https://storage.googleapis.com/chrome-for-testing-public/142.0.7444.61/mac-arm64/chromedriver-mac-arm64.zip

2. 在命令行输入 open /usr/local/bin 打开文件夹，将下载的chromedriver 移动的到该文件夹（管理员权限）

### 1. 安装依赖

建议在Python虚拟环境中运行项目，以避免依赖冲突。按照以下步骤操作：

```bash

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# macOS/Linux系统
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 退出虚拟环境（完成工作后）
# deactivate
```

### 2. 配置设置

系统配置文件位于 `src/config/config.yml`，您可以根据需要修改以下设置：

- `isDebug`: 是否开启调试模式 (true/false)
- `apiKey`: API密钥
- `prompt`: AI生成内容的提示模板
- `crawler`: 爬虫相关配置（重试次数、超时时间、图片下载数量等）

### 3. 运行项目

确保虚拟环境已激活，然后运行Flask应用：

```bash
# 确保虚拟环境已激活（如果尚未激活）
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate

python src/web/app.py
```

应用将在 `http://0.0.0.0:5001` 启动。

### 4. 项目打包

项目根目录提供了打包脚本，可以将项目代码和配置文件打包为ZIP文件，同时排除虚拟环境、缓存文件等不必要的内容：

```bash
# 运行打包脚本
python pack_project.py

# 指定输出文件名
python pack_project.py --output my_custom_pack.zip

# 包含空目录
python pack_project.py --include-empty-dirs
```

打包后的文件将在项目根目录生成，默认文件名为 `HotspotCrawler_时间戳.zip`。

## 项目结构

```
HotspotCrawler/
├── src/
│   ├── config/           # 配置相关文件
│   │   ├── config.yml    # 主配置文件
│   │   └── config_manager.py  # 配置管理器
│   ├── crawlers/         # 爬虫模块
│   │   ├── __init__.py
│   │   ├── toutiao_crawler.py  # 头条爬虫
│   │   ├── article_extractor.py  # 文章提取器
│   │   ├── article_manager.py  # 文章管理器
│   │   └── media_downloader.py  # 媒体下载器
│   ├── utils/            # 工具模块
│   │   ├── __init__.py
│   │   ├── log_utils.py  # 日志工具
│   │   ├── scheduler_manager.py  # 调度器管理
│   │   └── ai_generator.py  # AI内容生成
│   ├── web/              # Web界面
│   │   ├── app.py        # Flask应用入口
│   │   └── index.html    # 前端页面
│   ├── logger/           # 日志模块
│   └── storage/          # 存储模块
├── requirements.txt      # 项目依赖
└── README.md             # 项目说明文档
```

## 使用说明

### Web界面功能

1. **首页** (`/`)：系统主页面，显示运行状态
2. **爬虫控制**：通过 `/run-crawler` 接口启动爬虫
3. **日志查看**：通过SSE（Server-Sent Events）实时查看系统日志
4. **AI内容生成**：通过 `/generate-ai-content` 接口生成AI内容

### 定时任务

系统启动时会自动初始化并启动定时任务调度器。您可以在 `utils/scheduler_manager.py` 中配置具体的定时任务。

## 主要功能模块

### 1. 爬虫模块

- **头条爬虫**：爬取头条热点内容
- **文章提取器**：从HTML中提取文章内容
- **媒体下载器**：下载文章中的图片等媒体资源

### 2. 配置管理

配置管理器会自动处理操作系统检测和路径配置，确保在不同平台上正确运行。

### 3. 日志系统

提供实时日志输出，通过SSE推送到前端界面。

### 4. AI内容生成

基于配置的提示模板，生成适合口播的短视频文案。

## 注意事项

1. 请确保Chrome浏览器已正确安装，Selenium爬虫需要使用Chrome浏览器
2. 初次运行时，系统会自动创建必要的目录结构
3. 调试模式下 (`isDebug: true`) 只会提取文章ID，不会爬取完整内容
4. 请合理设置爬虫的重试次数和超时时间，避免对目标网站造成过大压力

## 常见问题

### Q: 爬虫无法正常运行怎么办？
A: 请检查Chrome浏览器是否安装，以及网络连接是否正常。查看实时日志可获取更多错误信息。

### Q: 如何修改系统运行端口？
A: 在 `src/web/app.py` 文件中，修改最后一行的 `port` 参数。

### Q: 如何配置定时任务？
A: 编辑 `utils/scheduler_manager.py` 文件，设置相应的定时任务。

### Q: 运行项目时出现依赖错误怎么办？
A: 确保您在正确的虚拟环境中运行项目。尝试重新创建虚拟环境并安装依赖：
```bash
# 删除旧的虚拟环境
rm -rf venv  # macOS/Linux
# 或在Windows上
# rmdir /s /q venv

# 重新创建虚拟环境
python -m venv venv
# 激活虚拟环境
source venv/bin/activate  # macOS/Linux
# 或在Windows上
# venv\Scripts\activate

# 重新安装依赖
pip install -r requirements.txt
```

### Q: 虚拟环境中的Python版本与系统Python版本不一致怎么办？
A: 创建虚拟环境时，默认使用创建虚拟环境的Python版本。如果需要特定版本，请先安装对应版本的Python，然后使用该版本创建虚拟环境：
```bash
python3.x -m venv venv  # 替换3.x为您需要的Python版本
```

## License

MIT