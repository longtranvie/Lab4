"""
TravelBuddy Tools - Bộ công cụ cho trợ lý du lịch thông minh.

Gồm 3 tools: search_flights, search_hotels, calculate_budget.
"""

import logging
from typing import Optional

from langchain_core.tools import tool

logger = logging.getLogger(__name__)

# ============================================================
# MOCK DATA — Dữ liệu giả lập hệ thống du lịch
# Giá có logic: cuối tuần đắt hơn, hạng cao hơn đắt hơn
# ============================================================

FLIGHTS_DB: dict[tuple[str, str], list[dict]] = {
    ("Hà Nội", "Đà Nẵng"): [
        {"airline": "Vietnam Airlines", "departure": "06:00", "arrival": "07:20", "price": 1_450_000, "class": "economy"},
        {"airline": "Vietnam Airlines", "departure": "14:00", "arrival": "15:20", "price": 2_800_000, "class": "business"},
        {"airline": "VietJet Air", "departure": "08:30", "arrival": "09:50", "price": 1_100_000, "class": "economy"},
        {"airline": "Bamboo Airways", "departure": "16:00", "arrival": "17:20", "price": 1_350_000, "class": "economy"},
    ],
    ("Hà Nội", "Phú Quốc"): [
        {"airline": "Vietnam Airlines", "departure": "07:00", "arrival": "09:15", "price": 1_800_000, "class": "economy"},
        {"airline": "Vietnam Airlines", "departure": "13:00", "arrival": "15:15", "price": 3_200_000, "class": "business"},
        {"airline": "VietJet Air", "departure": "10:00", "arrival": "12:15", "price": 1_400_000, "class": "economy"},
    ],
    ("Hà Nội", "Hồ Chí Minh"): [
        {"airline": "Vietnam Airlines", "departure": "06:00", "arrival": "08:10", "price": 1_600_000, "class": "economy"},
        {"airline": "Vietnam Airlines", "departure": "09:00", "arrival": "11:10", "price": 2_900_000, "class": "business"},
        {"airline": "VietJet Air", "departure": "07:30", "arrival": "09:40", "price": 1_200_000, "class": "economy"},
        {"airline": "Bamboo Airways", "departure": "15:00", "arrival": "17:10", "price": 1_500_000, "class": "economy"},
    ],
    ("Hồ Chí Minh", "Đà Nẵng"): [
        {"airline": "Vietnam Airlines", "departure": "08:00", "arrival": "09:20", "price": 1_300_000, "class": "economy"},
        {"airline": "VietJet Air", "departure": "11:00", "arrival": "12:20", "price": 950_000, "class": "economy"},
        {"airline": "Bamboo Airways", "departure": "14:00", "arrival": "15:20", "price": 1_150_000, "class": "economy"},
    ],
    ("Hồ Chí Minh", "Phú Quốc"): [
        {"airline": "Vietnam Airlines", "departure": "09:00", "arrival": "10:00", "price": 1_100_000, "class": "economy"},
        {"airline": "VietJet Air", "departure": "12:00", "arrival": "13:00", "price": 850_000, "class": "economy"},
        {"airline": "Bamboo Airways", "departure": "17:00", "arrival": "18:00", "price": 980_000, "class": "economy"},
    ],
    ("Đà Nẵng", "Phú Quốc"): [
        {"airline": "Vietnam Airlines", "departure": "10:00", "arrival": "11:45", "price": 1_700_000, "class": "economy"},
        {"airline": "VietJet Air", "departure": "14:30", "arrival": "16:15", "price": 1_300_000, "class": "economy"},
    ],
}

HOTELS_DB: dict[str, list[dict]] = {
    "Đà Nẵng": [
        {"name": "Mường Thanh Luxury", "price_per_night": 1_200_000, "rating": 4.5, "type": "luxury"},
        {"name": "Novotel Đà Nẵng", "price_per_night": 1_800_000, "rating": 4.7, "type": "luxury"},
        {"name": "Fivitel Đà Nẵng", "price_per_night": 650_000, "rating": 4.0, "type": "standard"},
        {"name": "Sala Danang Beach Hotel", "price_per_night": 850_000, "rating": 4.2, "type": "standard"},
        {"name": "Backpacker Hostel Đà Nẵng", "price_per_night": 250_000, "rating": 3.8, "type": "budget"},
    ],
    "Phú Quốc": [
        {"name": "Vinpearl Resort Phú Quốc", "price_per_night": 3_500_000, "rating": 4.8, "type": "luxury"},
        {"name": "Sol Beach House", "price_per_night": 2_200_000, "rating": 4.5, "type": "luxury"},
        {"name": "Tropicana Resort", "price_per_night": 900_000, "rating": 4.1, "type": "standard"},
        {"name": "Ocean Pearl Hotel", "price_per_night": 650_000, "rating": 3.9, "type": "standard"},
        {"name": "Phu Quoc Backpacker", "price_per_night": 200_000, "rating": 3.5, "type": "budget"},
    ],
    "Hồ Chí Minh": [
        {"name": "Rex Hotel", "price_per_night": 2_500_000, "rating": 4.6, "type": "luxury"},
        {"name": "Liberty Central", "price_per_night": 1_500_000, "rating": 4.3, "type": "standard"},
        {"name": "Cozrum Homes", "price_per_night": 600_000, "rating": 4.0, "type": "standard"},
        {"name": "The Common Room", "price_per_night": 180_000, "rating": 3.7, "type": "budget"},
    ],
    "Hà Nội": [
        {"name": "Sofitel Legend Metropole", "price_per_night": 4_500_000, "rating": 4.9, "type": "luxury"},
        {"name": "Hanoi La Siesta Hotel", "price_per_night": 1_400_000, "rating": 4.4, "type": "standard"},
        {"name": "Old Quarter View Hotel", "price_per_night": 700_000, "rating": 4.1, "type": "standard"},
        {"name": "Hanoi Backpacker Hostel", "price_per_night": 150_000, "rating": 3.6, "type": "budget"},
    ],
}


def _format_price(amount: int) -> str:
    """Format số tiền VND: 1450000 -> '1.450.000đ'"""
    return f"{amount:,.0f}đ".replace(",", ".")


def _find_flights(origin: str, destination: str) -> list[dict]:
    """Tìm chuyến bay theo cả hai chiều của tuple key."""
    # Tìm trực tiếp
    flights = FLIGHTS_DB.get((origin, destination))
    if flights:
        return flights

    # Thử tra ngược chiều
    reverse = FLIGHTS_DB.get((destination, origin))
    if reverse:
        logger.info("Tìm thấy chuyến bay chiều ngược: %s -> %s", destination, origin)
        return reverse

    return []


@tool
def search_flights(origin: str, destination: str) -> str:
    """Tìm chuyến bay giữa hai thành phố Việt Nam.
    Trả về danh sách chuyến bay với hãng, giờ bay, giá vé và hạng ghế.

    Args:
        origin: Thành phố đi (VD: "Hà Nội")
        destination: Thành phố đến (VD: "Đà Nẵng")
    """
    logger.info("[search_flights] Tìm chuyến bay: %s -> %s", origin, destination)

    flights = _find_flights(origin, destination)

    if not flights:
        logger.warning("[search_flights] Không tìm thấy chuyến bay: %s -> %s", origin, destination)
        return f"Không tìm thấy chuyến bay từ {origin} đến {destination}."

    # Sắp xếp theo giá tăng dần
    sorted_flights = sorted(flights, key=lambda f: f["price"])

    lines = [f"Tìm thấy {len(sorted_flights)} chuyến bay từ {origin} đến {destination}:\n"]
    for i, f in enumerate(sorted_flights, 1):
        lines.append(
            f"{i}. {f['airline']} | {f['departure']}→{f['arrival']} | "
            f"{_format_price(f['price'])} | Hạng: {f['class']}"
        )

    result = "\n".join(lines)
    logger.info("[search_flights] Kết quả:\n%s", result)
    return result


@tool
def search_hotels(city: str, max_price: Optional[int] = None) -> str:
    """Tìm khách sạn tại thành phố. Có thể lọc theo giá tối đa mỗi đêm.

    Args:
        city: Tên thành phố (VD: "Đà Nẵng")
        max_price: Giá tối đa mỗi đêm (VND), bỏ trống để xem tất cả
    """
    logger.info("[search_hotels] Tìm khách sạn tại: %s (max: %s)", city, _format_price(max_price) if max_price else "không giới hạn")

    hotels = HOTELS_DB.get(city)

    if not hotels:
        logger.warning("[search_hotels] Không có dữ liệu khách sạn cho: %s", city)
        return f"Không tìm thấy khách sạn tại {city}."

    # Lọc theo giá nếu có
    if max_price is not None:
        hotels = [h for h in hotels if h["price_per_night"] <= max_price]
        if not hotels:
            return f"Không có khách sạn nào tại {city} dưới {_format_price(max_price)}/đêm."

    # Sắp xếp theo rating giảm dần
    sorted_hotels = sorted(hotels, key=lambda h: h["rating"], reverse=True)

    lines = [f"Tìm thấy {len(sorted_hotels)} khách sạn tại {city}:\n"]
    for i, h in enumerate(sorted_hotels, 1):
        lines.append(
            f"{i}. {h['name']} | {_format_price(h['price_per_night'])}/đêm | "
            f"Rating: {h['rating']} | Loại: {h['type']}"
        )

    result = "\n".join(lines)
    logger.info("[search_hotels] Kết quả:\n%s", result)
    return result


@tool
def calculate_budget(total_budget: int, expenses: str) -> str:
    """Tính ngân sách còn lại sau khi trừ các khoản chi phí.

    Args:
        total_budget: Tổng ngân sách ban đầu (VND)
        expenses: Chuỗi mô tả các khoản chi, cách nhau bởi dấu phẩy.
                  Định dạng: 'tên_khoản:số_tiền' (VD: 'vé_máy_bay:1450000,khách_sạn:650000')
    """
    logger.info("[calculate_budget] Tổng=%s, chi_phi='%s'", _format_price(total_budget), expenses)

    try:
        parsed: dict[str, int] = {}
        for item in expenses.split(","):
            item = item.strip()
            if not item:
                continue
            if ":" not in item:
                return f"Lỗi: khoản chi '{item}' không đúng định dạng 'tên:số_tiền'."
            name, amount_str = item.rsplit(":", 1)
            parsed[name.strip()] = int(amount_str.strip())

    except ValueError as e:
        logger.error("Lỗi parse chi phí: %s", e)
        return f"Lỗi: không thể đọc số tiền — hãy dùng định dạng 'tên_khoản:số_tiền' (VD: 'vé_máy_bay:1450000')."

    total_expenses = sum(parsed.values())
    remaining = total_budget - total_expenses

    # Format bảng chi tiết
    lines = ["Bảng chi phí:"]
    for name, amount in parsed.items():
        lines.append(f"  - {name}: {_format_price(amount)}")
    lines.append("  ---")
    lines.append(f"  Tổng chi: {_format_price(total_expenses)}")
    lines.append(f"  Ngân sách: {_format_price(total_budget)}")

    if remaining >= 0:
        lines.append(f"  Còn lại: {_format_price(remaining)}")
    else:
        lines.append(f"  Vượt ngân sách {_format_price(abs(remaining))}! Cần điều chỉnh.")

    result = "\n".join(lines)
    logger.info("[calculate_budget] Kết quả:\n%s", result)
    return result


def get_all_tools() -> list:
    """Trả về danh sách tất cả tools cho agent."""
    return [search_flights, search_hotels, calculate_budget]
