"""方法论层 - 技能模板库

包含 Superpowers 和 Oh My Hermes 的技能定义，
作为 prompt 注入源，不修改智能体代码。
"""

from .superpowers import (
    brainstorming模板,
    writing_plans模板,
    test_driven_dev模板,
    systematic_debug模板,
    verification模板,
)
from .oh_my_hermes import (
    clarify_requirements模板,
    product_brief模板,
    implement模板,
    security_review模板,
    kanban_task模板,
)

__all__ = [
    "brainstorming模板",
    "writing_plans模板",
    "test_driven_dev模板",
    "systematic_debug模板",
    "verification模板",
    "clarify_requirements模板",
    "product_brief模板",
    "implement模板",
    "security_review模板",
    "kanban_task模板",
]
