"""
competency_framework.py
------------------------
Mã hoá lại khung 04 miền năng lực / 11 năng lực và 03 mức độ tư duy
theo tài liệu "Các bước soạn NHCH theo năng lực" do người dùng cung cấp.

Đây là "nguồn sự thật" (single source of truth) cho toàn bộ công cụ —
mọi prompt gửi cho model đều build từ dữ liệu ở đây, để khi cần chỉnh
sửa khung năng lực, chỉ cần sửa 1 chỗ.
"""

from dataclasses import dataclass
from enum import Enum


class ThinkingLevel(str, Enum):
    APPLY = "Vận dụng"
    ANALYZE = "Phân tích"
    EVALUATE = "Đánh giá"


@dataclass(frozen=True)
class Competency:
    code: str          # ví dụ "B.4"
    name: str           # tên năng lực
    domain_code: str    # "A" | "B" | "C" | "D"
    domain_name: str
    # gợi ý loại câu hỏi tương ứng, dùng để build prompt cho model
    guidance: str


# 04 miền năng lực và 11 năng lực — trích nguyên văn từ tài liệu gốc.
COMPETENCIES: list[Competency] = [
    Competency(
        "A.1", "Áp dụng khái niệm cơ bản của y học",
        "A", "Áp dụng khái niệm cơ bản của y học và y học dự phòng",
        "Hỏi về cơ chế bệnh sinh, sinh lý/sinh lý bệnh nền tảng liên quan "
        "trực tiếp đến tình huống — không hỏi kiến thức sách giáo khoa "
        "chung chung, phải neo vào dữ kiện của ca bệnh.",
    ),
    Competency(
        "A.2", "Áp dụng khái niệm cơ bản của y học dự phòng",
        "A", "Áp dụng khái niệm cơ bản của y học và y học dự phòng",
        "Hỏi về nguyên lý dự phòng (dự phòng cấp 1/2/3, yếu tố nguy cơ, "
        "sàng lọc) áp dụng cho nhóm bệnh nhân của ca này.",
    ),
    Competency(
        "B.3", "Bệnh sử/tiền sử/thăm khám thực thể",
        "B", "Chẩn đoán ban đầu",
        "Hỏi thí sinh nhận diện dữ kiện bệnh sử/tiền sử/khám thực thể có "
        "giá trị nhất, liên quan nhất đến vấn đề hiện tại — không lẫn dữ "
        "kiện cận lâm sàng vào phần này.",
    ),
    Competency(
        "B.4", "Cận lâm sàng/xét nghiệm chẩn đoán",
        "B", "Chẩn đoán ban đầu",
        "Có 2 dạng nên khai thác riêng: "
        "(a) CHỈ ĐỊNH — cận lâm sàng nào cần làm tiếp theo và vì sao; "
        "(b) ĐỌC KẾT QUẢ — diễn giải kết quả cận lâm sàng đã có (không "
        "suy diễn quá mức từ một dấu hiệu đơn lẻ).",
    ),
    Competency(
        "B.5", "Chẩn đoán",
        "B", "Chẩn đoán ban đầu",
        "Yêu cầu tổng hợp toàn bộ dữ kiện lâm sàng + cận lâm sàng để đưa "
        "ra chẩn đoán/nhận định phù hợp nhất; các lựa chọn phải cùng là "
        "chẩn đoán, không lẫn xử trí.",
    ),
    Competency(
        "B.6", "Tiên lượng/kết cục",
        "B", "Chẩn đoán ban đầu",
        "Hỏi về yếu tố có giá trị nhất để tiên lượng diễn tiến/kết cục, "
        "hoặc kết cục nào có khả năng xảy ra nhất dựa trên dữ kiện hiện có.",
    ),
    Competency(
        "C.7", "Duy trì sức khỏe/phòng bệnh",
        "C", "Xử trí ban đầu",
        "Hỏi về biện pháp dự phòng/duy trì sức khỏe phù hợp với ca bệnh "
        "này (dự phòng tái phát, tư vấn trước — trong — sau xử trí).",
    ),
    Competency(
        "C.8", "Điều trị bằng thuốc",
        "C", "Xử trí ban đầu",
        "Hỏi lựa chọn/điều chỉnh thuốc điều trị phù hợp nhất với tình "
        "huống, có cân nhắc chống chỉ định/bệnh nền của bệnh nhân.",
    ),
    Competency(
        "C.9", "Can thiệp lâm sàng",
        "C", "Xử trí ban đầu",
        "Hỏi về thủ thuật/can thiệp lâm sàng (không phải thuốc) phù hợp "
        "nhất ở thời điểm hiện tại của ca bệnh.",
    ),
    Competency(
        "C.10", "Quản lý ca bệnh",
        "C", "Xử trí ban đầu",
        "Hỏi về kế hoạch theo dõi/quản lý tổng thể ca bệnh khi dữ liệu "
        "hiện tại chưa đủ để kết luận — ưu tiên phương án an toàn, hợp lý.",
    ),
    Competency(
        "D.11", "Giao tiếp và tính chuyên nghiệp",
        "D", "Cộng tác và giao tiếp",
        "Hỏi về cách giao tiếp/tư vấn với người bệnh, người nhà, đồng "
        "nghiệp hoặc phối hợp liên chuyên khoa phù hợp nhất trong ca này.",
    ),
]

COMPETENCY_BY_CODE = {c.code: c for c in COMPETENCIES}

# Bảng kiểm 12 tiêu chí trước khi duyệt câu hỏi — trích nguyên văn tài liệu gốc.
REVIEW_CHECKLIST: list[tuple[str, str]] = [
    ("Chung", "Câu hỏi lượng giá 1 khái niệm quan trọng"),
    ("Chung", "Câu hỏi ở dạng tình huống kiểm tra sự vận dụng kiến thức"),
    ("Chung", "Từ ngữ diễn đạt rõ ràng, cụ thể, không mơ hồ "
              "(không dùng \"thỉnh thoảng\", \"thường xuyên\", \"có thể\"...)"),
    ("Thân tình huống", "Thông tin theo trình tự hợp lý "
                         "(Tuổi giới → Nơi đến khám → Bệnh sử → tiền căn → "
                         "sinh hiệu → khám lâm sàng → cận lâm sàng)"),
    ("Thân tình huống", "Cung cấp đầy đủ thông tin, không viết thừa"),
    ("Câu hỏi dẫn", "Câu hỏi khẳng định, rõ ràng, kết thúc bằng dấu chấm hỏi"),
    ("Câu hỏi dẫn", "Che kín lựa chọn vẫn trả lời được bằng thân + câu dẫn"),
    ("Lựa chọn", "Lựa chọn ngắn gọn, độ dài tương đương nhau"),
    ("Lựa chọn", "Các lựa chọn tương đồng về hình thức và nội dung"),
    ("Lựa chọn", "Không có lỗi kỹ thuật (lỗi hội tụ, lặp từ, đáp án dài "
                  "nhất, khoảng số liệu chồng lấp, từ tuyệt đối, "
                  "\"tất cả đều đúng/sai\"...)"),
    ("Lựa chọn", "Mồi nhử hợp lý, có tính hấp dẫn (plausible)"),
    ("Đáp án", "Đáp án đủ thuyết phục, không gây tranh cãi"),
]

# Danh sách các cụm từ tuyệt đối cần tránh trong lựa chọn — dùng cho
# bước kiểm tra kỹ thuật tự động (validator.py).
ABSOLUTE_WORDS = [
    "luôn luôn", "không bao giờ", "tất cả đều", "chỉ có", "duy nhất",
    "toàn bộ", "tuyệt đối", "mọi trường hợp", "100%", "không thể",
]

CONVERGENCE_TRAP_PATTERNS = [
    "tất cả các đáp án trên", "tất cả các ý trên", "cả a, b, c đều đúng",
    "cả a, b, c đều sai", "không có đáp án nào đúng",
]

# Bộ khung mặc định cho 10 câu hỏi/1 tình huống, bao phủ đúng các mảng
# người dùng yêu cầu: chẩn đoán, cận lâm sàng cần thiết, đọc kết quả cận
# lâm sàng, điều trị, tiên lượng, dự phòng — cộng thêm bệnh sử/khám,
# can thiệp, quản lý ca và giao tiếp để câu hỏi bao phủ đủ 4 miền năng lực.
# Có thể truyền blueprint khác vào generator nếu muốn tỉ lệ khác.
DEFAULT_BLUEPRINT: list[tuple[str, ThinkingLevel]] = [
    ("B.3", ThinkingLevel.APPLY),      # Bệnh sử/tiền sử/thăm khám
    ("A.1", ThinkingLevel.APPLY),      # Khái niệm y học cơ bản áp dụng vào ca
    ("B.4", ThinkingLevel.ANALYZE),    # Cận lâm sàng cần chỉ định tiếp theo
    ("B.4", ThinkingLevel.ANALYZE),    # Đọc/diễn giải kết quả cận lâm sàng đã có
    ("B.5", ThinkingLevel.EVALUATE),   # Chẩn đoán
    ("B.6", ThinkingLevel.EVALUATE),   # Tiên lượng/kết cục
    ("C.7", ThinkingLevel.EVALUATE),   # Dự phòng/duy trì sức khỏe
    ("C.8", ThinkingLevel.EVALUATE),   # Điều trị bằng thuốc
    ("C.9", ThinkingLevel.EVALUATE),   # Can thiệp lâm sàng / quản lý ca
    ("D.11", ThinkingLevel.EVALUATE),  # Giao tiếp và tính chuyên nghiệp
]
