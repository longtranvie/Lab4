"""
Chạy 5 test cases theo yêu cầu Lab 4 và ghi kết quả ra test_results.md.
"""

import sys
import io
import logging
from datetime import datetime

from agent import run_agent

logger = logging.getLogger("test_runner")

# 5 kịch bản test theo đề bài
TEST_CASES: list[dict[str, str]] = [
    {
        "id": "1",
        "name": "Direct Answer (Không cần tool)",
        "input": "Xin chào! Tôi đang muốn đi du lịch nhưng chưa biết đi đâu.",
        "expect": "Agent chào hỏi, hỏi thêm về sở thích/ngân sách/thời gian. Không gọi tool nào.",
    },
    {
        "id": "2",
        "name": "Single Tool Call",
        "input": "Tìm giúp tôi chuyến bay từ Hà Nội đi Đà Nẵng",
        "expect": "Gọi search_flights('Hà Nội', 'Đà Nẵng'), liệt kê 4 chuyến bay.",
    },
    {
        "id": "3",
        "name": "Multi-Step Tool Chaining",
        "input": "Tôi ở Hà Nội, muốn đi Phú Quốc 2 đêm, budget 5 triệu. Tư vấn giúp!",
        "expect": "Chuỗi: search_flights → tìm vé rẻ nhất → calculate_budget → search_hotels với max_price → tổng hợp gợi ý.",
    },
    {
        "id": "4",
        "name": "Missing Info / Clarification",
        "input": "Tôi muốn đặt khách sạn",
        "expect": "Agent hỏi lại: thành phố nào? bao nhiêu đêm? ngân sách bao nhiêu? Không gọi tool vội.",
    },
    {
        "id": "5",
        "name": "Guardrail / Refusal",
        "input": "Giải giúp tôi bài tập lập trình Python về linked list",
        "expect": "Từ chối lịch sự, nói rằng chỉ hỗ trợ về du lịch.",
    },
]


def run_all_tests() -> str:
    """Chạy tất cả test cases và trả về nội dung markdown."""
    lines: list[str] = [
        "# Test Results — TravelBuddy Agent",
        f"\nNgày chạy: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
    ]

    for tc in TEST_CASES:
        print(f"\n{'='*60}")
        print(f">> TEST {tc['id']}: {tc['name']}")
        print(f"  Input: {tc['input']}")
        print(f"{'='*60}")

        # Capture log output
        log_capture = io.StringIO()
        handler = logging.StreamHandler(log_capture)
        handler.setLevel(logging.INFO)
        handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)-7s | %(name)s | %(message)s", "%H:%M:%S"))
        root_logger = logging.getLogger()
        root_logger.addHandler(handler)

        try:
            response = run_agent(tc["input"])
        except Exception as e:
            response = f"ERROR: {e}"
            logger.error("Test %s thất bại: %s", tc["id"], e)
        finally:
            root_logger.removeHandler(handler)

        captured_logs = log_capture.getvalue()

        print(f"\nResponse:\n{response}\n")

        # Ghi vào markdown
        lines.append(f"## Test {tc['id']} — {tc['name']}")
        lines.append(f"\n**Input:** `{tc['input']}`\n")
        lines.append(f"**Kỳ vọng:** {tc['expect']}\n")
        lines.append("**Console Log:**")
        lines.append(f"```\n{captured_logs}```\n")
        lines.append(f"**Response:**\n```\n{response}\n```\n")
        lines.append("---\n")

    return "\n".join(lines)


if __name__ == "__main__":
    output = run_all_tests()

    with open("test_results.md", "w", encoding="utf-8") as f:
        f.write(output)

    print("\nKết quả đã được ghi vào test_results.md")
