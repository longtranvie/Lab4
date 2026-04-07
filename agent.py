"""
TravelBuddy Agent — Trợ lý du lịch thông minh sử dụng LangGraph.

Agent tự quyết định gọi tool nào, bao nhiêu lần, và kết hợp kết quả
để đưa ra gợi ý tối ưu cho khách hàng.
"""

import logging
import sys
from pathlib import Path
from typing import Annotated

from typing_extensions import TypedDict
from dotenv import load_dotenv
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

from tools import get_all_tools

load_dotenv()

# ============================================================
# Logging — hiển thị rõ ràng quá trình suy luận của Agent
# ============================================================

LOG_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
DATE_FORMAT = "%H:%M:%S"

logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    datefmt=DATE_FORMAT,
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("travelbuddy")

# Giảm noise từ thư viện ngoài
for noisy in ("httpx", "httpcore", "openai", "langchain", "langsmith"):
    logging.getLogger(noisy).setLevel(logging.WARNING)


# ============================================================
# 1. Đọc System Prompt từ file markdown
# ============================================================

PROMPT_PATH = Path(__file__).parent / "prompts" / "system_prompt.md"
SYSTEM_PROMPT = PROMPT_PATH.read_text(encoding="utf-8")
logger.info("[init] Đã tải system prompt từ: %s", PROMPT_PATH)


# ============================================================
# 2. Khai báo State
# ============================================================

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]


# ============================================================
# 3. Khởi tạo LLM và Tools
# ============================================================

tools_list = get_all_tools()
logger.info("[init] Đã đăng ký %d tools: %s", len(tools_list), [t.name for t in tools_list])

llm = ChatOpenAI(model="gpt-5-nano", temperature=0)
llm_with_tools = llm.bind_tools(tools_list)


# ============================================================
# 4. Agent Node — nơi LLM suy luận
# ============================================================

def agent_node(state: AgentState) -> dict:
    """Gọi LLM để suy luận, chèn system prompt nếu chưa có."""
    messages = state["messages"]

    # Chèn system prompt ở đầu nếu chưa có
    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages

    logger.info("[agent] Đang suy luận... (%d messages trong context)", len(messages))

    response = llm_with_tools.invoke(messages)

    # Log reasoning
    if response.tool_calls:
        tool_names = [tc["name"] for tc in response.tool_calls]
        logger.info("[agent] Quyết định gọi tools: %s", tool_names)
    else:
        preview = response.content[:120] + "..." if len(response.content) > 120 else response.content
        logger.info("[agent] Trả lời: %s", preview)

    return {"messages": [response]}


# ============================================================
# 5. Xây dựng Graph
# ============================================================

tool_node = ToolNode(tools_list)

graph_builder = StateGraph(AgentState)
graph_builder.add_node("agent", agent_node)
graph_builder.add_node("tools", tool_node)

graph_builder.add_edge(START, "agent")
graph_builder.add_conditional_edges("agent", tools_condition)
graph_builder.add_edge("tools", "agent")

graph = graph_builder.compile()
logger.info("[init] LangGraph đã được biên dịch thành công.")


# ============================================================
# 6. Hàm chạy Agent
# ============================================================

def run_agent(user_input: str) -> str:
    """Chạy agent với một câu hỏi từ người dùng."""
    logger.info("=" * 60)
    logger.info("[user] %s", user_input)
    logger.info("=" * 60)

    result = graph.invoke({
        "messages": [HumanMessage(content=user_input)]
    })

    # Lấy tin nhắn cuối cùng (câu trả lời của agent)
    final_message = result["messages"][-1]
    logger.info("=" * 60)
    logger.info("[done] Hoàn thành — tổng %d messages trong conversation", len(result["messages"]))
    logger.info("=" * 60)

    return final_message.content


# ============================================================
# 7. Interactive loop — chạy khi gọi trực tiếp
# ============================================================

def main() -> None:
    """Vòng lặp chat tương tác."""
    print("\n" + "=" * 60)
    print("TravelBuddy -- Trợ lý du lịch thông minh")
    print("Gõ 'quit' hoặc 'exit' để thoát.")
    print("=" * 60 + "\n")

    while True:
        try:
            user_input = input("Bạn: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nTạm biệt!")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "thoát"):
            print("Tạm biệt! Chúc bạn có chuyến đi vui vẻ!")
            break

        response = run_agent(user_input)
        print(f"\nTravelBuddy: {response}\n")


if __name__ == "__main__":
    main()
