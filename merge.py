# -*- coding: utf-8 -*-
"""
【健壮版+行数统计】合并指定文件夹中的所有文件内容到一个文本文件。

核心改进：
1.  采用更可靠的解码策略（优先尝试UTF-8和GBK），避免 chardet 误判导致乱码。
2.  优化了文件过滤逻辑，使其更清晰和高效。
3.  增加了更详细的日志和性能计时。
4.  新增参数化配置，可通过命令行或直接修改脚本来指定目录。
5.  【新增】增加了单个文件行数和总行数的统计功能。
"""

import os
import pathlib
import sys
import time

import chardet

# --- 请在这里配置 ---
TARGET_DIRECTORY_OVERRIDE = ""

OUTPUT_FILENAME_OVERRIDE = ""

# 只处理这些文件扩展名（小写）
INCLUDE_EXTENSIONS = {".ts", ".vue", ".md", ".json", ".html", ".py"}

# 明确排除这些目录（及其所有子目录）
EXCLUDE_DIRS = {"tests", "node_modules", "build", ".git"}

# 如果设置了此项，将只处理这些目录下的文件。如果为空集合，则处理所有非排除目录。
INCLUDE_ONLY_DIRS = {}
# --- 配置结束 ---


def decode_safely(path: pathlib.Path) -> str:
    """
    一个更健壮的文件解码函数。

    策略：
    1. 尝试使用 UTF-8 解码。
    2. 如果失败，尝试使用 GBK 解码（兼容老的中文编码）。
    3. 如果还失败，才使用 chardet 进行猜测。
    4. 如果全部失败，则使用 'latin-1' 并替换错误字符，保证程序不崩溃。
    """
    try:
        raw_bytes = path.read_bytes()
    except IOError as e:
        print(f"      - ❌ 读取文件失败: {e}")
        return f"*** 无法读取文件 {path}: {e} ***\n"

    # 常见编码尝试列表
    encodings_to_try = ["utf-8", "gbk"]

    for enc in encodings_to_try:
        try:
            return raw_bytes.decode(enc)
        except UnicodeDecodeError:
            continue  # 解码失败，尝试下一个

    # 如果常见编码都失败了，再求助于 chardet
    try:
        guess = chardet.detect(raw_bytes)["encoding"]
        if guess:
            print(f"      - ⚠️  UTF-8/GBK解码失败，使用 chardet 猜测的编码: {guess}")
            return raw_bytes.decode(guess, errors="replace")
    except Exception:
        pass  # chardet 也可能失败

    # 最终的保险措施
    print("      - ❌ 所有解码尝试均失败！使用 'latin-1' 作为最后手段。")
    return raw_bytes.decode("latin-1", errors="replace")


def merge_files(folder: pathlib.Path, output_path: pathlib.Path):
    """
    递归遍历文件夹，将所有符合条件的文件内容写入输出文件。
    """
    folder = folder.resolve()
    output_path = output_path.resolve()
    script_path = pathlib.Path(__file__).resolve()

    print(f"开始遍历：{folder}")
    print(f"输出文件：{output_path}")

    files_to_process = []
    print("开始收集文件路径...")
    start_collect_time = time.perf_counter()

    for root, dirs, files in os.walk(folder, topdown=True):
        # 优化：原地修改dirs列表，阻止os.walk进入排除的目录
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

        current_path = pathlib.Path(root)

        # 如果设置了只包含特定目录，则进行检查
        if INCLUDE_ONLY_DIRS:
            # 检查当前路径是否在任何一个指定的包含目录下
            is_path_allowed = any(
                (include_dir in current_path.parts)
                or (current_path.name == include_dir)
                for include_dir in INCLUDE_ONLY_DIRS
            )
            if not is_path_allowed:
                continue  # 如果当前路径不在任何包含目录树下，则跳过此目录下的所有文件

        for f in files:
            file_path = current_path / f

            # 跳过脚本自身和输出文件
            if file_path == script_path or file_path == output_path:
                continue

            # 根据文件扩展名过滤
            if (
                INCLUDE_EXTENSIONS
                and file_path.suffix.lower() not in INCLUDE_EXTENSIONS
            ):
                continue

            files_to_process.append(file_path)

    end_collect_time = time.perf_counter()
    print(
        f"文件路径收集完成，共发现 {len(files_to_process)} 个文件。耗时：{(end_collect_time - start_collect_time):.4f} 秒。"
    )

    files_to_process.sort()

    file_count = 0
    total_line_count = 0  # 初始化总行数计数器

    total_start_time = time.perf_counter()
    with output_path.open("w", encoding="utf-8-sig") as outfile:  # 写入 UTF-8 + BOM
        for path in files_to_process:
            file_count += 1

            # 读取内容
            content = decode_safely(path)

            # --- 统计行数逻辑 ---
            # 使用 splitlines() 可以正确处理 \n, \r, \r\n 等各种换行符
            current_file_lines = len(content.splitlines())
            total_line_count += current_file_lines
            # --------------------

            print(
                f"[{file_count}/{len(files_to_process)}] 正在处理：{path.relative_to(folder)} ({current_file_lines} 行)"
            )

            outfile.write(f"--- 文件路径：{path.relative_to(folder)} ---\n\n")
            outfile.write(content)
            outfile.write("\n\n--- 文件结束 ---\n\n")

    total_end_time = time.perf_counter()

    # 打印最终统计信息
    print("-" * 50)
    print("✅ 合并完成！")
    print("📊 统计概览:")
    print(f"   - 文件总数: {len(files_to_process)} 个")
    print(f"   - 代码总行: {total_line_count} 行")  # 打印总行数
    print(f"   - 耗时总计: {(total_end_time - total_start_time):.2f} 秒")
    print("-" * 50)


if __name__ == "__main__":
    # --- 1. 确定最终的目标目录 (target_folder) ---
    # 优先级: 命令行参数 > 脚本内配置 > 默认值

    target_folder_path_str = None

    # 最高优先级：检查命令行参数
    if len(sys.argv) > 1:
        target_folder_path_str = sys.argv[1]
        print(f"信息：使用命令行参数指定的目标目录 -> {target_folder_path_str}")
    # 第二优先级：检查脚本内配置
    elif TARGET_DIRECTORY_OVERRIDE:
        target_folder_path_str = TARGET_DIRECTORY_OVERRIDE
        print(f"信息：使用脚本内配置的目标目录 -> {target_folder_path_str}")

    # 如果以上都未指定，使用默认值
    if target_folder_path_str:
        target_folder = pathlib.Path(target_folder_path_str).expanduser().resolve()
    else:
        target_folder = pathlib.Path(__file__).parent.resolve()
        print(f"信息：未指定目标目录，使用默认的脚本所在目录 -> {target_folder}")

    # --- 2. 确定最终的输出文件路径 (output_file) ---
    # 输出文件始终保存在脚本所在目录
    script_dir = pathlib.Path(__file__).parent.resolve()

    # 文件名优先级: 脚本内配置 > 自动生成
    output_filename = OUTPUT_FILENAME_OVERRIDE
    if not output_filename:
        # 如果脚本内未配置，则根据目标目录名自动生成
        output_filename = f"merged_{target_folder.name}.txt"

    output_file = script_dir / output_filename

    # --- 3. 校验并执行 ---
    if not target_folder.is_dir():
        print(f"❌ 错误：最终确定的目标不是一个有效的目录：{target_folder}")
        sys.exit(1)

    print("-" * 50)
    print(f"源目录: {target_folder}")
    print(f"输出到: {output_file}")
    print("-" * 50)

    merge_files(target_folder, output_file)
