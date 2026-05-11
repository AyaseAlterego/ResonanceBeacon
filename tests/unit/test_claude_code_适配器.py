"""测试 Claude Code 适配器"""
import asyncio
import pytest
from unittest.mock import patch, AsyncMock
from src.hermes.智能体.适配器.claude_code import ClaudeCode适配器
from src.hermes.智能体.基础 import 智能体类别, 智能体成本, 上下文包


@pytest.fixture
def 配置():
    return {"api_key": "test-key", "timeout": 30, "max_tokens": 100}


@pytest.fixture
def 适配器(配置):
    return ClaudeCode适配器(模型="claude-sonnet-4-20250514", 配置=配置)


class Test属性:

    def test_智能体ID(self, 适配器):
        assert 适配器.智能体ID == "claude_code"

    def test_类别(self, 适配器):
        assert 适配器.类别 == 智能体类别.超级大脑

    def test_成本层级(self, 适配器):
        assert 适配器.成本层级 == 智能体成本.昂贵

    def test_能力列表_含新能力(self, 适配器):
        能力名称 = [c.名称 for c in 适配器.能力列表]
        assert "file_operations" in 能力名称
        assert "bash_execution" in 能力名称


class Test初始化:

    @patch("shutil.which", return_value="/usr/local/bin/claude")
    def test_CLI模式(self, mock_which, 适配器):
        import asyncio
        asyncio.run(适配器.初始化({}))
        assert 适配器._CLI可用 is True

    @patch("shutil.which", return_value=None)
    @patch("anthropic.AsyncAnthropic")
    def test_API回退(self, mock_anthropic, mock_which, 适配器):
        import asyncio
        asyncio.run(适配器.初始化({"api_key": "test"}))
        assert 适配器._CLI可用 is False
        assert 适配器._客户端 is not None

    @patch("shutil.which", return_value=None)
    @patch("anthropic.AsyncAnthropic", side_effect=ImportError)
    def test_API初始化失败(self, mock_anthropic, mock_which, 适配器):
        import asyncio
        with pytest.raises(ImportError):
            asyncio.run(适配器.初始化({"api_key": "test"}))


class TestCLI执行:

    @pytest.mark.asyncio
    @patch("shutil.which", return_value="/usr/local/bin/claude")
    async def test_CLI任务成功(self, mock_which, 适配器):
        await 适配器.初始化({"api_key": "test"})
        mock进程 = AsyncMock()
        mock进程.communicate = AsyncMock(return_value=(b"```python\nprint('ok')\n```", b""))
        mock进程.returncode = 0
        with patch.object(asyncio, "create_subprocess_exec", return_value=mock进程):
            结果 = await 适配器.执行任务("t1", "code_generation", {"需求": "hi"}, 上下文包(项目路径="/workspace"))
        assert 结果.状态 == "completed"
        assert "/workspace" in 结果.输出数据["工作目录"]

    @pytest.mark.asyncio
    @patch("shutil.which", return_value="/usr/local/bin/claude")
    async def test_CLI任务失败(self, mock_which, 适配器):
        await 适配器.初始化({"api_key": "test"})
        mock进程 = AsyncMock()
        mock进程.communicate = AsyncMock(return_value=(b"", b"error!"))
        mock进程.returncode = 1
        with patch.object(asyncio, "create_subprocess_exec", return_value=mock进程):
            结果 = await 适配器.执行任务("t1", "code_generation", {}, 上下文包())
        assert 结果.状态 == "failed"

    @pytest.mark.asyncio
    @patch("shutil.which", return_value="/usr/local/bin/claude")
    async def test_CLI取消(self, mock_which, 适配器):
        await 适配器.初始化({"api_key": "test"})
        mock进程 = AsyncMock()
        mock进程.terminate = AsyncMock()
        适配器._进程 = mock进程
        assert await 适配器.取消任务("t1") is True
        mock进程.terminate.assert_called_once()


class Test制品提取:

    def test_代码块(self, 适配器):
        制品 = 适配器._提取制品("```python\nx=1\n```")
        code = [a for a in 制品 if a["类型"] == "code"]
        assert len(code) >= 1
        assert "x=1" in code[0]["内容"]

    def test_语言标识(self, 适配器):
        制品 = 适配器._提取制品("```javascript\nconsole.log()\n```")
        code = [a for a in 制品 if a["类型"] == "code"]
        assert code[0]["语言"] == "javascript"
