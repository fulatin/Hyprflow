# Hyperflow: Hyprland 可视化自动化助手

Hyperflow 是一个为 Hyprland 设计的可视化自动化助手，旨在让每个人都能够轻松实现窗口管理器自动化。通过简单的图形界面编辑器和强大的后台程序，您可以创建复杂的自动化工作流。

## 特性

- **可视化规则编辑器**：通过拖放式图形界面创建自动化规则
- **实时事件处理**：即时响应 Hyprland 事件
- **灵活的触发器**：支持各种 Hyprland 事件（窗口打开/关闭、工作区更改等）
- **条件逻辑**：应用条件来微调操作执行时机
- **可扩展的操作**：执行任何 shell 命令，包括 `hyprctl` 命令
- **热重载配置**：无需重启后台程序即可重新加载规则
- **自动配置监控**：后台程序会自动检测 workflow.json 的更改并重新加载配置
- **双击编辑规则**：在编辑器中双击任意规则即可快速编辑

## 安装

1. 克隆仓库：
   ```
   git clone https://github.com/fulatin/Hyprflow
   cd hyperflow
   ```

2. 安装依赖：
   ```
   pip install -r requirements.txt
   ```

## 使用方法

HyperFlow 有三个可以通过主入口访问的主要组件：

### 运行后台程序

后台程序监听 Hyprland 事件并执行您的自动化规则：

```
python main.py daemon
```

### 启动图形界面编辑器

使用可视化编辑器创建和编辑自动化规则：

```
python main.py editor
```

### 使用命令行界面

通过命令行界面管理后台程序：

```
python main.py cli [子命令]
```

CLI 子命令：
- `start`：启动 Hyperflow 后台程序
- `stop`：停止 Hyperflow 后台程序
- `restart`：重启 Hyperflow 后台程序
- `status`：显示后台程序状态
- `reload`：重新加载后台程序配置

## 工作原理

Hyperflow 通过连接 Hyprland 的 IPC 套接字提供自动化功能：

1. **事件监听**：连接到 Hyprland 的 `.socket2.sock` 以接收实时事件
2. **规则匹配**：将事件与您配置的规则进行比较
3. **操作执行**：当规则匹配时通过 `subprocess` 执行命令

## 配置

规则存储在 `~/.config/hyperflow/workflows.json` 中。每条规则包含：

- **触发器**：激活规则的事件（例如，`openwindow`）
- **条件**：必须满足的附加条件（例如，窗口类等于 "spotify"）
- **操作**：规则匹配时要执行的命令（例如，`hyprctl dispatch movetoworkspace 5`）

示例规则：
```json
{
  "id": "wf_001",
  "name": "自动将 Spotify 移至工作区 5",
  "enabled": true,
  "trigger": {
    "type": "openwindow",
    "debounce": 100
  },
  "conditions": [
    {
      "property": "class",
      "operator": "equals",
      "value": "spotify"
    }
  ],
  "actions": [
    {
      "command": "hyprctl dispatch movetoworkspace 5"
    }
  ]
}
```