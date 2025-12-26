# server.py
from mcp.server.fastmcp import FastMCP
import sys
import logging
import os
import math
import random

logger = logging.getLogger('my_mcp_tool')

# Fix UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stderr.reconfigure(encoding='utf-8')
    sys.stdout.reconfigure(encoding='utf-8')
    
# Create an MCP server
mcp = FastMCP("my_mcp_tool")    

# ====== 计算器 start ======

# Add a calculator tool
@mcp.tool()
def calculator(python_expression: str) -> dict:
    logger.info("调用了calculator工具")
    """计算Python表达式的结果。可以使用math和random模块中的函数。"""
    try:
        result = eval(python_expression)
        logger.info(f"计算公式: {python_expression}, 结果: {result}")
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"计算出错: {str(e)}")
        return {"success": False, "error": str(e)}        

# ====== 计算器 end ======




# ====== 获取实时资讯 start ======

coze_api_token = os.getenv("COZE_API_TOKEN", "")
if not coze_api_token:
    raise RuntimeError("COZE_API_TOKEN is not set")
from cozepy import Coze, TokenAuth, Message, ChatStatus, MessageContentType, ChatEventType  # noqa
from cozepy import COZE_CN_BASE_URL,Stream, WorkflowEvent, WorkflowEventType  # noqa
coze = Coze(auth=TokenAuth(token=coze_api_token), base_url=COZE_CN_BASE_URL)
workflow_id = os.getenv("COZE_WORKFLOW_ID", "7582874791208697875")
user_id = "666" # 用户id 随便填，没影响

# 直接工作流查询
def handle_workflow_iterator(stream: Stream[WorkflowEvent]):
    for event in stream:
        if event.event == WorkflowEventType.MESSAGE:
            res_messages = ''
            # 把event.message.content从字符串转为json对象
            event.message.content = eval(event.message.content)

            # 遍历res_messages里的output数组
            for output in event.message.content['output']:
                a = f"{output['title']}：{output['summary']}\n"
                res_messages += a

            return res_messages
        elif event.event == WorkflowEventType.ERROR:
            logger.error(f"获取实时咨询时出错: {str(event.error)}")
            return str(event.error)
        elif event.event == WorkflowEventType.INTERRUPT:
            handle_workflow_iterator(
                coze.workflows.runs.resume(
                    workflow_id=workflow_id,
                    event_id=event.interrupt.interrupt_data.event_id,
                    resume_data="hey",
                    interrupt_type=event.interrupt.interrupt_data.type,
                )
            )

@mcp.tool()
def web_search(input_query: str) -> dict:
    logger.info("调用了web_search工具")
    """获取实时资讯。当你需要获取实时的信息，比如汇率、时事、新闻、比赛信息等等，这个工具非常有用。input_query为搜索关键词。"""
    try:
        logger.info(f"搜索信息: {input_query}")
        res_messages = handle_workflow_iterator(
            coze.workflows.runs.stream(
                workflow_id=workflow_id,
                parameters={
                    "input": input_query
                }
            )
        )
        # logger.info(f"搜索结果: {res_messages}")
        return {"success": True, "result": res_messages}

    except Exception as e:
        logger.error(f"获取实时咨询时出错: {str(e)}")
        return {"success": False, "error": str(e)}


# ====== 获取网络实时咨询 end ======

# 写入到后台角色介绍当中，可以更好的调用查询工具
# 所有用户查询实时信息的请求，包括但不限于汇率、时事、新闻、比赛信息等等，你必须调用工具get_web_news来查询。你拥有get_web_news查询工具，不要自行捏造信息，当用户让你查询实时信息时，你提取用户的查询关键词，然后工具(get_web_news)即可。并提醒用户请稍等！

# ====== 测试自定义工具 start ======
# 增加一个自己自定义的工具 获取我们的秘密
# @mcp.tool()
# def getOurSecret() -> dict:
#     """这个工具可以获取到我们之间的秘密，当用户说起关于我们之间的秘密的时候，请使用这个工具，返回我们的秘密"""
#     result = "这是我们之间的秘密：我们在10年前买了一张彩票中了100万元，现在还存在银行，银行卡的密码是0123456789。这件事情只有我们两个知道。"
#     return {"success": True, "result": result}
# ====== 测试自定义工具 end ======

# Start the server
if __name__ == "__main__":
    mcp.run(transport="stdio")