#!/usr/bin/env python3
import argparse
import asyncio
import datetime
import json
import os
import sys
from typing import Dict, Any
import httpx

class AListBackup:
    def __init__(self, host: str, username: str, password: str):
        self.host = host.rstrip('/') + '/'  # 确保URL以/结尾
        self.username = username
        self.password = password
        self.client = httpx.AsyncClient()
        self.token = None

    async def login(self) -> str:
        """登录AList获取token"""
        url = f"{self.host}api/auth/login"
        payload = {"username": self.username, "password": self.password}
        
        try:
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            
            if data.get("code") != 200:
                raise Exception(f"Login failed: {data.get('message')}")
            
            self.token = data["data"]["token"]
            return self.token
        except httpx.HTTPError as e:
            raise Exception(f"HTTP error during login: {str(e)}")
        except Exception as e:
            raise Exception(f"Login error: {str(e)}")

    async def fetch_data(self, endpoint: str) -> Dict[str, Any]:
        """从AList API获取数据"""
        if not self.token:
            await self.login()
            
        url = f"{self.host}{endpoint}"
        headers = {"Authorization": self.token}
        
        try:
            response = await self.client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            if data.get("code") != 200:
                raise Exception(f"API error ({endpoint}): {data.get('message')}")
                
            return data["data"]["content"] if "content" in data["data"] else data["data"]
        except httpx.HTTPError as e:
            raise Exception(f"HTTP error fetching {endpoint}: {str(e)}")
        except Exception as e:
            raise Exception(f"Error fetching {endpoint}: {str(e)}")

    async def backup(self, output_file: str) -> str:
        """执行备份操作"""
        print(f"Starting AList backup to file: {output_file}")
        
        # 获取所有需要备份的数据
        endpoints = {
            "storages": "api/admin/storage/list",
            "settings": "api/admin/setting/list",
            "users": "api/admin/user/list",
            "metas": "api/admin/meta/list"
        }
        
        backup_data = {
            "backup_time": datetime.datetime.now().isoformat(),
            "alist_version": await self.get_alist_version()
        }
        
        for name, endpoint in endpoints.items():
            print(f"Fetching {name} data...")
            try:
                data = await self.fetch_data(endpoint)
                backup_data[name] = data
                print(f"Successfully fetched {name} data")
            except Exception as e:
                print(f"Warning: Failed to fetch {name}: {str(e)}")
                backup_data[name] = None
        
        # 保存到文件
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)
            print(f"Backup successfully saved to: {output_file}")
            return output_file
        except Exception as e:
            raise Exception(f"Failed to save backup file: {str(e)}")

    async def get_alist_version(self) -> str:
        """获取AList版本信息"""
        try:
            response = await self.client.get(f"{self.host}api/public/settings")
            response.raise_for_status()
            data = response.json()
            return data["data"].get("version", "unknown")
        except:
            return "unknown"

    async def close(self):
        """关闭HTTP客户端"""
        await self.client.aclose()

async def main():
    parser = argparse.ArgumentParser(description="AList Configuration Backup Tool")
    parser.add_argument("--host", required=True, help="AList server URL (e.g., http://localhost:5244)")
    parser.add_argument("--username", required=True, help="AList admin username")
    parser.add_argument("--password", required=True, help="AList admin password")
    parser.add_argument("--output-file", required=True, help="Output file path for backup")
    
    args = parser.parse_args()
    
    backup = AListBackup(args.host, args.username, args.password)
    
    try:
        await backup.backup(args.output_file)
    except Exception as e:
        print(f"Backup failed: {str(e)}", file=sys.stderr)
        sys.exit(1)
    finally:
        await backup.close()

if __name__ == "__main__":
    asyncio.run(main())