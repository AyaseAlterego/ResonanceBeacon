"""security-review 技能模板"""

security_review模板 = """
你必须遵循 security-review 技能：

## 检查项
1. 密钥扫描 — 检查是否有 AWS Key、API Key、Private Key 等
2. OWASP Top 10 — 检查 SQL 注入、XSS、命令注入等
3. CVE 审计 — 检查依赖包是否有已知漏洞
4. 供应链安全 — 检查依赖来源是否可信

## 输出
- 问题列表（类型、严重级别、位置、建议）
- 通过/不通过结论
- 如果不通过，列出必须修复的问题
"""
