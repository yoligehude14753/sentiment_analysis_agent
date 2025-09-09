#!/usr/bin/env python3
"""
健康检查脚本
用于监控应用状态和系统资源
"""

import requests
import psutil
import json
import sys
import time
from datetime import datetime

def check_application_health():
    """检查应用健康状态"""
    try:
        response = requests.get('http://localhost:8000/', timeout=10)
        if response.status_code == 200:
            return {"status": "healthy", "response_time": response.elapsed.total_seconds()}
        else:
            return {"status": "unhealthy", "status_code": response.status_code}
    except requests.exceptions.RequestException as e:
        return {"status": "error", "error": str(e)}

def check_system_resources():
    """检查系统资源使用情况"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_available_gb": round(memory.available / 1024**3, 2),
            "disk_percent": disk.percent,
            "disk_free_gb": round(disk.free / 1024**3, 2)
        }
    except Exception as e:
        return {"error": str(e)}

def check_processes():
    """检查关键进程状态"""
    processes = {}
    
    # 检查gunicorn进程
    gunicorn_processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
        if 'gunicorn' in proc.info['name'].lower():
            gunicorn_processes.append(proc.info)
    
    processes['gunicorn'] = {
        "count": len(gunicorn_processes),
        "processes": gunicorn_processes
    }
    
    # 检查nginx进程
    nginx_processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
        if 'nginx' in proc.info['name'].lower():
            nginx_processes.append(proc.info)
    
    processes['nginx'] = {
        "count": len(nginx_processes),
        "processes": nginx_processes
    }
    
    return processes

def check_database():
    """检查数据库文件"""
    import os
    db_files = [
        '/var/www/sentiment-analysis/sentiment_analysis.db',
        '/var/www/sentiment-analysis/sentiment_results.db'
    ]
    
    db_status = {}
    for db_file in db_files:
        if os.path.exists(db_file):
            stat = os.stat(db_file)
            db_status[os.path.basename(db_file)] = {
                "exists": True,
                "size_mb": round(stat.st_size / 1024**2, 2),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
            }
        else:
            db_status[os.path.basename(db_file)] = {"exists": False}
    
    return db_status

def main():
    """主函数"""
    print("🔍 开始健康检查...")
    print(f"检查时间: {datetime.now().isoformat()}")
    print("=" * 50)
    
    # 检查应用健康状态
    print("📱 应用状态检查:")
    app_health = check_application_health()
    if app_health["status"] == "healthy":
        print(f"  ✅ 应用运行正常 (响应时间: {app_health['response_time']:.2f}s)")
    else:
        print(f"  ❌ 应用异常: {app_health}")
    
    # 检查系统资源
    print("\n💻 系统资源检查:")
    resources = check_system_resources()
    if "error" not in resources:
        print(f"  CPU使用率: {resources['cpu_percent']}%")
        print(f"  内存使用率: {resources['memory_percent']}% (可用: {resources['memory_available_gb']}GB)")
        print(f"  磁盘使用率: {resources['disk_percent']}% (可用: {resources['disk_free_gb']}GB)")
        
        # 警告检查
        if resources['cpu_percent'] > 80:
            print("  ⚠️  CPU使用率过高！")
        if resources['memory_percent'] > 85:
            print("  ⚠️  内存使用率过高！")
        if resources['disk_percent'] > 90:
            print("  ⚠️  磁盘空间不足！")
    else:
        print(f"  ❌ 无法获取系统资源: {resources['error']}")
    
    # 检查进程状态
    print("\n🔧 进程状态检查:")
    processes = check_processes()
    
    gunicorn_count = processes['gunicorn']['count']
    nginx_count = processes['nginx']['count']
    
    if gunicorn_count > 0:
        print(f"  ✅ Gunicorn进程: {gunicorn_count}个")
    else:
        print("  ❌ Gunicorn进程未运行！")
    
    if nginx_count > 0:
        print(f"  ✅ Nginx进程: {nginx_count}个")
    else:
        print("  ❌ Nginx进程未运行！")
    
    # 检查数据库
    print("\n💾 数据库检查:")
    db_status = check_database()
    for db_name, status in db_status.items():
        if status["exists"]:
            print(f"  ✅ {db_name}: {status['size_mb']}MB")
        else:
            print(f"  ⚠️  {db_name}: 文件不存在")
    
    # 生成健康报告
    health_report = {
        "timestamp": datetime.now().isoformat(),
        "application": app_health,
        "system_resources": resources,
        "processes": processes,
        "databases": db_status
    }
    
    # 保存报告
    try:
        with open('/var/log/sentiment-analysis/health_report.json', 'w') as f:
            json.dump(health_report, f, indent=2)
        print("\n📋 健康报告已保存到: /var/log/sentiment-analysis/health_report.json")
    except Exception as e:
        print(f"\n❌ 无法保存健康报告: {e}")
    
    # 返回状态码
    if (app_health["status"] == "healthy" and 
        gunicorn_count > 0 and 
        nginx_count > 0 and
        "error" not in resources):
        print("\n🎉 系统整体状态: 健康")
        return 0
    else:
        print("\n⚠️  系统整体状态: 需要关注")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)






