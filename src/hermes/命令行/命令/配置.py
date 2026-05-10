"""配置管理命令"""
import typer
from typing import Optional

app = typer.Typer(help="配置管理命令")


@app.command()
def 显示():
    """显示当前合并后的配置"""
    from ...配置.配置加载器 import 获取配置

    配置 = 获取配置()

    typer.echo("当前配置:\n")
    typer.echo(f"  项目名称: {配置.项目名称}")
    typer.echo(f"  版本: {配置.版本}")
    typer.echo(f"  环境: {配置.环境}")
    typer.echo(f"  数据库URL: {配置.数据库URL}")
    typer.echo(f"  RedisURL: {配置.RedisURL}")
    typer.echo()

    # 智能体配置
    typer.echo("智能体配置:")
    try:
        智能体配置字典 = 配置.智能体.model_dump() if hasattr(配置.智能体, 'model_dump') else {}
        typer.echo(f"    Claude Code模型: {智能体配置字典.get('claude_code', {}).get('模型', '未设置')}")
        typer.echo(f"    OpenCode模型: {智能体配置字典.get('opencode', {}).get('模型', '未设置')}")
        typer.echo(f"    Codex模型: {智能体配置字典.get('codex', {}).get('模型', '未设置')}")
    except Exception as e:
        typer.echo(f"    智能体配置: {e}")
    typer.echo()


@app.command()
def 设置(
    路径: str = typer.Argument(..., help="配置路径（例如：项目名称 或 智能体.claude_code.模型）"),
    值: str = typer.Argument(..., help="配置值")
):
    """设置配置值"""
    from pathlib import Path
    import json

    # 加载当前配置
    配置文件 = Path.cwd() / ".hermes" / "配置.json"
    if not 配置文件.exists():
        typer.echo("错误: 未找到项目配置文件", err=True)
        typer.echo("请先运行 'hermes 项目 创建' 创建项目")
        raise typer.Exit(1)

    try:
        with open(配置文件, "r", encoding="utf-8") as f:
            配置 = json.load(f)
    except Exception as e:
        typer.echo(f"错误: 读取配置失败: {e}", err=True)
        raise typer.Exit(1)

    # 解析路径
    部分 = 路径.split(".")
    当前配置 = 配置

    # 导航到目标位置
    for i in range(len(部分) - 1):
        部分名 = 部分[i]
        if 部分名 not in 当前配置:
            当前配置[部分名] = {}
        当前配置 = 当前配置[部分名]

    # 设置值
    最终键 = 部分[-1]

    # 尝试解析值类型
    if 值.lower() in ("true", "false"):
        值 = 值.lower() == "true"
    elif 值.isdigit():
        值 = int(值)
    else:
        try:
            值 = float(值)
        except ValueError:
            pass  # 保持为字符串

    当前配置[最终键] = 值

    # 保存配置
    try:
        with open(配置文件, "w", encoding="utf-8") as f:
            json.dump(配置, f, ensure_ascii=False, indent=2)
        typer.echo(f"✓ 已设置 {路径} = {值}")
    except Exception as e:
        typer.echo(f"错误: 保存配置失败: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def 获取(
    路径: str = typer.Argument(..., help="配置路径（例如：项目名称 或 智能体.claude_code.模型）")
):
    """获取配置值"""
    from pathlib import Path
    import json

    # 加载配置
    配置文件 = Path.cwd() / ".hermes" / "配置.json"
    if not 配置文件.exists():
        typer.echo("错误: 未找到项目配置文件", err=True)
        raise typer.Exit(1)

    try:
        with open(配置文件, "r", encoding="utf-8") as f:
            配置 = json.load(f)
    except Exception as e:
        typer.echo(f"错误: 读取配置失败: {e}", err=True)
        raise typer.Exit(1)

    # 解析路径
    部分 = 路径.split(".")
    当前配置 = 配置

    try:
        for 部分名 in 部分:
            if isinstance(当前配置, dict) and 部分名 in 当前配置:
                当前配置 = 当前配置[部分名]
            else:
                typer.echo(f"错误: 配置路径不存在: {路径}", err=True)
                raise typer.Exit(1)

        typer.echo(f"{路径} = {当前配置}")

    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"错误: 获取配置失败: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def 验证():
    """验证当前配置"""
    from pathlib import Path
    import json

    # 加载配置
    配置文件 = Path.cwd() / ".hermes" / "配置.json"
    if not 配置文件.exists():
        typer.echo("错误: 未找到项目配置文件", err=True)
        raise typer.Exit(1)

    try:
        with open(配置文件, "r", encoding="utf-8") as f:
            配置 = json.load(f)
    except Exception as e:
        typer.echo(f"错误: 读取配置失败: {e}", err=True)
        raise typer.Exit(1)

    typer.echo("验证配置...\n")

    错误列表 = []

    # 检查必填字段
    if "项目名称" not in 配置:
        错误列表.append("缺少必填字段: 项目名称")
    if "版本" not in 配置:
        错误列表.append("缺少必填字段: 版本")
    if "环境" not in 配置:
        错误列表.append("缺少必填字段: 环境")

    # 检查环境值
    环境 = 配置.get("环境", "")
    if 环境 not in ("development", "staging", "production"):
        错误列表.append(f"无效的环境值: {环境}（应为 development, staging, production）")

    # 显示结果
    if 错误列表:
        typer.echo("验证失败:\n")
        for 错误 in 错误列表:
            typer.echo(f"  ✗ {错误}")
        raise typer.Exit(1)
    else:
        typer.echo("✓ 配置验证通过")
