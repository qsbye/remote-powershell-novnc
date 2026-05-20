# HTTP Shell CLI + VNC - 远程 Shell & 桌面工具

基于 HTTP 协议的远程 Shell 执行系统，集成 noVNC 远程桌面功能。通过 Go 语言编写的单文件可执行程序，在工控机侧启动 HTTP 服务端接收命令和提供 VNC 远程桌面，在开发机侧启动客户端实现类似 SSH 的交互式体验。

**当前版本 v2.4**：在 v2.3 基础上增强 VNC 兼容性，支持自动检测并使用系统中已运行的其他 VNC Server。

---

## 功能特性

- **零依赖部署**：单文件可执行程序，无需安装运行时
- **双角色一体**：同一个程序既可当服务端也可当客户端
- **Shell 自动检测**：按 `pwsh → powershell → cmd` 优先级检测 Windows Shell
- **编码自适应**：自动处理 Windows GBK/UTF-8 编码问题
- **命令超时控制**：超时后主动 Kill 进程
- **CORS 跨域支持**：允许浏览器端直接调用 API
- **文件上传/下载**：通过 multipart/form-data 实现文件传输
- **rsync 双向增量同步**：
  - `rsync` 命令：本地→远程增量同步（上传）
  - `rsync-pull` 命令：远程→本地增量拉取（下载）
  - 基于 Adler-32 + MD5 双阶段校验的块级 delta 同步
  - 传输失败自动回退到全量传输
- **RFB 文件传输**：支持断点续传（offset 参数）、MD5 校验、目录列表
- **服务端日志**：自动记录操作日志到 `http_shell_cli_{yyyyMMddHHmmssfff}.log`
- **VNC 远程桌面**（Windows 服务端）：
  - **兼容已有 VNC Server**：自动检测 RealVNC/TightVNC/UltraVNC 等（端口 5900-5909, 15900-15909），直接复用
  - 内嵌 TightVNC Server，无其他 VNC 时自动释放并运行
  - 内嵌 noVNC 1.4.0，浏览器直接访问
  - WebSocket 代理桥接，无需额外配置
  - 自动检测并递增端口避免冲突

---

## 项目结构

```
http_shell_cli_vnc/
├── http_shell_cli_vnc.go      # 主程序（服务端+客户端+rsync+RFB+VNC）
├── http_shell_cli_windows.go  # Windows 平台专用（GBK转码、VT颜色、隐藏窗口）
├── http_shell_cli_unix.go     # Unix/Linux/macOS 平台空实现
├── public_fs/
│   ├── public_fs.go           # embed 静态文件定义
│   ├── novnc/                 # noVNC 1.4.0 前端文件
│   └── tvnc/                  # TightVNC Server 二进制
│       ├── tvnserver.exe
│       ├── hookldr.exe
│       ├── screenhooks32.dll
│       ├── screenhooks64.dll
│       └── tvnviewer.exe
├── vnc_proxy/
│   ├── proxy.go               # WebSocket VNC 代理
│   └── peer.go                # VNC 连接对等体
├── go.mod                     # Go 模块定义
├── go.sum                     # Go 依赖校验
├── build.ps1                  # PowerShell 打包脚本（带时间戳）
├── build.bat                  # CMD 打包脚本（带时间戳）
└── README.md                  # 本文档
```

---

## 快速开始

### 1. 初始化并编译

```bash
# 进入项目目录
cd http_shell_cli_vnc

# 下载依赖
go mod tidy

# 编译当前平台版本
go build -o http_shell_cli_vnc.exe .

# 或使用打包脚本（自动添加时间戳后缀）
.\build.ps1        # PowerShell
.\build.bat        # CMD
```

打包脚本会生成带时间戳的可执行文件，例如：`http_shell_cli_vnc_20260519_132801.exe`

### 2. 启动服务端（工控机）

```bash
# 交互式选择角色
.\http_shell_cli_vnc.exe

# 或直接指定角色
.\http_shell_cli_vnc.exe -role server -host 0.0.0.0 -port 10022
```

Windows 服务端启动时会自动：
1. **检测是否已有 VNC Server 运行**（兼容模式）
   - 扫描端口 5900-5909 和 15900-15909
   - 如果检测到 RealVNC/TightVNC/UltraVNC 等，直接复用，跳过注册表和 tvnserver 启动
2. 无其他 VNC 时，进入内嵌模式：
   - 检测并递增 RFB 端口（默认 15900）避免冲突
   - 释放内嵌的 TightVNC Server 到 `.cache/tvnc/`
   - 写入注册表配置（需要管理员权限）
   - 启动 tvnserver 服务
3. 启动 noVNC HTTP 服务和 WebSocket 代理

### 3. 连接客户端（开发机）

```bash
# 交互式模式（类似 SSH）
.\http_shell_cli_vnc.exe -role client -url http://192.168.1.100:10022

# 单次执行模式
.\http_shell_cli_vnc.exe -role client -url http://192.168.1.100:10022 -c "Get-Location"
```

### 4. 访问 VNC 远程桌面

在浏览器中打开：
```
http://192.168.1.100:10022/vnc/vnc.html
```

无需密码，直接连接即可看到远程桌面。

---

## API 接口

### POST /exec

执行 Shell 命令。

**请求体：**
```json
{
  "command": "Get-ChildItem",
  "timeout": 30,
  "work_dir": "C:\\Users"
}
```

**响应：**
```json
{
  "status": "success",
  "stdout": "...",
  "stderr": "",
  "exit_code": 0,
  "timeout": false,
  "command": "Get-ChildItem"
}
```

### POST /upload

上传文件到服务端。

**参数：**
- `file` (file, 必填)：要上传的文件
- `path` (string, 可选)：服务端保存路径

**curl 示例：**
```bash
curl -X POST http://192.168.1.100:10022/upload \
  -F "file=@local.txt" \
  -F "path=C:/remote/dir/"
```

### POST /download

从服务端下载文件。

**参数：**
- `path` (string, 必填)：服务端文件路径

**curl 示例：**
```bash
curl -X POST http://192.168.1.100:10022/download \
  -F "path=C:/remote/dir/file.txt" \
  -o local.txt
```

### Rsync 增量同步接口

#### POST /rsync/blockset

获取文件块集合。

**请求体：**
```json
{
  "path": "/remote/file.dat",
  "seed": 12345
}
```

#### POST /rsync/delta

计算增量数据。

**Push 模式（默认）：**
```json
{
  "src_path": "/local/file.dat",
  "dst_path": "/remote/file.dat",
  "seed": 12345
}
```

**Pull 模式：**
```json
{
  "src_path": "/remote/file.dat",
  "dst_path": "/local/file.dat",
  "seed": 12345,
  "direction": "pull",
  "local_bs": { ... }
}
```

#### POST /rsync/apply

应用增量数据重建文件。

**请求体：**
```json
{
  "dst_path": "/remote/file.dat",
  "src_path": "/remote/file.dat",
  "chunks": [
    {"op": 1, "length": 256, "data": "..."},
    {"op": 2, "length": 5},
    {"op": 0}
  ]
}
```

### RFB 文件传输接口

#### POST /rfb/file/list

列出远程目录内容。

#### POST /rfb/file/download

下载文件（支持断点续传）。

**请求体：**
```json
{
  "path": "/remote/file.dat",
  "offset": 0
}
```

#### POST /rfb/file/upload

上传文件（支持断点续传）。

**参数：**
- `file` (file, 必填)
- `path` (string, 必填)
- `offset` (string, 可选)

#### POST /rfb/file/md5

计算文件 MD5 校验值。

### VNC 远程桌面接口

#### GET /vnc/

noVNC 静态文件服务。访问 `/vnc/vnc.html` 打开远程桌面页面。

#### GET /websockify

VNC WebSocket 代理端点。noVNC 通过此端点与 TightVNC Server 通信。

### GET /health

检查服务状态。

---

## 客户端内置命令

| 命令 | 说明 |
|------|------|
| `exit`, `quit`, `q` | 退出客户端 |
| `cd <目录>` | 设置后续命令的工作目录 |
| `pwd` | 显示当前工作目录 |
| `clear`, `cls` | 清屏 |
| `!<命令>` | 执行本地命令（不发送到服务端） |
| `upload <本地路径> [远程路径]` | 上传文件 |
| `download <远程路径> [本地路径]` | 下载文件 |
| `rsync <本地路径> [远程路径]` | rsync 增量同步（本地→远程） |
| `rsync-pull <远程路径> [本地路径]` | rsync 增量拉取（远程→本地） |
| `rfb-upload <本地路径> [远程路径]` | RFB 断点续传上传 |
| `rfb-download <远程路径> [本地路径]` | RFB 断点续传下载 |
| `rfb-list [目录]` | RFB 列出远程目录 |
| `help`, `?` | 显示帮助 |

---

## VNC 远程桌面说明

### 工作原理

```
浏览器(noVNC)  <--WebSocket-->  /websockify  <--TCP-->  VNC Server(127.0.0.1:5900+ 或 15900+)
```

1. 服务端启动时，优先检测系统中是否已有 VNC Server（端口 5900-5909, 15900-15909）
2. 如果检测到已有 VNC Server，直接进入兼容模式，WebSocket 代理连接到已有服务
3. 如果没有检测到，释放内嵌的 TightVNC Server 到 `.cache/tvnc/`，写入注册表，启动 tvnserver
4. HTTP 服务提供 noVNC 静态页面（`/vnc/`）
5. WebSocket 代理（`/websockify`）桥接浏览器与 VNC Server

### 端口说明

| 服务 | 默认端口 | 说明 |
|------|----------|------|
| HTTP Shell | 10022 | 主 HTTP 服务端口（可配置） |
| VNC RFB | 15900 | TightVNC Server 端口（自动递增） |
| VNC HTTP | 9091 | noVNC 页面端口（与主服务复用） |

### 注意事项

- **仅 Windows 服务端支持 VNC**：Linux/macOS 服务端不启动 VNC 相关组件
- **兼容已有 VNC Server**：支持 RealVNC、TightVNC、UltraVNC 等，无需管理员权限即可复用
- **内嵌模式需要管理员权限**：首次运行内嵌 TightVNC 需要管理员权限写入注册表和安装服务
- **端口冲突自动处理**：如果 15900 被占用，自动递增到可用端口
- **VNC 服务监控**：如果内嵌 tvnserver 进程意外退出，程序会自动退出

---

## Rsync 增量同步原理

### 块大小计算

```
块大小 = max(700, ceil(sqrt(文件大小)) 向上取整到 8 的倍数)
```

| 文件大小 | 块大小 | 块数量 |
|---------|--------|--------|
| 100 KB | 700 B | 147 |
| 1 MB | 1,024 B | 1,024 |
| 10 MB | 2,048 B | 5,120 |
| 100 MB | 3,600 B | 28,445 |
| 1 GB | 8,192 B | 131,072 |

### 双阶段校验和

| 阶段 | 校验和 | 长度 | 用途 |
|------|--------|------|------|
| 第一阶段 | Adler-32 滚动校验和 | 4 字节 | 快速滚动比较，O(1) 滑动窗口更新 |
| 第二阶段 | MD5 强校验和 | 16 字节 | 强验证，混入随机种子防止哈希碰撞 |

### 自动回退机制

rsync 在以下情况自动回退到全量传输：
- 远程文件不存在
- blockset 获取失败 / delta 计算失败 / apply 失败
- MD5 验证不匹配
- 增量效率 < 20%（且文件 > 1MB）

---

## 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `HTTP_SHELL_PORT` | `10022` | 服务端监听端口 |
| `HTTP_SHELL_HOST` | `0.0.0.0` | 服务端监听地址 |
| `HTTP_SHELL_TIMEOUT` | `30` | 默认命令超时秒数 |

---

## 更新日志

### v2.4
- 增强 VNC 兼容性：自动检测并使用系统中已运行的 VNC Server
- 支持 RealVNC、TightVNC、UltraVNC 等常见 VNC 服务端
- 无需管理员权限即可在已有 VNC 环境下运行

### v2.3
- 新增 VNC 远程桌面功能（TightVNC Server + noVNC + WebSocket 代理）
- 服务端启动时自动初始化 VNC 服务（Windows）
- 打包脚本添加时间戳后缀

### v2.2
- 新增服务端日志功能，自动记录到时间戳命名的 `.log` 文件

### v2.1
- 新增 rsync 双向增量同步
- 新增 RFB 文件传输协议（含断点续传）

---

## 适用场景

- 离线内网工控机远程维护
- 无法安装 SSH 的封闭系统
- 临时性的命令执行需求
- 跨平台（Windows/Linux）统一工具
- 大文件增量同步（rsync 模式）
- 不稳定网络下的文件传输（RFB 断点续传模式）
- **需要图形化远程桌面的工控机维护**（VNC 模式）

## 不适用场景

- 公网暴露的生产环境
- 高并发批量命令执行
- 需要交互式 TUI 程序（如 vim）

---

## 安全提示

本服务设计用于**离线内网环境**，不提供身份认证。如需增强安全性，建议：
- 在前端增加反向代理（如 Nginx）配置 Basic Auth 或 IP 白名单
- 通过 VPN 或专线传输
- 对敏感文件传输启用 TLS（HTTPS）
- VNC 远程桌面默认无密码，建议在受控网络中使用

---

## 打包说明

### 使用脚本打包

```powershell
# PowerShell
.\build.ps1

# CMD
.\build.bat
```

输出示例：`http_shell_cli_vnc_20260519_132801.exe`（约 12MB）

### 手动打包

```bash
# 整理依赖
go mod tidy

# 编译（带时间戳）
go build -ldflags "-s -w" -o http_shell_cli_vnc_$(date +%Y%m%d_%H%M%S).exe .
```

### 交叉编译

```bash
# 交叉编译 Windows 版本（在 Linux/macOS 上）
GOOS=windows GOARCH=amd64 go build -ldflags "-s -w" -o http_shell_cli_vnc.exe .

# 交叉编译 Linux 版本
GOOS=linux GOARCH=amd64 go build -ldflags "-s -w" -o http_shell_cli_vnc .
```

---

## 依赖说明

| 依赖 | 用途 |
|------|------|
| `golang.org/x/net/websocket` | noVNC WebSocket 代理 |
| `golang.org/x/sys/windows/registry` | Windows 注册表操作（VNC 配置） |
| `golang.org/x/text/encoding/simplifiedchinese` | Windows GBK 编码转换 |
| `github.com/evangwt/go-bufcopy` | VNC 代理数据拷贝 |
| `github.com/pkg/errors` | 错误处理增强 |

---

## License

MIT License
