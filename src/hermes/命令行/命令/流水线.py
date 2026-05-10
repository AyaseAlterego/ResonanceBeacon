"""流水线管理命令"""
import typer
from pathlib import Path
from typing import Optional
import asyncio
import json

app = typer.Typer(help="流水线管理命令")


@app.command()
def 运行(
    定义文件: str = typer.Argument(..., help="流水线定义文件路径"),
    用户输入: str = typer.Option(..., "--input", "-i", help="用户输入"),
    项目路径: str = typer.Option(".", "--project", "-p", help="项目路径"),
    阶段数: Optional[int] = typer.Option(None, "--stages", help="限制执行的阶段数")
):
    """运行流水线"""
    # 加载流水线定义
    定义路径 = Path(定义文件)
    if not 定义路径.exists():
        typer.echo(f"错误: 定义文件不存在: {定义文件}", err=True)
        raise typer.Exit(1)

    try:
        with open(定义路径, "r", encoding="utf-8") as f:
            流水线定义 = json.load(f)
    except json.JSONDecodeError as e:
        typer.echo(f"错误: 无效的JSON格式: {e}", err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"错误: 加载定义文件失败: {e}", err=True)
        raise typer.Exit(1)

    # 验证流水线定义
    if "id" not in 流水线定义:
        流水线定义["id"] = 流水线定义.get("name", "unknown")
    if "stages" not in 流水线定义:
        typer.echo("错误: 流水线定义缺少'stages'字段", err=True)
        raise typer.Exit(1)

    # 如果指定了阶段数限制
    if 阶段数 and 阶段数 > 0:
        流水线定义["stages"] = 流水线定义["stages"][:阶段数]

    流水线名称 = 流水线定义.get("name", "未命名")
    阶段数统计 = len(流水线定义["stages"])

    typer.echo(f"加载流水线: {流水线名称}")
    typer.echo(f"  阶段数: {阶段数统计}")
    typer.echo(f"  用户输入: {用户输入[:50]}...")
    typer.echo()

    try:
        # 初始化组件
        from ...智能体 import 智能体注册表, 类别路由器
        from ...智能体.基础 import 智能体类别
        from ...后台 import 后台任务管理器
        from ...编排器.引擎 import 流水线引擎
        from ...编排器.调度器 import DAG调度器

        # 创建智能体注册表
        注册表 = 智能体注册表()

        # 创建类别路由器
        路由器 = 类别路由器()
        路由器.设置注册表(注册表)

        # 注册所有智能体类别（暂时为空）
        for 类别 in 智能体类别:
            路由器.注册类别路由(类别, [])

        # 创建后台管理器
        后台管理器 = 后台任务管理器()

        # 创建流水线引擎
        引擎 = 流水线引擎(
            智能体注册表=注册表,
            类别路由器=路由器,
            后台管理器=后台管理器
        )

        # 运行流水线
        typer.echo("开始执行流水线...")
        结果 = asyncio.run(引擎.运行流水线(流水线定义, 用户输入))

        # 显示结果
        typer.echo()
        if 结果.状态 == "completed":
            typer.echo(f"[OK] 流水线执行成功")
        else:
            typer.echo(f"[FAIL] 流水线执行失败")

        typer.echo(f"  流水线ID: {结果.流水线ID}")
        typer.echo(f"  状态: {结果.状态}")
        typer.echo(f"  阶段: {结果.完成阶段数}/{结果.阶段数}")

        if 结果.错误:
            typer.echo(f"  错误: {结果.错误}")

    except Exception as e:
        typer.echo(f"[ERROR] 流水线执行失败: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def 状态(
    流水线ID: str = typer.Argument(..., help="流水线ID")
):
    """查看流水线状态"""
    # 这里应该从数据库或内存中获取流水线状态
    # 目前显示存根信息
    typer.echo(f"流水线ID: {流水线ID}")
    typer.echo("状态: 未找到（数据库集成待实现）")
    typer.echo()
    typer.echo("注意: 完整的流水线状态查询需要数据库集成")


@app.command()
def 列表():
    """列出所有流水线"""
    # 这里应该从数据库中查询流水线列表
    typer.echo("流水线列表:")
    typer.echo("  （数据库集成待实现）")
    typer.echo()
    typer.echo("注意: 完整的流水线列表需要数据库集成")


@app.command()
def 取消(
    流水线ID: str = typer.Argument(..., help="流水线ID"),
    确认: bool = typer.Option(False, "--yes", "-y", help="跳过确认提示")
):
    """取消运行中的流水线"""
    if not 确认:
        确认执行 = typer.confirm(f"确认取消流水线 {流水线ID}?")
        if not 确认执行:
            typer.echo("已取消")
            return

    # 这里应该调用取消逻辑
    typer.echo(f"取消流水线: {流水线ID}")
    typer.echo("注意: 完整的取消功能需要后台管理器集成")
