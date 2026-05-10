"""智能体管理命令"""
import typer
from typing import Optional

app = typer.Typer(help="智能体管理命令")


@app.command()
def 列表():
    """列出所有可用的智能体"""
    from ...智能体.基础 import 智能体类别, 智能体成本

    typer.echo("可用智能体:\n")

    # Claude Code
    typer.echo("  claude_code")
    typer.echo("    类别: 超级大脑")
    typer.echo("    成本层级: 昂贵")
    typer.echo("    上下文窗口: 200,000")
    typer.echo("    能力: 架构设计, 代码生成, 代码审查, 文档生成")
    typer.echo()

    # OpenCode
    typer.echo("  opencode")
    typer.echo("    类别: 工具")
    typer.echo("    成本层级: 便宜")
    typer.echo("    上下文窗口: 128,000")
    typer.echo("    能力: 代码生成, 代码审查, 代码库探索")
    typer.echo()

    # Codex
    typer.echo("  codex")
    typer.echo("    类别: 工具")
    typer.echo("    成本层级: 便宜")
    typer.echo("    上下文窗口: 16,000")
    typer.echo("    能力: 代码生成, 测试生成, 代码解释")


@app.command()
def 状态(
    智能体ID: Optional[str] = typer.Argument(None, help="智能体ID（不指定则显示所有）")
):
    """显示智能体状态"""
    from ...智能体 import 健康检查器

    检查器 = 健康检查器()

    if 智能体ID:
        # 显示单个智能体状态
        typer.echo(f"智能体: {智能体ID}")
        统计 = 检查器.获取负载统计(智能体ID)
        if 统计:
            typer.echo(f"  健康率: {统计.健康率:.2%}")
            typer.echo(f"  任务数: {统计.最近任务数}")
            typer.echo(f"  成功数: {统计.最近成功数}")
        else:
            typer.echo("  状态: 无数据")
    else:
        # 显示所有智能体状态
        typer.echo("智能体状态:\n")
        统计列表 = 检查器.获取所有负载统计()
        if not 统计列表:
            typer.echo("  （无智能体数据）")
        else:
            for 统计 in 统计列表:
                typer.echo(f"  {统计.智能体ID}")
                typer.echo(f"    健康率: {统计.健康率:.2%}")
                typer.echo(f"    任务数: {统计.最近任务数}")
                typer.echo()


@app.command()
def 健康检查():
    """执行智能体健康检查"""
    from ...智能体 import 健康检查器

    检查器 = 健康检查器()

    typer.echo("执行健康检查...\n")

    # 检查所有智能体
    智能体列表 = ["claude_code", "opencode", "codex"]

    for 智能体ID in 智能体列表:
        typer.echo(f"  {智能体ID}...")
        统计 = 检查器.获取负载统计(智能体ID)
        if 统计:
            if 统计.健康率 >= 0.8:
                状态 = "✓ 健康"
            elif 统计.健康率 >= 0.5:
                状态 = "⚠ 警告"
            else:
                状态 = "✗ 不健康"
            typer.echo(f"    {状态} (健康率: {统计.健康率:.2%})")
        else:
            typer.echo("    - 无数据")

    typer.echo()


@app.command()
def 加载(
    智能体ID: str = typer.Argument(..., help="智能体ID")
):
    """显示智能体详细负载统计"""
    from ...智能体 import 健康检查器

    检查器 = 健康检查器()
    统计 = 检查器.获取负载统计(智能体ID)

    if not 统计:
        typer.echo(f"未找到智能体: {智能体ID}")
        raise typer.Exit(1)

    typer.echo(f"智能体负载统计: {智能体ID}\n")
    typer.echo(f"  最近任务数: {统计.最近任务数}")
    typer.echo(f"  最近成功数: {统计.最近成功数}")
    typer.echo(f"  最近失败数: {统计.最近失败数}")
    typer.echo(f"  健康率: {统计.健康率:.2%}")
    typer.echo(f"  平均响应时间: {统计.平均响应时间:.2f}秒")
