# by zhlhlf

import requests
import json
from tabulate import tabulate
import subprocess
import argparse

# 默认Alist配置（用于恢复操作）
DEFAULT_ALIST_URL = "http://127.0.0.1:5244"
DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD = "admin"

def reset_password(password):
    """重置本地Alist管理员密码"""
    try:
        subprocess.check_call(["./alist", "admin", "set", password])
        print(f"密码重置成功：{password}")
    except Exception as e:
        print(f"密码重置失败: {e}")

def login(host, username, password):
    """登录获取访问令牌"""
    login_url = f"{host}/api/auth/login"
    try:
        response = requests.post(login_url, json={"username": username, "password": password})
        response.raise_for_status()
        return response.json()["data"]["token"]
    except requests.exceptions.RequestException as e:
        raise Exception(f"登录失败: {str(e)}")

# 存储管理功能
def add_storage(token, host, storage_data, verbose=True):
    """添加存储"""
    url = f"{host}/api/admin/storage/create"
    try:
        response = requests.post(
            url,
            headers={"Authorization": token, "Content-Type": "application/json"},
            json=storage_data
        )
        response.raise_for_status()
        if verbose:
            print(f"存储添加成功：{storage_data['mount_path']}")
        return True
    except requests.exceptions.RequestException as e:
        if verbose:
            print(f"存储添加失败 [{storage_data['mount_path']}]: {str(e)}")
        return False

def get_storage_list(token, host):
    """获取存储列表"""
    url = f"{host}/api/admin/storage/list"
    try:
        response = requests.get(url, headers={"Authorization": token})
        response.raise_for_status()
        return response.json()["data"]["content"]
    except requests.exceptions.RequestException as e:
        raise Exception(f"获取存储列表失败: {str(e)}")

# 用户管理功能
def add_user(token, host, user_data, verbose=True):
    """添加用户"""
    url = f"{host}/api/admin/user/create"
    try:
        response = requests.post(
            url,
            headers={"Authorization": token, "Content-Type": "application/json"},
            json=user_data
        )
        response.raise_for_status()
        if verbose:
            print(f"用户添加成功：{user_data['username']}")
        return True
    except requests.exceptions.RequestException as e:
        if verbose:
            print(f"用户添加失败 [{user_data['username']}]: {str(e)}")
        return False

def get_user_list(token, host):
    """获取用户列表"""
    url = f"{host}/api/admin/user/list"
    try:
        response = requests.get(url, headers={"Authorization": token})
        response.raise_for_status()
        return response.json()["data"]["content"]
    except requests.exceptions.RequestException as e:
        raise Exception(f"获取用户列表失败: {str(e)}")

def update_admin_user(token, host, username):
    """更新管理员账户配置"""
    url = f"{host}/api/admin/user/update"
    admin_data = {
        "id": 1,
        "username": username,
        "password": "",
        "base_path": "/",
        "role": 2,
        "permission": 16383,
        "disabled": False,
        "sso_id": ""
    }
    try:
        response = requests.post(
            url,
            headers={"Authorization": token, "Content-Type": "application/json"},
            json=admin_data
        )
        response.raise_for_status()
        print("管理员账户更新成功")
        return True
    except requests.exceptions.RequestException as e:
        print(f"管理员更新失败: {str(e)}")
        return False

# 备份恢复功能
def backup_data(host, username, password):
    """执行备份操作"""
    try:
        token = login(host, username, password)
        print("备份数据收集中...")
        
        backup = {
            "storages": get_storage_list(token, host),
            "users": get_user_list(token, host)
        }
        
        with open('alist_backup.json', 'w', encoding='utf-8') as f:
            json.dump(backup, f, ensure_ascii=False, indent=4)
        
        print("备份完成：alist_backup.json")
        return True
    except Exception as e:
        print(f"备份失败: {str(e)}")
        return False

def restore_data(host, username, password):
    """执行恢复操作"""
    try:
        # 重置本地管理员密码
        reset_password(password)
        
        # 获取访问令牌
        token = login(host, username, password)
        
        print("开始恢复数据...")
        with open('alist_backup.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 恢复存储
        restored_storages = []
        for storage in data.get("storages", []):
            storage_data = {k: storage[k] for k in [
                "mount_path", "order", "driver", "cache_expiration", "status",
                "addition", "remark", "disabled", "enable_sign", "order_by",
                "order_direction", "extract_folder", "web_proxy", "webdav_policy",
                "proxy_range", "down_proxy_url"
            ]}
            if add_storage(token, host, storage_data, verbose=False):
                restored_storages.append(storage_data['mount_path'])
        
        # 恢复用户
        restored_users = []
        for user in data.get("users", []):
            user_data = {k: user[k] for k in [
                "username", "password", "role", "permission", "base_path",
                "disabled"
            ]}
            if add_user(token, host, user_data, verbose=False):
                restored_users.append(user_data['username'])
        
        # 显示汇总结果
        print("\n恢复结果汇总:")
        if restored_storages:
            print(f"成功恢复存储({len(restored_storages)}个):", " ".join(restored_storages))
        else:
            print("没有存储被恢复")
            
        if restored_users:
            print(f"成功恢复用户({len(restored_users)}个):", " ".join(restored_users))
        else:
            print("没有用户被恢复")
        
        # 更新管理员账户
        update_admin_user(token, host, username)
        
        print("\n恢复操作完成")
        return True
    except Exception as e:
        print(f"恢复失败: {str(e)}")
        return False

def main():
    # 命令行参数解析
    parser = argparse.ArgumentParser(description='Alist备份恢复工具')
    parser.add_argument('--host', help='Alist服务器地址（示例：http://127.0.0.1:5244）')
    parser.add_argument('--username', help='管理员用户名')
    parser.add_argument('--password', help='管理员密码')
    args = parser.parse_args()
    
    # 检测备份参数
    if all([args.host, args.username, args.password]):
        print("进入备份模式")
        backup_data(
            host=args.host.rstrip('/'),
            username=args.username,
            password=args.password
        )
    else:
        print("进入恢复模式（使用本地配置）")
        restore_data(
            host=DEFAULT_ALIST_URL,
            username=DEFAULT_USERNAME,
            password=DEFAULT_PASSWORD
        )

if __name__ == "__main__":
    # 检查依赖安装
    try:
        from tabulate import tabulate
    except ImportError:
        print("安装必要依赖：tabulate")
        subprocess.check_call(["pip", "install", "tabulate"])
    
    main()