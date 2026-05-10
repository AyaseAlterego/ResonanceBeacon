"""项目管理命令"""
import typer
from pathlib import Path
from typing import Optional

app = typer.Typer(help="项目管理命令")


@app.command()
def 创建(
    名称: str = typer.Argument(..., help="项目名称"),
    路径: Optional[str] = typer.Option(None, "--path", "-p", help="项目路径（默认为当前目录/<名称>）"),
    描述: Optional[str] = typer.Option(None, "--description", "-d", help="项目描述"),
    仓库: Optional[str] = typer.Option(None, "--repo", "-r", help="Git仓库URL")
):
    """创建新项目"""
    # 确定项目路径
    if 路径:
        项目路径 = Path(路径)
    else:
        项目路径 = Path.cwd() / 名称

    # 检查路径是否已存在
    if 项目路径.exists():
        typer.echo(f"错误: 路径已存在: {项目路径}", err=True)
        raise typer.Exit(1)

    try:
        # 创建项目目录
        项目路径.mkdir(parents=True, exist_ok=True)

        # 创建项目配置目录
        配置目录 = 项目路径 / ".hermes"
        配置目录.mkdir(exist_ok=True)

        # 创建项目配置文件
        配置内容 = {
            "项目名称": 名称,
            "描述": 描述 or "",
            "版本": "0.1.0",
            "环境": "development"
        }

        if 仓库:
            配置内容["仓库URL"] = 仓库

        import json
        配置文件 = 配置目录 / "配置.json"
        with open(配置文件, "w", encoding="utf-8") as f:
            json.dump(配置内容, f, ensure_ascii=False, indent=2)

        # 创建必要的目录结构
        (项目路径 / "源代码").mkdir(exist_ok=True)
        (项目路径 / "测试").mkdir(exist_ok=True)
        (项目路径 / "制品").mkdir(exist_ok=True)

        typer.echo(f"[OK] 项目 '{名称}' 已创建")
        typer.echo(f"  路径: {项目路径}")
        typer.echo(f"  配置: {配置文件}")

    except Exception as e:
        typer.echo(f"错误: 创建项目失败: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def 列表():
    """列出当前目录下的所有项目"""
    import json

    当前目录 = Path.cwd()
    项目列表 = []

    # 搜索包含.hermes目录的子目录
    for 子目录 in 当前目录.iterdir():
        if 子目录.is_dir():
            配置文件 = 子目录 / ".hermes" / "配置.json"
            if 配置文件.exists():
                try:
                    with open(配置文件, "r", encoding="utf-8") as f:
                        配置 = json.load(f)
                    项目列表.append({
                        "名称": 配置.get("项目名称", 子目录.name),
                        "路径": 子目录,
                        "描述": 配置.get("描述", ""),
                        "版本": 配置.get("版本", "")
                    })
                except Exception:
                    continue

    if not 项目列表:
        typer.echo("当前目录下没有找到项目")
        return

    typer.echo("找到以下项目:\n")
    for 项目 in 项目列表:
        typer.echo(f"  {项目['名称']}")
        typer.echo(f"    路径: {项目['路径']}")
        if 项目['描述']:
            typer.echo(f"    描述: {项目['描述']}")
        if 项目['版本']:
            typer.echo(f"    版本: {项目['版本']}")
        typer.echo()


@app.command()
def 详情(
    路径: str = typer.Argument(".", help="项目路径")
):
    """显示项目详情"""
    import json

    项目路径 = Path(路径)
    配置文件 = 项目路径 / ".hermes" / "配置.json"

    if not 配置文件.exists():
        typer.echo(f"错误: 未找到项目配置: {配置文件}", err=True)
        raise typer.Exit(1)

    try:
        with open(配置文件, "r", encoding="utf-8") as f:
            配置 = json.load(f)

        typer.echo(f"项目: {配置.get('项目名称', '未知')}")
        typer.echo(f"描述: {配置.get('描述', '无')}")
        typer.echo(f"版本: {配置.get('版本', '未知')}")
        typer.echo(f"环境: {配置.get('环境', '未知')}")
        if "仓库URL" in 配置:
            typer.echo(f"仓库: {配置['仓库URL']}")

    except Exception as e:
        typer.echo(f"错误: 读取配置失败: {e}", err=True)
        raise typer.Exit(1)
