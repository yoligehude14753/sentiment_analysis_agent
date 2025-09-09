#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
检查API响应
"""

import requests
import json

def check_api():
    """检查API响应"""
    try:
        # 测试获取文章列表
        response = requests.get("http://localhost:8001/api/results/list?page=1&page_size=2")
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("API响应:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            if data.get('data'):
                first_item = data['data'][0]
                print(f"\n第一条数据的字段:")
                for key, value in first_item.items():
                    print(f"  {key}: {value}")
        else:
            print(f"错误: {response.text}")
            
    except Exception as e:
        print(f"异常: {e}")

if __name__ == "__main__":
    check_api()
