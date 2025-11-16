# PyInstaller打包指南

## 📦 打包为Mac可执行文件

您的HotspotCrawler项目**可以使用PyInstaller成功打包为Mac可执行文件**。以下是详细的打包指南：

## 🛠️ 打包步骤

### 1. 安装PyInstaller

```bash
pip install pyinstaller
```

### 2. 使用自动化脚本打包

项目已提供自动化打包脚本，推荐使用：

```bash
# 运行打包脚本
./build_mac.sh
```

### 3. 手动打包（可选）

如果需要自定义打包选项：

```bash
# 使用spec文件打包
pyinstaller build.spec

# 或简单打包（可能缺少某些依赖）
pyinstaller --onefile --windowed src/web/app.py --name HotspotCrawler
```

## 📁 打包结果

打包完成后，您将获得：

1. **可执行文件**: `dist/HotspotCrawler`
2. **应用程序包**: `dist/HotspotCrawler.app`
3. **启动脚本**: `dist/run_hotspot_crawler.sh`

## 🚀 运行方式

### 方式1: 直接运行可执行文件
```bash
./dist/HotspotCrawler
```

### 方式2: 使用启动脚本（推荐）
```bash
./dist/run_hotspot_crawler.sh
```

### 方式3: 双击应用程序包
```bash
open dist/HotspotCrawler.app
```

## ⚙️ 打包配置说明

### build.spec配置文件
- **数据文件**: 自动包含配置文件和HTML模板
- **隐藏导入**: 包含所有必要的模块依赖
- **排除项**: 排除不需要的模块以减小体积

### 关键修改
1. **路径处理**: 支持开发环境和打包环境的路径识别
2. **ChromeDriver**: 自动管理ChromeDriver依赖
3. **配置文件**: 支持在打包环境中读取配置

## ⚠️ 系统要求

### 目标系统必须安装：
- **Chrome浏览器**: Selenium爬虫必需
- **macOS 10.14+**: 建议较新版本系统
- **网络权限**: 用于爬取网页内容

### Chrome浏览器检查
打包的应用会自动检查Chrome浏览器是否安装，如果没有安装会提示用户下载。

## 🔧 自定义配置

### 修改端口
编辑 `src/config/config.yml`：
```yaml
# 添加端口配置
port: 5001
```

### 修改启动页面
编辑 `src/web/app.py` 中的启动逻辑。

## 📋 使用说明

1. **启动应用**: 运行可执行文件后，Web服务会在后台启动
2. **访问界面**: 浏览器自动打开 `http://localhost:5001`
3. **停止服务**: 在终端按 `Ctrl+C` 或关闭应用程序

## 🐛 常见问题

### Q: 打包后无法找到配置文件？
A: 配置文件已自动打包，如果仍有问题，手动将 `src/config/config.yml` 复制到可执行文件同目录。

### Q: ChromeDriver相关错误？
A: 确保目标系统安装了Chrome浏览器，应用会自动管理ChromeDriver。

### Q: 权限被拒绝？
A: 在macOS中，首次运行可能需要在"系统偏好设置 > 安全性与隐私"中允许运行。

### Q: 应用体积过大？
A: 这是正常现象，PyInstaller会包含所有依赖。可以使用UPX压缩减小体积。

## 📊 文件大小参考

- **预期大小**: 80-120MB（包含所有依赖）
- **压缩后**: 使用UPX可减少20-30%体积

## 🔄 更新应用

当源代码更新后，重新运行打包脚本即可生成新版本：

```bash
./build_mac.sh
```

## 📤 分发说明

打包后的应用可以分发给其他Mac用户，但需要确保：

1. 目标系统安装了Chrome浏览器
2. 网络连接正常（用于爬虫功能）
3. 如果有AI功能，需要配置相应的API密钥