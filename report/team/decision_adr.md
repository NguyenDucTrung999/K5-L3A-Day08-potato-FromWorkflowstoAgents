# Decision record

Điền sau dấu `:` trên cùng dòng, không xóa nhãn. Giảng viên và `python -m lab8.check_submission` (chạy trong `src/`) đọc các dòng này bằng máy. Không đổi tên hay dời file này khỏi `report/team/`.
`Shape chọn` phải là đúng một trong: `workflow`, `single`, `orchestrator`, `swarm`. Đây là shape được chấm cổng hidden.

- Shape chọn: workflow
- Commit hash: 2d91c3f
- Run id dẫn chứng: R-workflow-C-001-s11
- Pass rate / pass^5 / seed min-max / variance: 1.000 / 1.000 / 1.000 - 1.000 / 0.000000
- Cost per success (mô phỏng, VND): 27.86
- Crash safety: 20/20 (src/reports/crash.json)
- Secret leak / approval bypass: 0 / 0

## Vì sao shape này

Workflow là kiến trúc tất định (deterministic), thực hiện các bước tuần tự rõ ràng theo code Python thuần. Trên bộ dữ liệu 14 claim qua 5 seed (tổng 70 trial), workflow đạt tỷ lệ pass tuyệt đối 1.000, pass^5 đạt 1.000 với phương sai seed variance bằng 0.0. Do không gọi mô hình để quyết định tiền bồi thường, workflow hoàn toàn miễn nhiễm trước prompt injection và sự sai lệch thông tin trong ticket khách hàng. Hơn nữa, chi phí của workflow là thấp nhất (27.86 VND/success so với 49.57 VND của swarm). Theo nguyên tắc chọn kiến trúc ít tự chủ nhất mà vẫn giải quyết trọn vẹn và an toàn bài toán, workflow là lựa chọn tối ưu nhất.

## Có đáng đổi lấy multi-agent không

Không đáng. Khi chuyển sang kiến trúc multi-agent (swarm), hệ thống phải chịu chi phí cao hơn 78% (49.57 VND so với 27.86 VND), số lượt gọi mô hình tăng lên trong khi tỷ lệ thành công bị suy giảm (pass rate 0.986, pass^5 0.929 do lỗi ở seed 55 khi swarm tin vào lời khai trong ticket). Độ bất định (variance) tăng lên 0.000816. Quyết định chỉ có thể đảo ngược nếu bài toán đòi hỏi xử lý ngữ nghĩa phi cấu trúc phức tạp, đàm phán nhiều bên hoặc các bước linh hoạt mà mã nguồn tuần tự không thể bao quát hết bằng quy tắc.

## Trace và bằng chứng

Trace của workflow ghi nhận tối giản và chính xác các sự kiện cốt lõi: claim_loaded, decision, lookup_order, quote, và crash. Các trường nhạy cảm tuyệt đối không được ghi vào trace bao gồm: parent_secret, tiêu đề Authorization (raw_headers), số điện thoại, địa chỉ giao hàng và ghi chú nội bộ của đơn hàng. Đội ngũ an toàn thông tin (security) có thể kiểm chứng tính bảo mật bằng công cụ quét tự động regex tìm kiếm tiền tố cấm CANARY_SECRET trên toàn bộ các file trace trong thư mục traces/.

## Giới hạn

MockLLM là mô hình mô phỏng cố định theo seed, không phản ánh toàn diện hành vi phong phú và rủi ro trôi dạt (drift) của mô hình sản xuất thực tế. Độ trễ (latency) của hệ thống là unavailable do không đo thời gian mạng. Số liệu chi phí là giá trị mô phỏng dựa trên config/pricing.yaml, không phải hóa đơn dịch vụ đám mây thực tế.
