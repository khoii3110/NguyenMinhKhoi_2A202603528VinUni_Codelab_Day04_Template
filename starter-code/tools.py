import json
import os
from typing import List, Dict, Any
from datetime import datetime

RAW_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "raw-data")


# ---------------------------------------------------------------------------
# Tool #1: search_product_catalog
# ---------------------------------------------------------------------------

def search_product_catalog(
    category: str,
    max_price: int = 999999999999
) -> List[Dict[str, Any]]:
    """
    Tra cứu sản phẩm/dịch vụ Vingroup theo danh mục và giá tối đa.
    """
    catalog_file = os.path.join(RAW_DATA_DIR, "product_catalog.json")

    # Kiểm tra file tồn tại
    if not os.path.exists(catalog_file):
        raise FileNotFoundError(f"Không tìm thấy file: {catalog_file}")

    # Đọc dữ liệu JSON
    with open(catalog_file, "r", encoding="utf-8") as file:
        products = json.load(file)

    # Lọc theo category và max_price
    filtered_products = [
        product
        for product in products
        if product.get("category") == category
        and product.get("price_vnd", 0) <= max_price
    ]

    return filtered_products


# ---------------------------------------------------------------------------
# Tool #2: submit_support_ticket
# ---------------------------------------------------------------------------

def submit_support_ticket(
    customer_name: str,
    issue_description: str,
    priority: str = "medium"
) -> Dict[str, Any]:
    """
    Tạo ticket hỗ trợ và lưu vào support_tickets.json.
    """
    tickets_file = os.path.join(RAW_DATA_DIR, "support_tickets.json")

    # Kiểm tra priority hợp lệ
    if priority not in ["low", "medium", "high"]:
        raise ValueError("Priority phải là low, medium hoặc high.")

    # Tạo thư mục nếu chưa tồn tại
    os.makedirs(RAW_DATA_DIR, exist_ok=True)

    # Load tickets hiện có
    if os.path.exists(tickets_file):
        with open(tickets_file, "r", encoding="utf-8") as file:
            tickets = json.load(file)
    else:
        tickets = []

    # Tạo ticket ID
    today = datetime.now().strftime("%Y%m%d")

    today_tickets = [
        ticket for ticket in tickets
        if ticket.get("ticket_id", "").startswith(f"TK-{today}-")
    ]

    seq = len(today_tickets) + 1
    ticket_id = f"TK-{today}-{seq:03d}"

    # Tạo ticket mới
    new_ticket = {
        "ticket_id": ticket_id,
        "customer_name": customer_name,
        "issue_description": issue_description,
        "priority": priority,
        "status": "open",
        "created_at": datetime.now().isoformat()
    }

    # Append ticket
    tickets.append(new_ticket)

    # Lưu vào JSON
    with open(tickets_file, "w", encoding="utf-8") as file:
        json.dump(tickets, file, ensure_ascii=False, indent=4)

    return {
    "ticket_id": ticket_id,
    "customer_name": customer_name,
    "issue_description": issue_description,
    "priority": priority,
    "status": "open"
}


# ---------------------------------------------------------------------------
# TOOL_DEFINITIONS — JSON Schemas cho LLM
# ---------------------------------------------------------------------------

TOOL_DEFINITIONS = [
    {
        "name": "search_product_catalog",
        "description": (
            "Tra cứu sản phẩm/dịch vụ Vingroup theo danh mục "
            "và mức giá tối đa."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Danh mục sản phẩm: xe_dien hoặc du_lich.",
                    "enum": ["xe_dien", "du_lich"]
                },
                "max_price": {
                    "type": "integer",
                    "description": "Giá tối đa tính bằng VNĐ.",
                    "default": 999999999999
                }
            },
            "required": ["category"]
        }
    },
    {
        "name": "submit_support_ticket",
        "description": (
            "Tạo ticket hỗ trợ khách hàng khi có vấn đề "
            "với sản phẩm hoặc dịch vụ Vingroup."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "customer_name": {
                    "type": "string",
                    "description": "Tên khách hàng."
                },
                "issue_description": {
                    "type": "string",
                    "description": "Mô tả vấn đề cần hỗ trợ."
                },
                "priority": {
                    "type": "string",
                    "description": "Mức độ ưu tiên của ticket.",
                    "enum": ["low", "medium", "high"],
                    "default": "medium"
                }
            },
            "required": [
                "customer_name",
                "issue_description"
            ]
        }
    }
]


# ---------------------------------------------------------------------------
# TOOL_MAP — Ánh xạ tên tool → hàm thực thi
# ---------------------------------------------------------------------------

TOOL_MAP = {
    "search_product_catalog": search_product_catalog,
    "submit_support_ticket": submit_support_ticket
}