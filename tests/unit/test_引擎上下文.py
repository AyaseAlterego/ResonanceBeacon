"""测试引擎上下文传递"""
import pytest
from src.hermes.编排器.引擎 import 流水线引擎


class Test引擎上下文:

    @pytest.mark.asyncio
    async def test_引擎初始化携带项目路径(self):
        引擎 = 流水线引擎(
            智能体注册表=None,
            类别路由器=None,
            后台管理器=None,
            项目路径="/workspace/project"
        )
        assert 引擎.项目路径 == "/workspace/project"

    @pytest.mark.asyncio
    async def test_引擎默认项目路径为空(self):
        引擎 = 流水线引擎(
            智能体注册表=None,
            类别路由器=None,
            后台管理器=None
        )
        assert 引擎.项目路径 == ""
