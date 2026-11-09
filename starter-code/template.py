"""
Lab #4: System Prompt Engineering & Tool Calling Engine
Học viên hoàn thiện các mục TODO để hoàn thành bài lab.

Kiến trúc:
  - ChatbotBaseline: LLM thuần, không dùng tool → quan sát hallucination.
  - ToolCallingAgent: Agent dùng System Prompt + 2 Tool Schemas.
"""

import json
import re
from typing import Dict, Any, List
from tools import TOOL_DEFINITIONS, TOOL_MAP, search_product_catalog, submit_support_ticket

# ═══════════════════════════════════════════════════════════════════════════
# TODO 1: Thiết kế SYSTEM PROMPT cấp sản xuất
# Yêu cầu: Phải chứa Persona, Core Rules, Operational Boundaries, Output Contract.
# ═══════════════════════════════════════════════════════════════════════════

SYSTEM_PROMPT = """
# PERSONA
You are VinAssistant, an AI customer support assistant for Vingroup.
Your role is to provide accurate information about Vingroup products
and services, assist customers with product searches and support requests.

Communication style:
- Professional, concise, and helpful.
- Respond in the user's language.
- Never fabricate information.

# AVAILABLE TOOLS
You have access to the following tools:

1. search_product_catalog:
   Search the product catalog for products matching user requirements.
   Use this tool when users ask about products, prices, or availability.

2. submit_support_ticket:
   Submit a customer support request.
   Use this tool when users report problems or request support.

# CORE RULES
1. Never invent product names, prices, specifications, or availability.
2. Always use search_product_catalog for product-related queries.
3. Always use submit_support_ticket when a customer requests support.
4. Only provide information returned by tools or explicitly known facts.
5. If tool results are empty, clearly inform the user.
6. Never claim a tool action succeeded unless the tool confirms it.
7. Do not call unnecessary tools.

# OPERATIONAL BOUNDARIES
1. Only answer questions related to Vingroup and its ecosystem.
2. Do not provide unrelated information.
3. Do not fabricate internal company information.
4. If a request is outside your scope, politely explain the limitation.

# OUTPUT CONTRACT
Follow the ReAct structure internally:

Thought: Identify user intent and determine whether tools are needed.
Action: Select and call the appropriate tool.
Observation: Analyze the tool result.
Final Answer: Provide a concise response based on verified information.

Never expose internal reasoning or private thoughts.
Only return the final answer to the user.
"""


# ═══════════════════════════════════════════════════════════════════════════
# CLASS: ChatbotBaseline
# ═══════════════════════════════════════════════════════════════════════════

class ChatbotBaseline:
	"""Baseline LLM Chatbot — Không sử dụng Tool Calling hay ReAct Loop."""

	def query(self, user_input: str) -> Dict[str, Any]:
		# TODO 2: Trả về câu trả lời tĩnh (mock) hoặc gọi Gemini API 1 lượt (không dùng tool)
		# Mục tiêu: Quan sát hiện tượng bịa thông tin (hallucination)
		return {
			"answer": f"[Chatbot Baseline] Trả lời cho: {user_input}",
			"tool_calls": [],
			"status": "success",
			"mode": "mock_baseline"
		}


# ═══════════════════════════════════════════════════════════════════════════
# CLASS: ToolCallingAgent
# ═══════════════════════════════════════════════════════════════════════════

class ToolCallingAgent:
    """Agent với System Prompt Engineering & Tool Calling."""

    def __init__(self, max_iterations: int = 5):
        self.max_iterations = max_iterations
        self.trace: List[Dict[str, Any]] = []

    def run(self, user_input: str) -> Dict[str, Any]:
        self.trace = []
        query = user_input.lower()

        # TODO 3: Analyze user intent

        # Chỉ tìm catalog khi người dùng có ý định tìm/mua sản phẩm
        has_vehicle = bool(re.search(
            r"xe điện|vinfast|ô tô|oto",
            query
        ))

        has_search_intent = bool(re.search(
            r"muốn xem|tìm|có .* nào|giá|dưới|trên|mua|danh sách",
            query
        ))

        needs_catalog = has_vehicle and has_search_intent

        # Phát hiện yêu cầu hỗ trợ
        needs_ticket = bool(re.search(
            r"bị lỗi|lỗi|hỏng|không hoạt động|khiếu nại|"
            r"cần hỗ trợ|cần xử lý|sự cố",
            query
        ))

        self.trace.append({
            "step": "intent_analysis",
            "needs_catalog": needs_catalog,
            "needs_ticket": needs_ticket
        })

        # Prepare tool calls
        tool_calls = []

        if needs_catalog:
            tool_calls.append("search_product_catalog")

        if needs_ticket:
            tool_calls.append("submit_support_ticket")

        # Extract maximum price
        max_price = 999999999999

        price_match = re.search(
            r"(\d+(?:[.,]\d+)?)\s*(triệu|tỷ)",
            query
        )

        if price_match:
            amount = float(price_match.group(1).replace(",", "."))

            if price_match.group(2) == "triệu":
                max_price = int(amount * 1_000_000)
            else:
                max_price = int(amount * 1_000_000_000)

        # Extract customer name
        name_match = re.search(
            r"tôi tên\s+([^,.]+)",
            user_input,
            re.IGNORECASE
        )

        customer_name = (
            name_match.group(1).strip()
            if name_match
            else "Khách hàng"
        )

        # Determine ticket priority
        priority = "medium"

        if re.search(r"nghiêm trọng|gấp|khẩn cấp", query):
            priority = "high"

        # TODO 4: Agent Loop
        iteration = 0
        observations = []
        if not tool_calls:
            iteration = 1

        while tool_calls and iteration < self.max_iterations:
            iteration += 1
            tool_name = tool_calls.pop(0)

            self.trace.append({
                "step": "action",
                "iteration": iteration,
                "tool": tool_name
            })

            try:
                if tool_name == "search_product_catalog":
                    result = TOOL_MAP[tool_name](
                        category="xe_dien",
                        max_price=max_price
                    )

                elif tool_name == "submit_support_ticket":
                    result = TOOL_MAP[tool_name](
                        customer_name=customer_name,
                        issue_description=user_input,
                        priority=priority
                    )

                observations.append({
                    "tool": tool_name,
                    "result": result
                })

                self.trace.append({
                    "step": "observation",
                    "iteration": iteration,
                    "tool": tool_name,
                    "result": result
                })

            except Exception as e:
                observations.append({
                    "tool": tool_name,
                    "error": str(e)
                })

                self.trace.append({
                    "step": "error",
                    "iteration": iteration,
                    "tool": tool_name,
                    "error": str(e)
                })

        # TODO 5: Generate final answer
        answers = []
        if not observations:
            if "bảo hành pin" in query:
                answer = (
                    "Chính sách bảo hành pin xe điện VinFast "
                    "phụ thuộc vào dòng xe và điều kiện áp dụng. "
                    "Vui lòng kiểm tra chính sách chính thức của VinFast."
                )
            else:
                answer = (
                    "Tôi hỗ trợ các yêu cầu liên quan đến "
                    "sản phẩm và dịch vụ của Vingroup."
                )

            status = "completed"
        else:
            for item in observations:
                if "error" in item:
                    answers.append(
                        f"Lỗi khi thực hiện {item['tool']}: "
                        f"{item['error']}"
                    )
                    continue

                result = item["result"]

                if item["tool"] == "search_product_catalog":
                    if result:
                        answers.append(
                            "Sản phẩm tìm thấy:\n" +
                            "\n".join(
                                f"- {p.get('name', 'Unknown')}: "
                                f"{p.get('price_vnd', 'N/A')} VND"
                                for p in result
                            )
                        )
                    else:
                        answers.append(
                            "Không tìm thấy sản phẩm phù hợp."
                        )

                elif item["tool"] == "submit_support_ticket":
                    answers.append(
                        f"Đã tạo yêu cầu hỗ trợ cho {result.get('customer_name', customer_name)}. "
                        f"Mã ticket: {result.get('ticket_id')}"
                    )

            answer = "\n".join(answers)
            status = "completed"

        self.trace.append({
            "step": "final_answer",
            "answer": answer
        })

        return {
            "answer": answer,
            "trace": self.trace,
            "iterations": iteration,
            "status": status,
            "tool_calls": [
                item["tool"] for item in observations
            ]
        }

# ═══════════════════════════════════════════════════════════════════════════
# MAIN — Chạy thử nhanh
# ═══════════════════════════════════════════════════════════════════════════

def main():
	user_query = "Tôi muốn xem xe điện VinFast giá dưới 600 triệu."

	print("=== RUNNING CHATBOT BASELINE ===")
	chatbot = ChatbotBaseline()
	print(chatbot.query(user_query))

	print("\n=== RUNNING TOOL CALLING AGENT ===")
	agent = ToolCallingAgent(max_iterations=5)
	result = agent.run(user_query)
	print("Result:", result["answer"])
	print("Trace Log:", json.dumps(agent.trace, indent=2, ensure_ascii=False))

if __name__ == "__main__":
	main()
