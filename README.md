# Deprecate - ReOrc MCP Client 

Client for ReOrc's Model Creation Platform (MCP).

## Installation

### Prerequisites

Before installing the ReOrc MCP Client, ensure you have the following:

1. **Cursor IDE** - Download and install from [cursor.sh](https://cursor.sh)
2. **Python 3.12** - Download from [python.org](https://python.org) or install via your system package manager
3. **ReOrc Studio Account** - Ensure you have access to ReOrc Studio with appropriate permissions

### Installation Steps

#### 1. Clone the Repository

```bash
git clone https://github.com/reorc/reorc-mcp.git
cd reorc-mcp
```

#### 2. Install Dependencies

```bash
# Install required Python packages
pip install -r requirements.txt
```

The tool requires:
- `requests>=2.28.0` - For API communication
- `PyYAML>=6.0` - For YAML processing

#### 3. Configure ReOrc Studio MCP Settings

1. Open **ReOrc Studio** in your browser
2. Click the user icon (bottom left corner)
3. Navigate to **Profile** → **ReOrc MCP Settings**
4. Copy the **MCP Access Code** (in JSON) from this page

#### 4. Configure Cursor MCP Integration

1. Open **Cursor IDE**
2. Go to **Settings** (Cmd/Ctrl + Comma)
3. Navigate to **Cursor Settings** → **Tools & Integrations** → **MCP Tools**
4. Click **New MCP Server**, which opens a JSON file
5. Paste the JSON code from Step 3 above, and save
6. Cursor may notify registration of the new MCP, and ask for enabling (on bottom left)

#### 5. Verify Installation

Test your installation by running:

```bash
# Validate your authentication
python3 cli.py auth validate

# If validation fails, login to get a new token
python3 cli.py auth login
```

### Configuration File

The MCP configuration is stored in `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "reorc-mcp": {
      "transport": "sse",
      "url": "https://mcp.test.reorc.cloud/mcp?access_token={YOUR_ACCESS_TOKEN}"
    }
  },
  "auth": {
    "defaultCredentials": {
      "email": "{YOUR_REORC_ACCOUNT}",
      "password": "{YOUR_REORC_PASSWORD}",
      "tenant_domain": "{TENANT_DOMAIN}"
    }
  }
}
```

### Troubleshooting

If you encounter issues:

1. **Authentication Problems**: Run `python3 cli.py auth validate` to check your token
2. **Missing Dependencies**: Ensure all packages are installed with `pip install -r requirements.txt`
3. **Python Version**: Verify you're using Python 3.12 with `python3 --version`
4. **Cursor Integration**: Try refreshing the MCP server in Cursor settings

## Getting Started

After completing the installation, you can start using ReOrc MCP Client directly within Cursor IDE. Here's a quick guide to get you up and running:

### Quick Start Commands

Open Cursor IDE and use the chat interface to interact with ReOrc MCP. You can ask Cursor to:

#### 1. List Available Projects
```
List all my ReOrc projects
```

#### 2. Download a Project Locally
```
Download project "my_project_code" locally
```

#### 3. Create a Data Model
```
Create a new staging model called "stg_customers" for project "my_project_code" that selects all customers from the raw customers table
```

#### 4. Preview Data Model
```
Preview the data from model "stg_customers" in project "my_project_code"
```

#### 5. Build Data Model
```
Build model "stg_customers" in project "my_project_code"
```

### Example Workflow

1. **Start a conversation in Cursor**: Open Cursor's chat and ask to list your projects
2. **Download a project**: Ask Cursor to download the project you want to work on
3. **Create models**: Describe what kind of data model you want to create
4. **Preview and iterate**: Preview your models to see the data before building
5. **Build and deploy**: Build your models to make them available in your data warehouse

### Video Tutorial

For a comprehensive walkthrough on building data foundations with ReOrc via Cursor, watch our tutorial video:
📺 [**Building Data Foundation with ReOrc via Cursor**](https://www.youtube.com/watch?v=kJ4GZFVPsfU)

### Tips for Success

- **Be descriptive**: When asking Cursor to create models, describe your business logic clearly
- **Use natural language**: You don't need to know SQL - describe what you want in plain English
- **Iterate locally**: Use the local-first approach to make changes and test before syncing to the server
- **Preview first**: Always preview your models before building them to catch issues early

## Overview

ReOrc MCP Client is a client-side application that interacts with the ReOrc Studio server while empowering users to take full control of model authoring, plan validation, and quality assurance in their local environment.

## Local-First Development Model

This client implements a local-first approach to model development, allowing users to:

1. **Create and modify models locally** before syncing with the server
2. **Track changes with Git** for better version control and collaboration
3. **Preview and validate plans** before applying them
4. **Roll back unwanted changes** easily
5. **Maintain transparency** in how models are modified

## Directory Structure

- `local-model-projects/` - Downloaded DBT projects for local editing
- `utils/` - Utilities for CLI operations using python3 to run
- `.cursor/` - Configuration for Cursor IDE integration

## CLI Usage

The client includes a command-line interface for working with local project files and Git repositories:

### File Operations

```bash
# List files in a project
python3 cli.py file list dbt_project_1 [--path models/staging]

# Read a file
python3 cli.py file read dbt_project_1 models/staging/stg_customers.sql

# Write to a file
python3 cli.py file write dbt_project_1 models/staging/stg_orders.sql --content "SELECT * FROM orders"
# Or pipe content
cat new_model.sql | python3 cli.py file write dbt_project_1 models/staging/stg_orders.sql

# Delete a file
python3 cli.py file delete dbt_project_1 models/staging/deprecated_model.sql
```

### Git Operations

```bash
# Initialize Git repository for a project
python3 cli.py git init dbt_project_1

# Check Git status
python3 cli.py git status dbt_project_1

# Commit changes
python3 cli.py git commit dbt_project_1 "Add new staging model for orders"

# Reset changes (soft reset by default)
python3 cli.py git reset dbt_project_1 
# Hard reset (discard all changes)
python3 cli.py git reset dbt_project_1 --hard
# Reset specific file
python3 cli.py git reset dbt_project_1 --file-path models/staging/stg_orders.sql

# View commit history
python3 cli.py git history dbt_project_1 --max-count 5
```

### Project Operations

```bash
# Sync local changes to the server
python3 cli.py project sync dbt_project_1 --plan-id my_plan_name

# Sync specific models only
python3 cli.py project sync dbt_project_1 --plan-id my_plan_name --models stg_orders,stg_customers

# Automatically commit changes after syncing
python3 cli.py project sync dbt_project_1 --plan-id my_plan_name --commit

# Skip confirmation prompt
python3 cli.py project sync dbt_project_1 --plan-id my_plan_name --yes
```

## MCP Server Connection

The client connects to the MCP server as configured in `.cursor/mcp.json`. This file contains:

```json
{
  "mcpServers": {
    "reorc-mcp": {
      "transport": "sse",
      "url": "https://mcp.test.reorc.cloud/mcp?access_token={YOUR_ACCESS_TOKEN}"
    }
  },
  "auth": {
    "defaultCredentials": {
      "email": "{YOUR_REORC_ACCOUNT}",
      "password": "{YOUR_REORC_PASSWORD}",
      "tenant_domain": "{TENANT_DOMAIN}"
    }
  }
}
```

## Complete End-to-End Workflow

### 1. Download and Initialize Project

```bash
# 1. Download the project files using CLI: 
python3 cli.py project download dbt_project_1

# 2. Extract the project files (happening automatically via CLI)

# 3. Initialize git repository in the project directory
python3 cli.py git init dbt_project_1
```

### 2. Create and Edit Models Locally

```bash
# Edit models using your preferred code editor
# OR use the CLI to write models:
python3 cli.py file write dbt_project_1 models/staging/stg_orders.sql --content "SELECT * FROM orders"

# Check status of your changes
python3 cli.py git status dbt_project_1

# Commit changes locally to track your work
python3 cli.py git commit dbt_project_1 "Update staging orders model"
```

### 3. Sync Changes to Server

```bash
# Sync all modified SQL models to the server
python3 cli.py project sync dbt_project_1 --plan-id my_plan_name

# Sync specific models and commit changes
python3 cli.py project sync dbt_project_1 --plan-id my_plan_name --models stg_orders --commit
```

### 4. Build and Test on Server

```bash
# In Cursor IDE: Call the build_data_model tool with your project_code and model_name
```

### 5. Roll Back if Needed

```bash
# Reset to the state before your changes using git
python3 cli.py git reset dbt_project_1 --hard

# Reset specific file only
python3 cli.py git reset dbt_project_1 --file-path models/staging/stg_orders.sql
```

## Development Workflow Benefits

1. **Local Development First**
   - Edit files in your preferred editor
   - Use version control to track changes
   - Test locally before syncing to server

2. **Transparent Change History**
   - See what changes are being made with git diff
   - Track revision history locally
   - Maintain control over when to sync

3. **Collaborative Workflow**
   - Multiple developers can work on different models
   - Changes are easily reviewable as git history
   - Sync only when ready to integrate with server

4. **Risk Mitigation**
   - Roll back changes easily with git
   - Verify changes before syncing to server
   - Maintain local backups of all model versions

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.


# reorc-mcp-client



