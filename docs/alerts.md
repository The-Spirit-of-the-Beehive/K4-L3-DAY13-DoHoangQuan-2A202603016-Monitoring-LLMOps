# Template Alert và Runbook

Mỗi alert phải dựa trên triệu chứng người dùng hoặc SLO, không dựa trực tiếp vào tên implementation nội bộ.

## Alert mẫu để tham khảo

Ví dụ dưới đây minh họa mức độ cụ thể cần có. Học viên không cần copy nguyên, nhưng ba alert trong bài nộp nên rõ ràng tương tự: điều kiện là gì, kéo dài bao lâu, ảnh hưởng tới user ra sao và người trực cần kiểm tra gì trước.

- Tên: `HighLatencyP95`
- Severity: `warning`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: latency P95 của `response_sent.latency_ms`
- Điều kiện và thời gian duy trì: `p95(latency_ms) > 3000ms` trong 5 phút
- Ảnh hưởng tới người dùng: người dùng phải chờ lâu hơn trước khi nhận câu trả lời
- Ba bước kiểm tra đầu tiên:
  1. Mở dashboard latency để xác nhận P95/P99 và khoảng thời gian tăng.
  2. Lọc `data/logs.jsonl` trong khoảng đó, lấy một `correlation_id` có `latency_ms` cao.
  3. Mở trace cùng `correlation_id` trên Langfuse, so sánh các span chính để xác định bước nào bất thường.
- Mitigation tạm thời: dựa trên evidence thực tế để rollback prompt, khôi phục cấu hình liên quan, tắt practice scenario hoặc giảm tải khi demo.
- Owner: `student-2A202603016`

## Alert 1

- Tên: `HighLatencyP95`
- Severity: `warning`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: Latency P95 của `response_sent.latency_ms`
- Điều kiện và thời gian duy trì: `p95(latency_ms) > 3000ms` duy trì liên tục trong 5 phút
- Ảnh hưởng tới người dùng: Người dùng nhận phản hồi rất chậm, suy giảm trải nghiệm sử dụng
- Ba bước kiểm tra đầu tiên:
  1. Mở dashboard Latency để xem mốc thời gian P95 tăng vọt và đối chiếu với TTFT.
  2. Lọc file `data/logs.jsonl` tìm các log `response_sent` có `latency_ms > 3000` và lấy `correlation_id`.
  3. Tìm `correlation_id` trên Langfuse để xem span nào chiếm thời gian chính (bước `retrieval` hay `generation`).
- Mitigation tạm thời: Nếu do bước retrieval quá tải, tạm thời tăng timeout hoặc bật fallback context; nếu do prompt mới dài, thực hiện rollback prompt về phiên bản ổn định trước đó.
- Owner: `student-2A202603016`

## Alert 2

- Tên: `HighErrorRate`
- Severity: `critical`
- Duration: `2m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: Guardrail `error_rate_pct_max <= 2%`
- Điều kiện và thời gian duy trì: `error_rate_pct > 2.0%` duy trì trong 2 phút
- Ảnh hưởng tới người dùng: Nhiều request trả về lỗi HTTP 500, người dùng không nhận được câu trả lời
- Ba bước kiểm tra đầu tiên:
  1. Mở dashboard Error Rate để xác định lượng request lỗi và phân loại `error_type`.
  2. Lọc log `request_failed` trong `data/logs.jsonl`, trích xuất `correlation_id` và thông báo lỗi chi tiết (`payload.detail`).
  3. Kiểm tra trace trên Langfuse để xác định module gây lỗi (vector store timeout, model connection error).
- Mitigation tạm thời: Khởi động lại service phụ thuộc (như vector store/cache), bật circuit breaker hoặc trả câu trả lời fallback an toàn thay vì crash request.
- Owner: `student-2A202603016`

## Alert 3

- Tên: `LowRetrievalSuccessRate`
- Severity: `warning`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: Guardrail `retrieval_success_rate_pct_min >= 90%`
- Điều kiện và thời gian duy trì: `retrieval_success_rate_pct < 90.0%` duy trì trong 5 phút
- Ảnh hưởng tới người dùng: AI trả lời không có tài liệu dẫn chứng hoặc trả lời sai lệch do thiếu context
- Ba bước kiểm tra đầu tiên:
  1. Mở panel Errors trên dashboard để kiểm tra tỷ lệ retrieval thành công theo thời gian.
  2. Kiểm tra log sự kiện `tool_name == "retrieval"` có `tool_success == false`.
  3. Mở span `retrieval` trên Langfuse để xem exception hoặc lỗi kết nối tới cơ sở tri thức.
- Mitigation tạm thời: Kiểm tra trạng thái vector store, chuyển tạm sang bộ nhớ cache tĩnh hoặc hạ tải tìm kiếm ngữ nghĩa.
- Owner: `student-2A202603016`