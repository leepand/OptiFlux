# setup.py

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="optiflux",
    version="0.1.0",
    author="leepand",
    author_email="your.email@example.com",
    description="A lightweight MLOps tool for code deployment and management.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/leepand/OptiFlux",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "flask>=2.0.0",
        "requests>=2.26.0",
        "pydantic>=1.8.0",
        "gunicorn>=20.1.0",  # 新增核心依赖
        "python-dotenv>=0.19.0",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    entry_points={
        "console_scripts": [
            "optiflux-client=optiflux.client.client:main",
            "optiflux-server=optiflux.server.server:main",
            "optiflux=optiflux.cli:main",  # 注册命令行工具
        ],
    },
)
