#!/usr/bin/env python3
# bundle_go_to_md.py
import os
from pathlib import Path

# 需要排除的文件后缀（支持子串匹配）
EXCLUDE_SUFFIX = {
    ".swp",          # Vim 临时文件
    ".tmp",          # 通用临时文件
    "~",             # 备份文件
}
# 需要排除的目录名
EXCLUDE_DIRS = {
    ".git",          # Git 仓库
    ".vs",           # Visual Studio
    "bin",           # 编译输出（可执行文件）
    "build",         # 构建缓存
    "target",        # 默认构建目录
    "node_modules",  # Node.js 依赖
    ".idea",         # JetBrains IDE
    "dist",          # 打包输出
}

def collect_go_files(root_dir: Path):
    """
    收集 root_dir 下所有 .go, go.mod, go.sum 文件，排除指定目录与临时文件
    返回: List[Tuple[相对路径, 绝对路径]]
    """
    go_files = []
    # 使用 os.walk 遍历目录，topdown=True 允许我们在遍历过程中修改 dirnames
    for dirpath, dirnames, filenames in os.walk(root_dir, topdown=True):
        # 过滤掉待排除目录（原地修改 dirnames，防止继续深入）
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]

        for file in filenames:
            full_path = Path(dirpath) / file
            # 排除带指定后缀的临时文件
            if any(file.endswith(sfx) for sfx in EXCLUDE_SUFFIX):
                continue
            # 保留 Go 源文件与模块配置文件
            if file.endswith(".go") or file in ("go.mod", "go.sum"):
                # 计算相对于根目录的路径，用于 Markdown 标题
                relative_path = full_path.relative_to(root_dir)
                go_files.append((relative_path, full_path))

    # 按相对路径排序，保证输出顺序稳定
    return sorted(go_files)

def build_md_content(go_files, root_name: str):
    """
    根据收集到的文件构建 Markdown 内容
    返回: 完整的 Markdown 字符串
    """
    lines = [f"# {root_name} Go Source Bundle\n\n"]
    for rel_path, full_path in go_files:
        try:
            # 尝试以 UTF-8 读取文件内容
            code = full_path.read_text(encoding="utf-8")
        except Exception as e:
            # 读取失败时，用注释记录错误信息
            code = f"// 读取失败: {e}"

        # 根据文件后缀决定代码高亮语言
        if rel_path.suffix == ".mod":
            lang = "go-mod"
        elif rel_path.suffix == ".sum":
            lang = "go-sum"
        else:
            lang = "go"

        # 追加文件标题与代码块
        lines.extend([
            f"**{rel_path.as_posix()}**\n",
            f"```{lang}\n",
            code,
            "\n```\n\n",
        ])

    return "".join(lines)

def main():
    """
    主入口：
    1. 支持命令行参数传入路径；
    2. 无参数时，通过交互提示拖入文件夹；
    3. 收集文件 -> 生成 Markdown -> 写入磁盘。
    """
    import sys

    # 获取命令行参数或交互输入
    if len(sys.argv) < 2:
        folder = input("拖入 Go 项目文件夹路径：").strip().strip('"')
    else:
        folder = sys.argv[1]

    root_path = Path(folder).resolve()
    if not root_path.is_dir():
        print("路径无效，不是文件夹：", root_path)
        return

    # 收集文件
    go_files = collect_go_files(root_path)
    if not go_files:
        print("未找到任何 .go/go.mod/go.sum 文件。")
        return

    # 构建 Markdown 内容
    md_content = build_md_content(go_files, root_path.name)

    # 写入磁盘（当前工作目录）
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    output_file = Path.cwd() / f"{root_path.name}_bundle_{timestamp}.md"
    output_file.write_text(md_content, encoding="utf-8")
    print(f"✅ 合并完成，已生成：{output_file}")

if __name__ == "__main__":
    main()
    input("回车以退出...")