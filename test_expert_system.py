#!/usr/bin/env python3
"""
专家系统功能测试脚本
测试专家账号创建、登录、数据导入等功能
"""

import sys
import os
import requests
import json
from pathlib import Path

# 添加当前目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# API 基础URL
BASE_URL = "http://localhost:8000"

def test_expert_creation():
    """测试专家账号创建"""
    print("🔍 测试专家账号创建...")
    
    expert_data = {
        "name": "测试专家",
        "email": "test_expert@example.com",
        "password": "test123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/experts/", json=expert_data)
        if response.status_code == 200:
            expert = response.json()
            print(f"✅ 专家账号创建成功: ID={expert['id']}, 姓名={expert['name']}")
            return expert
        else:
            print(f"❌ 专家账号创建失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ 专家账号创建失败: {e}")
        return None

def test_expert_login(email, password):
    """测试专家登录"""
    print("🔍 测试专家登录...")
    
    login_data = {
        "email": email,
        "password": password
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/experts/login", json=login_data)
        if response.status_code == 200:
            login_result = response.json()
            print(f"✅ 专家登录成功: {login_result['expert']['name']}")
            return login_result
        else:
            print(f"❌ 专家登录失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ 专家登录失败: {e}")
        return None

def test_get_all_experts():
    """测试获取所有专家"""
    print("🔍 测试获取所有专家...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/experts/")
        if response.status_code == 200:
            experts = response.json()
            print(f"✅ 获取专家列表成功: 共 {len(experts)} 位专家")
            for expert in experts:
                print(f"   - {expert['name']} ({expert['email']})")
            return experts
        else:
            print(f"❌ 获取专家列表失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ 获取专家列表失败: {e}")
        return None

def test_data_import():
    """测试数据导入功能"""
    print("🔍 测试数据导入功能...")
    
    test_file_path = Path("test_data/dockerfile_test_with_expert.json")
    
    if not test_file_path.exists():
        print(f"❌ 测试数据文件不存在: {test_file_path}")
        return False
    
    try:
        with open(test_file_path, 'rb') as f:
            files = {'file': ('dockerfile_test_with_expert.json', f, 'application/json')}
            response = requests.post(f"{BASE_URL}/api/data-import/upload", files=files)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 数据导入成功:")
            print(f"   - 导入问题数: {result.get('imported_questions', 0)}")
            print(f"   - 导入回答数: {result.get('imported_answers', 0)}")
            print(f"   - 导入专家回答数: {result.get('imported_expert_answers', 0)}")
            return True
        else:
            print(f"❌ 数据导入失败: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ 数据导入失败: {e}")
        return False

def test_server_connection():
    """测试服务器连接"""
    print("🔍 测试服务器连接...")
    
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            print("✅ 服务器连接正常")
            return True
        else:
            print(f"❌ 服务器连接失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 服务器连接失败: {e}")
        return False

def main():
    """运行所有测试"""
    print("=" * 50)
    print("🚀 开始专家系统功能测试")
    print("=" * 50)
    
    # 1. 测试服务器连接
    if not test_server_connection():
        print("\n❌ 服务器未启动，请先启动后端服务")
        print("启动命令: cd backend && python run.py")
        return
    
    # 2. 测试专家账号创建
    expert = test_expert_creation()
    if not expert:
        print("\n❌ 专家账号创建失败，后续测试可能受影响")
    
    # 3. 测试专家登录
    if expert:
        login_result = test_expert_login(expert['email'], "test123")
        if not login_result:
            print("\n❌ 专家登录失败")
    
    # 4. 测试获取所有专家
    test_get_all_experts()
    
    # 5. 测试数据导入
    test_data_import()
    
    print("\n" + "=" * 50)
    print("🎉 专家系统功能测试完成")
    print("=" * 50)
    print("\n📋 手动测试步骤:")
    print("1. 启动前端: cd frontend && npm run serve")
    print("2. 访问 http://localhost:8080")
    print("3. 点击 '专家登录' 进行注册/登录")
    print("4. 测试专家面板、数据导入、专家管理等功能")

if __name__ == "__main__":
    main()
