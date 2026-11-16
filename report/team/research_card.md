# Research card

File này nằm cố định ở `report/team/research_card.md`; `python -m lab8.check_submission` đọc cột "Nhóm điền" bằng máy.

Phần này nối tiếp phần mini research ở buổi lý thuyết (slide 62–63). Chọn **một** câu R1–R4, điền 6 dòng, rồi biến nó thành **một ablation** chạy được trong lab: giữ nguyên model (MockLLM), tool, seed, corpus và giá, chỉ thay đổi một biến.

| Câu | Nguồn (thư viện tham khảo, slide 68–69) | Câu hỏi gợi ý cho lab |
| --- | --- | --- |
| R1 · Scaling | Google Research 2026, *Towards a Science of Scaling Agent Systems* | Task claims chủ yếu tuần tự hay song song được? Dự đoán thêm investigator sẽ làm pass rate và cost/success thay đổi thế nào. |
| R2 · Failure taxonomy | MAST, NeurIPS 2025, *Why Do Multi-Agent LLM Systems Fail?* | Các trial fail của swarm (seed 55) thuộc nhóm nào: lỗi giao việc, lệch mục tiêu, hay lỗi kiểm chứng? |
| R3 · Architecture choices | AgentArch, AACL 2026 | Nếu đổi topology mà giữ nguyên mọi thứ khác, biến nào phải cố định để kết luận còn đúng? |
| R4 · Evaluation confounders | EMNLP 2026, *Rethinking Evaluation of MAS Efficiency* | Làm sao chứng minh chênh lệch giữa A/B/C/D là do topology, không phải do prompt, tool hay seed? |

## Phiếu của nhóm

Điền vào cột cuối. Không xóa hai cột đầu.

| Field | Hướng dẫn | Nhóm điền |
| --- | --- | --- |
| CÂU | R1 / R2 / R3 / R4 | R3 |
| SOURCE | Paper/blog, năm, URL, loại bằng chứng (benchmark, production report, blog kinh nghiệm) | AgentArch, AACL 2026, benchmark |
| CLAIM | Một kết luận gốc của nguồn. Không viết rộng hơn phạm vi paper | Lựa chọn topology kiến trúc là yếu tố quyết định độ tin cậy và chi phí thực thi của hệ thống tác tử |
| BOUNDARY | Model / dataset / setup giới hạn kết luận đó | Môi trường mô phỏng MockLLM với tập luật nghiệp vụ cố định và dữ liệu bán cấu trúc |
| HYPOTHESIS | Nếu đổi shape A→B (hoặc bật/tắt một thành phần), metric X sẽ đổi theo hướng nào, khoảng bao nhiêu | Nếu đổi từ workflow (Shape A) sang swarm (Shape D), chi phí bồi thường mô phỏng tăng ~78% và phương sai seed_variance tăng từ 0.0 lên >0.0 |
| METHOD | Biến giữ cố định: model, tools, seed, corpus, giá, evaluator. Biến duy nhất được thay đổi: … | Cố định: MockLLM, bộ công cụ, 5 seed (11, 22, 33, 44, 55), tập dữ liệu public_claims, bảng giá simulated. Biến duy nhất thay đổi: shape kiến trúc (workflow vs swarm) |
| FAILURE / METRIC | Một lỗi dự kiến và cách đo nó: pass rate, pass^5, variance, cost/success, leak, bypass | Swarm thất bại ở seed 55 trên claim C-002 do tin thông tin ticket; đo lường bằng pass rate, pass^5 và seed_variance |

## Kết quả ablation

- Lệnh đã chạy (copy nguyên văn): `python -m lab8.benchmark --shapes workflow,swarm --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/benchmark.json`
- Run id / file report: `src/reports/benchmark.json`, run id: `R-workflow-C-001-s11`, `R-swarm-C-002-s55`
- Kết quả so với hypothesis (đúng / sai / không kết luận được), kèm số liệu: Đúng như giả thuyết. Workflow đạt pass rate 1.000, pass^5 1.000, seed_variance 0.000000, cost per success 27.86 VND. Swarm đạt pass rate 0.986, pass^5 0.929, seed_variance 0.000816, cost per success 49.57 VND (chi phí tăng 77.9% so với workflow).
- Giới hạn: MockLLM không phải model sản xuất, latency là `unavailable`.

Muốn đi xa hơn một ablation để lấy điểm cộng thì xem [docs/bonus_topics.md](../../docs/bonus_topics.md).
