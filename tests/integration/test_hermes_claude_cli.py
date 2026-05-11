"""集成测试：Hermes 通过 CLI 调度 Claude Code"""
import shutil
import subprocess
import pytest

_CLAUDE_PATH = shutil.which("claude")

pytestmark = [
    pytest.mark.skipif(not _CLAUDE_PATH, reason="claude CLI 未安装"),
    pytest.mark.integration
]


class TestClaudeCLI:

    def test_claude_cli_disponivel(self):
        resultado = subprocess.run(
            [_CLAUDE_PATH, "--version"],
            capture_output=True, text=True, timeout=10
        )
        assert resultado.returncode == 0

    def test_claude_cli_comando_simples(self, tmp_path):
        prompt = '回复仅包含单词 "OK"'
        resultado = subprocess.run(
            [_CLAUDE_PATH, "-p", prompt],
            capture_output=True, text=True, timeout=60,
            cwd=str(tmp_path)
        )
        assert resultado.returncode == 0

    def test_claude_cli_trabalha_no_diretorio(self, tmp_path):
        (tmp_path / "mensagem.txt").write_text("ola mundo")
        prompt = '读取 mensagem.txt 文件并回复其内容'
        resultado = subprocess.run(
            [_CLAUDE_PATH, "-p", prompt],
            capture_output=True, text=True, timeout=60,
            cwd=str(tmp_path)
        )
        assert resultado.returncode == 0
