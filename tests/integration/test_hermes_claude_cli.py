"""集成测试：Hermes 通过 CLI 调度 Claude Code"""
import subprocess
import pytest


pytestmark = [
    pytest.mark.integration
]


class TestClaudeCLI:

    def test_claude_cli_disponivel(self):
        resultado = subprocess.run(
            ["claude", "--version"],
            capture_output=True, text=True, timeout=10
        )
        assert resultado.returncode == 0

    def test_claude_cli_comando_simples(self, tmp_path):
        prompt = 'responde apenas "OK"'
        resultado = subprocess.run(
            ["claude", "-p", prompt],
            capture_output=True, text=True, timeout=60,
            cwd=str(tmp_path)
        )
        assert resultado.returncode == 0
        assert "OK" in resultado.stdout

    def test_claude_cli_trabalha_no_diretorio(self, tmp_path):
        (tmp_path / "mensagem.txt").write_text("ola mundo")
        prompt = 'leia o arquivo mensagem.txt e responda com seu conteudo'
        resultado = subprocess.run(
            ["claude", "-p", prompt],
            capture_output=True, text=True, timeout=60,
            cwd=str(tmp_path)
        )
        assert resultado.returncode == 0
        assert "ola mundo" in resultado.stdout
