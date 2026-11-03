"""只打包交付材料，排除运行数据、密钥、虚拟环境和缓存。"""

import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NAME = "实验3_241220131_单锦曼"
EXCLUDED = {".venv", "instance", "__pycache__", ".pytest_cache", ".ruff_cache", ".git"}


def main():
    destination = ROOT / f"{NAME}.zip"
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.write(ROOT / "实验报告.pdf", f"{NAME}/实验报告.pdf")
        for directory in ("UML", "code"):
            for source in sorted((ROOT / directory).rglob("*")):
                if not source.is_file():
                    continue
                relative = source.relative_to(ROOT)
                if any(part in EXCLUDED for part in relative.parts):
                    continue
                if source.suffix in {".pyc", ".pem", ".key", ".sqlite3"}:
                    continue
                if source.name.startswith(".env"):
                    continue
                archive.write(source, str(Path(NAME) / relative))
    with zipfile.ZipFile(destination) as archive:
        assert archive.testzip() is None
        assert all(name.startswith(NAME + "/") for name in archive.namelist())
        assert not any(set(Path(name).parts) & EXCLUDED for name in archive.namelist())
        print(f"已生成 {destination.name}：{len(archive.namelist())} 个文件。")


if __name__ == "__main__":
    main()
