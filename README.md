# OptiFlux - 轻量级 MLOps

OptiFlux 是一个轻量级的 MLOps 工具，旨在简化和优化机器学习模型的部署与管理。它提供了一个直观的命令行接口（CLI），帮助用户管理模型版本、从远程服务器推送和拉取模型，以及配置开发、预生产和生产环境。

## 主要功能

- **模型版本管理**：轻松管理不同版本的模型。
- **远程部署**：支持将模型推送到远程服务器或从远程服务器拉取模型。
- **环境配置**：便捷地配置开发（dev）、预生产（preprod）和生产（prod）环境。
- **命令行集成**：提供简单易用的命令行工具，支持各种操作。
- **轻量级**：依赖少，易于集成到现有工作流中。

## 安装

安装 OptiFlux 非常简单，只需运行以下命令：

```bash
pip install OptiFlux
```

## 使用指南

OptiFlux 提供了命令行接口（CLI）来管理模型和环境。以下是一些常用命令：

### 初始化环境

初始化一个新的环境配置文件：

```bash
optiflux init
```

这将创建一个包含默认配置的 `.env` 文件。你可以使用 `--file` 选项指定其他文件名。

### 创建新模型项目

创建一个新的模型项目：

```bash
optiflux create-project --name mymodel --version 1.0
```

这将为你的模型生成一个结构化的项目目录。

### 添加文件到暂存区

将文件添加到暂存区：

```bash
optiflux add path/to/file_or_directory
```

### 提交更改

提交更改：

```bash
optiflux commit -m "提交信息"
```

### 推送更改到远程服务器

将更改推送到远程服务器：

```bash
optiflux push remote_name model_name model_version --server server_name
```

### 从远程服务器拉取更改

从远程服务器拉取更改：

```bash
optiflux pull remote_name model_name model_version --server server_name
```

### 登录服务器

登录到服务器：

```bash
optiflux login username password --server server_name
```

### 管理服务器配置

列出所有服务器配置：

```bash
optiflux config list
```

添加新的服务器配置：

```bash
optiflux config add server_name server_url api_key
```

更新现有服务器配置：

```bash
optiflux config update server_name --url new_url --api_key new_api_key
```

删除服务器配置：

```bash
optiflux config remove server_name
```

## 配置文件

OptiFlux 使用 `servers.yaml` 文件来管理服务器配置。当你添加新的服务器配置时，该文件会自动生成。

示例 `servers.yaml` 文件：

```yaml
servers:
  server1:
    url: http://example.com:8913
    api_key: your_api_key
  server2:
    url: http://another-example.com:8913
    api_key: another_api_key
```

## 贡献指南

我们欢迎贡献！请阅读 [CONTRIBUTING.md](CONTRIBUTING.md) 了解如何开始贡献。

## 许可证

本项目采用 MIT 许可证，详情请参阅 [LICENSE](LICENSE) 文件。

## 支持

如果你遇到任何问题或有疑问，请在 [GitHub 仓库](https://github.com/leepand/OptiFlux) 中提交问题。

---

**OptiFlux** - 轻松简化你的 MLOps 工作流。