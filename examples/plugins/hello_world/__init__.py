"""你好世界插件"""
from src.hermes.插件.系统 import 插件接口, 插件元数据, 插件类型


class 插件类(插件接口):
    @property
    def 元数据(self) -> 插件元数据:
        return 插件元数据(
            ID="hello_world",
            名称="你好世界",
            版本="1.0.0",
            类型=插件类型.智能体,
            描述="一个简单的示例插件，用于演示插件市场的安装和使用流程",
            作者="起源信标团队",
        )

    async def 初始化(self, 配置: dict) -> None:
        self.问候语 = 配置.get("问候语", "你好，世界！")

    async def 卸载(self) -> None:
        self.问候语 = None

    def 获取问候(self) -> str:
        return self.问候语
