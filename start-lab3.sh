#!/bin/sh
# 在仓库根目录一条命令启动实验三，也支持从其他工作目录调用。
set -eu

PROJECT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec "$PROJECT_DIR/lab3/code/start.sh" "$@"
