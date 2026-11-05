#!/bin/sh
# 使用已安装的项目虚拟环境，不依赖当前工作目录或手动激活环境。
set -eu

CODE_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$CODE_DIR"

if [ ! -x .venv/bin/python ]; then
    printf '%s\n' '尚未安装运行环境，请先按 code/README.md 的“安装与启动”步骤安装依赖。' >&2
    exit 1
fi

printf '%s\n' '正在启动南大二手。默认访问 http://127.0.0.1:5001，按 Ctrl+C 停止。'
exec .venv/bin/python -m marketplace run "$@"
