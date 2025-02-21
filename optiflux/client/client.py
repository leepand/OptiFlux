# optiflux/client/client.py

import os
import zipfile
import requests
from ..utils.file_utils import zip_directory
from ..config import SERVER_URL
import argparse


def deploy_code(local_path, env):
    """部署代码到远程服务器"""
    # 打包代码
    zip_path = os.path.join(local_path, "code.zip")
    zip_directory(local_path, zip_path)

    # 检查文件是否存在
    if not os.path.exists(zip_path):
        print("Error: Failed to create zip file.")
        return

    # 上传代码
    with open(zip_path, "rb") as f:
        files = {"file": f}
        data = {"env": env}  # 指定部署环境
        response = requests.post(f"{SERVER_URL}/deploy", files=files, data=data)

    # 清理临时文件
    os.remove(zip_path)

    # 检查响应
    if response.status_code == 200:
        print("Deployment successful!")
    else:
        print(f"Deployment failed: {response.text}")


def main():
    """命令行入口点"""
    parser = argparse.ArgumentParser(description="OptiFlux Client")
    parser.add_argument(
        "--path", required=True, help="Path to the local code directory"
    )
    parser.add_argument(
        "--env",
        required=True,
        choices=["dev", "preprod", "prod"],
        help="Target environment",
    )
    args = parser.parse_args()

    result = deploy_code(args.path, args.env)
    print(result)


if __name__ == "__main__":
    main()
