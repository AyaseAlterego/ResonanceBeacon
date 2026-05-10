"""健康检查命令"""
import typer

app = typer.Typer(help="系统健康检查命令")


@app.command()
def 检查():
    """执行全面的系统健康检查"""
    typer.echo("执行系统健康检查...\n")

    检查结果 = []

    # 检查配置
    typer.echo("1. 检查配置...")
    try:
        from ...配置.配置加载器 import 获取配置
        配置 = 获取配置()
        检查结果.append(("配置", "OK", "配置加载成功"))
        typer.echo("   [OK] 配置加载成功")
    except Exception as e:
        检查结果.append(("配置", "FAIL", str(e)))
        typer.echo(f"   [FAIL] 配置加载失败: {e}")

    # 检查智能体注册表
    typer.echo("2. 检查智能体注册表...")
    try:
        from ...智能体 import 智能体注册表
        注册表 = 智能体注册表()
        检查结果.append(("智能体注册表", "OK", "注册表创建成功"))
        typer.echo("   [OK] 智能体注册表创建成功")
    except Exception as e:
        检查结果.append(("智能体注册表", "FAIL", str(e)))
        typer.echo(f"   [FAIL] 智能体注册表创建失败: {e}")

    # 检查后台管理器
    typer.echo("3. 检查后台管理器...")
    try:
        from ...后台 import 后台任务管理器
        管理器 = 后台任务管理器()
        检查结果.append(("后台管理器", "OK", "管理器创建成功"))
        typer.echo("   [OK] 后台管理器创建成功")
    except Exception as e:
        检查结果.append(("后台管理器", "FAIL", str(e)))
        typer.echo(f"   [FAIL] 后台管理器创建失败: {e}")

    # 检查流水线引擎
    typer.echo("4. 检查流水线引擎...")
    try:
        from ...编排器.引擎 import 流水线引擎
        from ...智能体 import 智能体注册表, 类别路由器
        from ...后台 import 后台任务管理器

        注册表 = 智能体注册表()
        路由器 = 类别路由器()
        路由器.设置注册表(注册表)
        后台管理器 = 后台任务管理器()

        引擎 = 流水线引擎(
            智能体注册表=注册表,
            类别路由器=路由器,
            后台管理器=后台管理器
        )
        检查结果.append(("流水线引擎", "OK", "引擎创建成功"))
        typer.echo("   [OK] 流水线引擎创建成功")
    except Exception as e:
        检查结果.append(("流水线引擎", "FAIL", str(e)))
        typer.echo(f"   [FAIL] 流水线引擎创建失败: {e}")

    # 检查健康检查器
    typer.echo("5. 检查健康检查器...")
    try:
        from ...智能体 import 健康检查器
        检查器 = 健康检查器()
        检查结果.append(("健康检查器", "OK", "检查器创建成功"))
        typer.echo("   [OK] 健康检查器创建成功")
    except Exception as e:
        检查结果.append(("健康检查器", "FAIL", str(e)))
        typer.echo(f"   [FAIL] 健康检查器创建失败: {e}")

    # 检查制品存储
    typer.echo("6. 检查制品存储...")
    try:
        from ...制品.存储 import 本地制品存储
        存储 = 本地制品存储()
        检查结果.append(("制品存储", "OK", "存储创建成功"))
        typer.echo("   [OK] 制品存储创建成功")
    except Exception as e:
        检查结果.append(("制品存储", "FAIL", str(e)))
        typer.echo(f"   [FAIL] 制品存储创建失败: {e}")

    # 检查监控指标
    typer.echo("7. 检查监控指标...")
    try:
        from ...监控.指标 import 监控指标收集器
        收集器 = 监控指标收集器()
        收集器.创建默认指标()
        检查结果.append(("监控指标", "OK", "指标创建成功"))
        typer.echo("   [OK] 监控指标创建成功")
    except Exception as e:
        检查结果.append(("监控指标", "FAIL", str(e)))
        typer.echo(f"   [FAIL] 监控指标创建失败: {e}")

    # 显示总结
    typer.echo()
    成功数 = sum(1 for _, 状态, _ in 检查结果 if 状态 == "OK")
    失败数 = sum(1 for _, 状态, _ in 检查结果 if 状态 == "FAIL")

    if 失败数 == 0:
        typer.echo(f"[PASS] 健康检查通过 ({成功数}/{成功数+失败数})")
    else:
        typer.echo(f"[FAIL] 健康检查失败 ({成功数}/{成功数+失败数})")
        typer.echo("\n失败详情:")
        for 组件, 状态, 描述 in 检查结果:
            if 状态 == "FAIL":
                typer.echo(f"  - {组件}: {描述}")


@app.command()
def 版本():
    """显示版本和环境信息"""
    import sys
    import platform

    typer.echo("系统信息:\n")
    typer.echo(f"  Python: {sys.version}")
    typer.echo(f"  平台: {platform.platform()}")
    typer.echo(f"  处理器: {platform.processor()}")

    try:
        from ... import __version__
        typer.echo(f"\n起源信标版本: v{__version__}")
    except ImportError:
        typer.echo("\n起源信标版本: 未知")
