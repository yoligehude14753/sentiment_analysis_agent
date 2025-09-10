#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Linux兼容性测试脚本
测试代码在Linux环境下的兼容性问题
"""

import os
import sys
import platform
import subprocess
import tempfile
from pathlib import Path

def test_path_operations():
    """测试路径操作兼容性"""
    print("🔍 测试路径操作兼容性...")
    
    # 测试路径分隔符
    test_path = Path("data") / "test.db"
    print(f"✓ Path操作正常: {test_path}")
    
    # 测试临时目录
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        print(f"✓ 临时目录创建正常: {temp_path}")
    
    return True

def test_file_permissions():
    """测试文件权限操作"""
    print("🔍 测试文件权限操作...")
    
    try:
        # 创建测试文件
        test_file = Path("test_permissions.txt")
        test_file.write_text("test content")
        
        # 在Linux下设置权限
        if platform.system() != "Windows":
            os.chmod(test_file, 0o644)
            print("✓ 文件权限设置正常")
        else:
            print("✓ Windows环境，跳过权限测试")
        
        # 清理
        test_file.unlink()
        return True
        
    except Exception as e:
        print(f"❌ 文件权限测试失败: {e}")
        return False

def test_environment_variables():
    """测试环境变量处理"""
    print("🔍 测试环境变量处理...")
    
    # 测试常见环境变量
    env_vars = ["HOME", "USER", "PATH"]
    for var in env_vars:
        value = os.environ.get(var, "未设置")
        print(f"  {var}: {value}")
    
    # 测试设置临时环境变量
    os.environ["TEST_VAR"] = "test_value"
    if os.environ.get("TEST_VAR") == "test_value":
        print("✓ 环境变量设置正常")
        del os.environ["TEST_VAR"]
        return True
    else:
        print("❌ 环境变量设置失败")
        return False

def test_subprocess_operations():
    """测试子进程操作"""
    print("🔍 测试子进程操作...")
    
    try:
        # 测试基本命令
        if platform.system() == "Windows":
            result = subprocess.run(["dir"], shell=True, capture_output=True, text=True)
        else:
            result = subprocess.run(["ls"], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✓ 子进程执行正常")
            return True
        else:
            print(f"❌ 子进程执行失败: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ 子进程测试失败: {e}")
        return False

def test_python_imports():
    """测试Python模块导入"""
    print("🔍 测试关键模块导入...")
    
    modules_to_test = [
        "fastapi",
        "uvicorn", 
        "pandas",
        "sqlite3",
        "pathlib",
        "tempfile",
        "json",
        "datetime",
        "logging"
    ]
    
    failed_imports = []
    for module in modules_to_test:
        try:
            __import__(module)
            print(f"✓ {module}")
        except ImportError as e:
            print(f"❌ {module}: {e}")
            failed_imports.append(module)
    
    return len(failed_imports) == 0

def test_database_path():
    """测试数据库路径处理"""
    print("🔍 测试数据库路径处理...")
    
    try:
        # 测试相对路径
        db_path = Path("data/sentiment_analysis.db")
        print(f"✓ 数据库路径: {db_path.absolute()}")
        
        # 确保目录存在
        db_path.parent.mkdir(exist_ok=True)
        print(f"✓ 数据目录创建: {db_path.parent}")
        
        return True
        
    except Exception as e:
        print(f"❌ 数据库路径测试失败: {e}")
        return False

def test_file_encoding():
    """测试文件编码处理"""
    print("🔍 测试文件编码处理...")
    
    try:
        # 测试UTF-8编码
        test_content = "测试中文内容 Test English Content 🎉"
        test_file = Path("test_encoding.txt")
        
        # 写入UTF-8文件
        test_file.write_text(test_content, encoding='utf-8')
        
        # 读取验证
        read_content = test_file.read_text(encoding='utf-8')
        
        if read_content == test_content:
            print("✓ UTF-8编码处理正常")
            test_file.unlink()  # 清理
            return True
        else:
            print("❌ UTF-8编码处理失败")
            return False
            
    except Exception as e:
        print(f"❌ 文件编码测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 60)
    print("🐧 Linux兼容性测试开始")
    print("=" * 60)
    print(f"当前系统: {platform.system()} {platform.release()}")
    print(f"Python版本: {sys.version}")
    print(f"当前目录: {Path.cwd()}")
    print("=" * 60)
    
    tests = [
        ("路径操作", test_path_operations),
        ("文件权限", test_file_permissions), 
        ("环境变量", test_environment_variables),
        ("子进程操作", test_subprocess_operations),
        ("模块导入", test_python_imports),
        ("数据库路径", test_database_path),
        ("文件编码", test_file_encoding)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 40)
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} - 通过")
            else:
                failed += 1
                print(f"❌ {test_name} - 失败")
        except Exception as e:
            failed += 1
            print(f"💥 {test_name} - 异常: {e}")
    
    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)
    print(f"✅ 通过: {passed}")
    print(f"❌ 失败: {failed}")
    print(f"📈 成功率: {passed/(passed+failed)*100:.1f}%")
    
    if failed == 0:
        print("\n🎉 所有测试通过！代码具有良好的Linux兼容性")
        return True
    else:
        print(f"\n⚠️  有 {failed} 个测试失败，需要修复兼容性问题")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)


