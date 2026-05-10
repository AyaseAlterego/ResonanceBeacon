"""命令行工具"""
import typer

app = typer.Typer(
    name="hermes",
    help="起源信标 - 智能流水线开发系统",
    no_args_is_help=True
)


@app.command()
def 版本():
    """显示版本信息"""
    from .. import __version__
    typer.echo(f"起源信标 v{__version__}")


# 添加子命令组
try:
    from .命令.项目 import app as 项目命令
    from .命令.流水线 import app as 流水线命令
    from .命令.智能体 import app as 智能体命令
    from .命令.配置 import app as 配置命令
    from .命令.健康 import app as 健康命令

    app.add_typer(项目命令, name="项目", help="项目管理命令")
    app.add_typer(流水线命令, name="流水线", help="流水线管理命令")
    app.add_typer(智能体命令, name="智能体", help="智能体管理命令")
    app.add_typer(配置命令, name="配置", help="配置管理命令")
    app.add_typer(健康命令, name="健康", help="系统健康检查")

except ImportError as e:
    # 如果命令模块导入失败，记录错误但不阻止应用启动
    import logging
    logging.warning(f"无法加载命令模块: {e}")


if __name__ == "__main__":
    app()
