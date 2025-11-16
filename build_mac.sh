#!/bin/bash

# PyInstaller打包脚本 - macOS版本
# 使用方法: ./build_mac.sh

echo "🚀 开始构建HotspotCrawler macOS可执行文件..."

# 检查PyInstaller是否安装
if ! command -v pyinstaller &> /dev/null; then
    echo "❌ PyInstaller未安装，正在安装..."
    pip install pyinstaller
fi

# 清理之前的构建
echo "🧹 清理之前的构建文件..."
rm -rf build/ dist/

# 创建临时目录存放配置文件
echo "📁 准备配置文件..."
if [ ! -f "src/config/config.yml" ]; then
    echo "❌ 配置文件不存在: src/config/config.yml"
    exit 1
fi
if [ ! -f "src/web/index.html" ]; then
    echo "❌ HTML文件不存在: src/web/index.html"
    exit 1
fi
mkdir -p temp_config/src/config
cp src/config/config.yml temp_config/src/config/
mkdir -p temp_config/src/web
cp src/web/index.html temp_config/src/web/

# 执行打包
echo "🔨 开始打包..."
pyinstaller build.spec

# 检查打包结果
if [ -f "dist/HotspotCrawler" ]; then
    echo "✅ 打包成功！"
    echo "📦 可执行文件位置: dist/HotspotCrawler"
    echo "📏 文件大小: $(du -h dist/HotspotCrawler | cut -f1)"
    
    # 创建应用程序包
    echo "📱 创建macOS应用程序包..."
    mkdir -p "dist/HotspotCrawler.app/Contents/MacOS"
    mkdir -p "dist/HotspotCrawler.app/Contents/Resources"
    
    # 复制可执行文件
    cp "dist/HotspotCrawler" "dist/HotspotCrawler.app/Contents/MacOS/"
    
    # 创建Info.plist
    cat > "dist/HotspotCrawler.app/Contents/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>HotspotCrawler</string>
    <key>CFBundleIdentifier</key>
    <string>com.hotspotcrawler.app</string>
    <key>CFBundleName</key>
    <string>HotspotCrawler</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>LSUIElement</key>
    <false/>
</dict>
</plist>
EOF
    
    # 创建应用程序包启动脚本
    cat > "dist/HotspotCrawler.app/Contents/Resources/run.sh" << 'EOF'
#!/bin/bash
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../MacOS" && pwd)"
export PYTHONPATH="$DIR/../Resources:$PYTHONPATH"
"$DIR/HotspotCrawler"
EOF
    chmod +x "dist/HotspotCrawler.app/Contents/Resources/run.sh"
    
    echo "✅ 应用程序包创建完成: dist/HotspotCrawler.app"
    
    # 创建启动脚本
    cat > "dist/run_hotspot_crawler.sh" << EOF
#!/bin/bash
echo "🌐 启动HotspotCrawler..."
echo "📍 可执行文件位置: $(pwd)/HotspotCrawler"
echo "🌍 Web界面将在浏览器中打开: http://localhost:5001"
echo "⏹️  按Ctrl+C停止服务"
echo ""

# 设置环境变量
export PYTHONPATH="$(pwd):$PYTHONPATH"

# 启动应用并自动打开浏览器
./HotspotCrawler &
APP_PID=$!

# 等待服务启动
sleep 3

# 打开浏览器
open http://localhost:5001

# 等待应用结束
wait $APP_PID
EOF
    
    chmod +x "dist/run_hotspot_crawler.sh"
    
    # 清理临时文件
    rm -rf temp_config/
    
    echo ""
    echo "🎉 构建完成！"
    echo ""
    echo "📋 使用说明:"
    echo "1. 直接运行: ./dist/HotspotCrawler"
    echo "2. 或使用启动脚本: ./dist/run_hotspot_crawler.sh"
    echo "3. 或双击应用程序包: dist/HotspotCrawler.app"
    echo ""
    echo "⚠️  注意事项:"
    echo "- 确保目标系统已安装Chrome浏览器"
    echo "- 首次运行可能需要授权网络访问"
    echo "- 应用将在后台启动Web服务，通过浏览器访问"
    
else
    echo "❌ 打包失败，请检查错误信息"
    exit 1
fi