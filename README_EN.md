# OptiFlux - Lightweight MLOps Tool

OptiFlux is a lightweight MLOps tool designed to simplify the deployment and management of machine learning models. It provides a streamlined CLI for managing model versions, pushing and pulling models from remote servers, and configuring environments for development, pre-production, and production.

## Features

- **Model Versioning**: Easily manage different versions of your models.
- **Remote Deployment**: Push and pull models to/from remote servers.
- **Environment Configuration**: Configure different environments (dev, preprod, prod) with ease.
- **CLI Integration**: Simple and intuitive command-line interface for all operations.
- **Lightweight**: Minimal dependencies and easy to integrate into existing workflows.

## Installation

To install OptiFlux, simply run:

```bash
pip install OptiFlux
```

## Usage

OptiFlux provides a command-line interface (CLI) to manage your models and environments. Below are some common commands:

### Initialize Environment

To initialize a new environment configuration:

```bash
optiflux init
```

This will create a `.env` file with default configurations. You can specify a different file name using the `--file` option.

### Create a New Model Project

To create a new model project:

```bash
optiflux create-project --name mymodel --version 1.0
```

This will generate a structured project directory for your model.

### Add Files to Staging

To add files to the staging area:

```bash
optiflux add path/to/file_or_directory
```

### Commit Changes

To commit changes:

```bash
optiflux commit -m "Your commit message"
```

### Push Changes to Remote

To push changes to a remote server:

```bash
optiflux push remote_name model_name model_version --server server_name
```

### Pull Changes from Remote

To pull changes from a remote server:

```bash
optiflux pull remote_name model_name model_version --server server_name
```

### Login to Server

To login to a server:

```bash
optiflux login username password --server server_name
```

### Manage Server Configurations

To list all server configurations:

```bash
optiflux config list
```

To add a new server configuration:

```bash
optiflux config add server_name server_url api_key
```

To update an existing server configuration:

```bash
optiflux config update server_name --url new_url --api_key new_api_key
```

To remove a server configuration:

```bash
optiflux config remove server_name
```

## Configuration

OptiFlux uses a `servers.yaml` file to manage server configurations. This file is automatically created when you add a new server configuration.

Example `servers.yaml`:

```yaml
servers:
  server1:
    url: http://example.com:8913
    api_key: your_api_key
  server2:
    url: http://another-example.com:8913
    api_key: another_api_key
```

## Contributing

We welcome contributions! Please read our [CONTRIBUTING.md](CONTRIBUTING.md) for details on how to get started.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

If you encounter any issues or have questions, please open an issue on our [GitHub repository](https://github.com/leepand/OptiFlux).

---

**OptiFlux** - Simplify your MLOps workflow with ease.