# optiflux/utils/file_utils.py

import os
import zipfile
from datetime import datetime
import platform


def zip_directory(source_dir, output_path):
    """将目录打包为zip文件"""
    with zipfile.ZipFile(output_path, "w") as zipf:
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                if file != os.path.basename(output_path):  # 避免打包自身
                    zipf.write(
                        os.path.join(root, file),
                        os.path.relpath(os.path.join(root, file), source_dir),
                    )


def unzip_file(zip_path, target_dir):
    """解压zip文件到目标目录"""
    with zipfile.ZipFile(zip_path, "r") as zipf:
        zipf.extractall(target_dir)


def ensure_dir_exists(dir_path):
    """确保目录存在"""
    os.makedirs(dir_path, exist_ok=True)


def data_dir_default():
    """

    :return: default data directory depending on the platform and environment variables
    """
    system = platform.system()
    if system == "Windows":
        base_path = os.path.join(os.environ.get("APPDATA"), "optiflux")
    else:
        base_path = os.path.join(os.path.expanduser("~"), ".optiflux")
    ensure_dir_exists(base_path)
    return base_path
