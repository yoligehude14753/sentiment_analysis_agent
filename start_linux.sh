#!/bin/bash

# 情感分析系统 - Linux启动脚本
# 适用于GCP虚拟机部署

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查Python版本
check_python() {
    log_info "检查Python环境..."
    
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
        log_success "Python版本: $PYTHON_VERSION"
        
        # 检查版本是否满足要求 (>= 3.8)
        PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
        PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
        
        if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 8 ]; then
            log_success "Python版本满足要求"
        else
            log_error "Python版本过低，需要3.8或更高版本"
            exit 1
        fi
    else
        log_error "未找到Python3，请先安装Python3"
        exit 1
    fi
}

# 检查虚拟环境
check_venv() {
    log_info "检查虚拟环境..."
    
    if [ ! -d "venv" ]; then
        log_warning "虚拟环境不存在，正在创建..."
        python3 -m venv venv
        log_success "虚拟环境创建完成"
    else
        log_success "虚拟环境已存在"
    fi
    
    # 激活虚拟环境
    source venv/bin/activate
    log_success "虚拟环境已激活"
}

# 安装依赖
install_dependencies() {
    log_info "安装项目依赖..."
    
    # 升级pip
    pip install --upgrade pip
    
    # 安装依赖
    if [ -f "requirements_production.txt" ]; then
        pip install -r requirements_production.txt
        log_success "生产环境依赖安装完成"
    elif [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        log_success "依赖安装完成"
    else
        log_error "未找到requirements文件"
        exit 1
    fi
}

# 检查环境变量
check_env() {
    log_info "检查环境配置..."
    
    if [ ! -f ".env" ]; then
        log_warning "环境配置文件不存在，创建默认配置..."
        cat > .env << EOF
# 阿里云API配置
DASHSCOPE_API_KEY=your_api_key_here
ALI_MODEL_NAME=qwen-turbo
ALI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# 服务器配置
HOST=0.0.0.0
PORT=8000
DEBUG=False

# 数据库配置
DATABASE_URL=sqlite:///data/sentiment_analysis.db
EOF
        log_success "默认环境配置文件已创建"
        log_warning "请编辑.env文件设置您的API密钥"
    else
        log_success "环境配置文件已存在"
    fi
}

# 创建必要目录
create_directories() {
    log_info "创建必要目录..."
    
    mkdir -p data
    mkdir -p logs
    mkdir -p exports
    
    log_success "目录创建完成"
}

# 检查端口占用
check_port() {
    log_info "检查端口占用..."
    
    PORT=${PORT:-8000}
    
    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null ; then
        log_warning "端口 $PORT 已被占用"
        log_info "尝试终止占用进程..."
        
        # 尝试终止占用进程
        PID=$(lsof -Pi :$PORT -sTCP:LISTEN -t)
        if [ ! -z "$PID" ]; then
            kill -9 $PID 2>/dev/null || true
            sleep 2
        fi
        
        # 再次检查
        if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null ; then
            log_error "无法释放端口 $PORT，请手动处理"
            exit 1
        else
            log_success "端口 $PORT 已释放"
        fi
    else
        log_success "端口 $PORT 可用"
    fi
}

# 启动应用
start_app() {
    log_info "启动情感分析系统..."
    
    # 设置环境变量
    export PYTHONPATH="${PYTHONPATH}:$(pwd)"
    
    # 启动应用
    log_success "系统启动中..."
    log_info "访问地址: http://0.0.0.0:8000"
    log_info "按 Ctrl+C 停止服务"
    echo "=========================================="
    
    # 使用uvicorn启动
    python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
}

# 主函数
main() {
    echo "=========================================="
    echo "🚀 情感分析系统 - Linux启动脚本"
    echo "=========================================="
    
    # 检查当前目录
    if [ ! -f "main.py" ]; then
        log_error "请在项目根目录运行此脚本"
        exit 1
    fi
    
    # 执行检查步骤
    check_python
    check_venv
    install_dependencies
    check_env
    create_directories
    check_port
    
    # 启动应用
    start_app
}

# 捕获中断信号
trap 'echo -e "\n${YELLOW}正在停止服务...${NC}"; exit 0' INT

# 运行主函数
main "$@"


