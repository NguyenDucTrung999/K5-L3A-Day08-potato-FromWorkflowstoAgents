# Báo cáo cá nhân — 2A202603423_NguyenDucTrung

## 1. Thông tin thành viên

- Họ tên: Nguyen Duc Trung
- MSSV: 2A202603423
- Email: trung.nd@vinuni.edu.vn
- GitHub: cazofi

## 2. Phần việc phụ trách

- Phụ trách Shape A: `workflow` (Deterministic workflow).
- Phụ trách phần Integration: thiết lập môi trường, cấu hình và đồng bộ mã nguồn repository theo chuẩn skeleton-lab.

## 3. Đóng góp cụ thể

- Hiện thực hàm `run_claim` trong `src/lab8/shapes/workflow.py`: quy trình 8 bước xử lý yêu cầu bồi thường đơn hàng tự động, tuân thủ luật nghiệp vụ trần đơn hàng và phê duyệt.
- Đảm bảo tính bền vững (durability) và truyền tham số `crash_at` không bắt lỗi `InjectedCrash`.
- Đảm bảo ranh giới an toàn không để lộ secret hoặc dữ liệu định danh cá nhân (PII) ra trace.

## 4. Bằng chứng

- Bài kiểm thử liên quan: `src/tests/test_public_matrix.py::test_public_single_run_cases`.
- Run ID dẫn chứng: `R-workflow-C-001-s11`.
- Kết quả kiểm thử: 62/62 test của shape workflow đạt 100% pass trên cả 5 seed.

## 5. Công cụ AI đã dùng

- Antigravity AI Assistant: Hỗ trợ rà soát cấu trúc mã nguồn, đối chiếu kiểm thử và kiểm tra hợp lệ format bài nộp.
- Tự kiểm tra: Toàn bộ các dòng code logic đều được kiểm tra chặt chẽ qua bộ test tự động `pytest` và công cụ `lab8.check_submission`.

## 6. Tự đánh giá

- Hoàn thành đầy đủ 100% yêu cầu được giao, các bài test đều pass và không có lỗi vi phạm tiêu chuẩn bảo mật.
