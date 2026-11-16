# Báo cáo cá nhân — 2A202603423_NguyenDucTrung

## 1. Thông tin thành viên

- Họ tên: Nguyen Duc Trung
- MSSV: 2A202603423
- GitHub: NguyenDucTrung999

## 2. Phần việc phụ trách

- Phụ trách tầng bền vững (durability), sổ cái (ledger) và kiểm thử sự cố (crash test).
- Phụ trách đánh giá (evaluation): chạy benchmark 4 kiến trúc qua 5 seed ngẫu nhiên và phân tích số liệu đối chuẩn.

## 3. Đóng góp cụ thể

- Thực hiện kiểm thử tính lũy nghiệm (idempotency) và độ an toàn khi có sự cố dừng đột ngột (crash safety).
- Đảm bảo hệ thống đạt chỉ số toàn vẹn 20/20 trên suite kịch bản crash (`before_effect`, `after_effect_before_checkpoint`, `after_checkpoint`), ngăn chặn hoàn toàn lỗi ghi bồi thường hai lần (double refund).
- Thực thi công cụ đo đạc thực nghiệm benchmark qua 70 trial cho mỗi kiến trúc trên tập dữ liệu công khai, thu thập số liệu tỷ lệ thành công (pass rate, pass^5), độ phân tán (variance) và chi phí thực thi.

## 4. Bằng chứng

- Bài kiểm thử liên quan: `src/tests/test_crash_suite.py::test_crash_suite_20`.
- File báo cáo sự cố: `src/reports/crash.json` đạt điểm an toàn `20/20`.
- File báo cáo đối chuẩn: `src/reports/benchmark.json`.

## 5. Công cụ AI đã dùng

- Antigravity AI Assistant: Hỗ trợ rà soát cấu trúc mã nguồn, đối chiếu kiểm thử và kiểm tra hợp lệ format bài nộp.
- Tự kiểm tra: Toàn bộ kết quả đều được đối chiếu chặt chẽ qua bộ kiểm thử tự động `pytest` và công cụ `lab8.check_submission`.

## 6. Tự đánh giá

- Hoàn thành đầy đủ 100% nhiệm vụ được giao, vượt qua toàn bộ 20/20 kịch bản sự cố và đảm bảo các chỉ số đo đạc chính xác tuyệt đối.
