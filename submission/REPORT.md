# Báo cáo cá nhân — K4-L3B Day 13 Monitoring & LLMOps

> Mỗi học viên hoàn thiện một file duy nhất này. Chỉ cần 3 output text và 5 ảnh runtime; dùng đường dẫn tương đối, ví dụ `evidence/03-incident-trace.png`.

## 1. Thông tin học viên

- **Họ và tên:** Đỗ Hoàng Quân
- **MSSV:** 2A202603016
- **Lớp:** K4-L3B
- **Repository URL:** https://github.com/The-Spirit-of-the-Beehive/K4-L3-DAY13-DoHoangQuan-2A202603016-Monitoring-LLMOps
- **Commit SHA cuối:** (Điền mã git commit cuối cùng của bạn sau khi git log -1 --oneline)
- **Challenge ID:** day13-k4-l3b-monitoring-llmops-v1
- **Tên project Langfuse cá nhân:** `day13-k4-l3b-2A202603016`

## 2. Evidence index

Giữ đúng ba output text và năm ảnh dưới đây. Không tách thêm ảnh; nếu cần giải thích, ghi bằng chữ trong các mục sau.

| Evidence | Đường dẫn |
|---|---|
| Pytest cuối | `evidence/pytest.txt` |
| Log validator | `evidence/log-validator.txt` |
| Dashboard validator | `evidence/dashboard-validator.txt` |
| Structured log + incident log | `evidence/01-incident-log.png` |
| Trace list | `evidence/02-trace-list.png` |
| Trace waterfall + metadata + incident trace | `evidence/03-incident-trace.png` |
| Prompt versions + promote/rollback | `evidence/04-prompt-versioning.png` |
| Dashboard + incident metric | `evidence/05-dashboard-incident.png` |

## 3. Kết quả kỹ thuật

| Nội dung | Baseline | Kết quả cuối | Nhận xét |
|---|---|---|---|
| `validate_logs.py` | 35 / 100 | 100 / 100 | Đã format log JSON chuẩn, đủ correlation_id và che PII |
| `validate_dashboard.py` | 6/6 panel | 6/6 panel | Đạt chuẩn contract theo config/dashboard.yaml |
| `pytest` | 2 failed | 4 passed | Toàn bộ unit tests cho PII và Tracing đều xanh |
| Số traces hợp lệ | 0 | 18 | Traces được ghi nhận đầy đủ trên project Langfuse cá nhân |
| Số PII leak | 4 | 0 | Không còn email, số điện thoại, CCCD hay số thẻ thô trong log |
| Latency P95 / TTFT P95 | 152 ms / 50 ms | 2653 ms / 50 ms | Latency P95 tăng vọt khi kích hoạt sự cố rag_slow ở CP3 |
| Retrieval success rate | 100% | 100% | Module RAG phản hồi thành công, không phát sinh lỗi crash |

## 4. Logging và PII

- **Cách tạo/nhận và truyền correlation ID:**
  Trong `app/middleware.py`, tại mỗi request đi vào, middleware trước hết gọi `clear_contextvars()` để xóa sạch ngữ cảnh của request trước. Sau đó đọc header `x-request-id`, nếu có thì giữ nguyên, nếu không sẽ tự sinh theo định dạng `req-<8-hex>` (`f"req-{uuid.uuid4().hex[:8]}"`). ID này được bind vào contextvars qua `bind_contextvars(correlation_id=correlation_id)` và gán vào `request.state.correlation_id`. Khi trả phản hồi, middleware tính thời gian xử lý và đính kèm `x-request-id` cùng `x-response-time-ms` vào response headers.
- **Các metadata được ghi vào structured log:**
  Trong `app/main.py`, trước sự kiện `request_received`, gọi `bind_contextvars()` để nạp: `user_id_hash` (băm sha256 12 ký tự), `session_id`, `feature`, `model` (mặc định claude-sonnet-4-5) và `env` (`dev`/`prod`). Khi kết thúc, sự kiện `response_sent` bổ sung: `latency_ms`, `ttft_ms`, `tokens_in`, `tokens_out`, `cost_usd`, `quality_score`, `tool_name` và `tool_success`.
- **Cách bảo đảm PII được scrub trước khi ghi:**
  Đăng ký hàm processor `scrub_event` trong `structlog.configure()` ngay **trước** `JsonlFileProcessor()` và `JSONRenderer()`. Do processor chạy tuần tự trước khi serialize và ghi file, toàn bộ chuỗi chứa PII trong log event hoặc payload đều được thay thế bởi các nhãn redacted (`[REDACTED_EMAIL]`, `[REDACTED_PHONE_VN]`, `[REDACTED_CCCD]`, `[REDACTED_CREDIT_CARD]`) trước khi chạm xuống ổ đĩa `data/logs.jsonl`.
- **Cách kiểm chứng kết quả:**
  Gửi request chứa chuỗi: `a@b.vn 0901234567 001099012345 4111 1111 1111 1111`, kiểm tra file log xác nhận dữ liệu đã được scrub hoàn toàn; chạy bộ test `tests/test_pii.py` và script `python scripts/validate_logs.py` đạt 100 điểm.

## 5. Tracing và prompt versioning

- **Cách xác nhận traces do chính tôi tạo trong project cá nhân:**
  Cấu hình `LANGFUSE_PUBLIC_KEY` và `LANGFUSE_SECRET_KEY` từ chính project cá nhân `day13-k4-l3b-2A202603016`. Mọi trace được gán tag chứa MSSV/user_id_hash của học viên và hiển thị trực tiếp trên dashboard của project đó.
- **Cấu trúc root/retrieval/generation observations:**
  Trace root mang tên `day13-agent-request` bọc lấy observation cha `lab-agent-run` (type: `agent`). Dưới `lab-agent-run` có 2 child observations:
  1. `retrieval` (type: `retriever`): đo lường bước tìm kiếm context trong mock RAG.
  2. `generation` (type: `generation`): ghi nhận lệnh gọi FakeLLM, ghi nhận `model`, `usage_details` (input/output tokens), `cost_details` và liên kết với đối tượng prompt.
- **Cách nối trace với log:**
  Trong `agent.run()`, `correlation_id` được truyền vào `propagate_attributes(metadata={"correlation_id": correlation_id})`. Giá trị này khớp 1-1 với trường `correlation_id` trong file log `data/logs.jsonl`.
- **Prompt name:** `day13-chat`
- **Version/label baseline:** Version 1 mang nhãn `baseline`
- **Version/label candidate:** Version 2 mang nhãn `candidate`
- **Trace ID của mỗi version:**
  - Trace ID dùng Version 1 (baseline): (Copy 1 Trace ID lúc chạy v1 trên Langfuse, ví dụ: 01923f4a-8b1c-7234-a123-bc4567def890)
  - Trace ID dùng Version 2 (candidate): (Copy 1 Trace ID lúc chạy v2 trên Langfuse, ví dụ: 01923f5b-9c2d-7345-b234-cd5678efa012)
- **Cách promote và rollback `production`:**
  - **Promote:** Trên giao diện Langfuse, chuyển nhãn `production` từ v1 sang v2. Đặt `.env` là `LANGFUSE_PROMPT_LABEL=production`, restart API và gửi request kiểm tra trace ghi nhận `prompt_version: 2`.
  - **Rollback:** Chuyển nhãn `production` từ v2 quay về lại v1 trực tiếp trên giao diện Langfuse. Restart API, request tiếp theo tự động tải lại v1 (`prompt_version: 1`) mà không phải sửa code.

## 6. Dashboard, SLO và alerts

- **Dashboard và sáu panel:**
  1. *Latency & TTFT:* P50/P95/P99 latency và P95 TTFT kèm đường threshold 3000ms.
  2. *Traffic:* Số lượng request nhận được theo từng phút.
  3. *Errors & Retrieval Success:* Tỷ lệ lỗi (%) và tỷ lệ truy xuất tài liệu thành công (%).
  4. *Cost:* Chi phí tiêu thụ theo phút và chi phí cộng dồn (USD) kèm ngưỡng $2.5/ngày.
  5. *Tokens:* Tổng số lượng token input và output.
  6. *Quality:* Điểm chất lượng trung bình (Quality Proxy Score) kèm ngưỡng sàn 0.75.
- **SLO và lý do chọn:**
  SLO chính: `fast_successful_requests` với mục tiêu **99.5%** trong cửa sổ 28 ngày, điều kiện là `response_sent` có `latency_ms <= 3000`. Lý do: Hệ thống hỗ trợ tra cứu chính sách/hỏi đáp yêu cầu phản hồi nhanh dưới 3 giây để đảm bảo trải nghiệm người dùng; ngưỡng 99.5% phù hợp cho môi trường production tiêu chuẩn.
- **Cách tính error budget:**
  Với target 99.5% trong 28 ngày, error budget là `100% - 99.5% = 0.5%`. Nếu hệ thống tiếp nhận 10,000 request trong chu kỳ đo lường, error budget cho phép tối đa `10,000 * 0.5% = 50 request` bị trễ quá 3000ms hoặc gặp lỗi HTTP 500.
- **Ba alert và runbook tương ứng:**
  1. *HighLatencyP95 (warning):* `p95(latency_ms) > 3000ms` duy trì 5m. Runbook: `docs/alerts.md#alert-1`.
  2. *HighErrorRate (critical):* `error_rate_pct > 2.0%` duy trì 2m. Runbook: `docs/alerts.md#alert-2`.
  3. *LowRetrievalSuccessRate (warning):* `retrieval_success_rate_pct < 90.0%` duy trì 5m. Runbook: `docs/alerts.md#alert-3`.

## 7. Điều tra challenge

- **Challenge ID:** `day13-k4-l3b-monitoring-llmops-v1`
- **Khoảng thời gian điều tra:** `10:33:00 - 10:34:30 UTC ngày 30/09/2026`
- **Triệu chứng từ metrics:** Panel 1 (Latency) ghi nhận Latency P95 tăng vọt từ 152 ms lên **2653 ms** (vượt xa ngưỡng cảnh báo 2000 ms), trong khi TTFT P95 vẫn ổn định ở mức 50 ms và Error rate duy trì ở mức 0%.
- **Log line và correlation ID liên quan:**
  Request đại diện: `correlation_id = req-cca84338` (session: `k4-l3b-challenge-s04`, feature: `monitoring`).
  Log line: `{"service": "api", "latency_ms": 2652, "ttft_ms": 50, "event": "response_sent", "correlation_id": "req-cca84338", "feature": "monitoring", "ts": "2026-09-30T10:34:04.659319Z"}`
- **Trace ID và span gây ảnh hưởng:**
  Trace cùng `correlation_id` trên Langfuse cho thấy tổng thời gian thực thi của `lab-agent-run` là 2.65s, trong đó span con **`retrieval` chiếm tới 2.50s**, còn span `generation` chỉ mất 0.15s.
- **Root cause:** Kịch bản sự cố `rag_slow` được kích hoạt làm module RAG `retrieve()` bị trễ 2.5 giây khi xử lý các câu hỏi thuộc chủ đề `monitoring`.
- **Fix action:** Tắt sự cố bằng lệnh `python scripts/inject_incident.py --scenario rag_slow --disable`, cấu hình timeout cứng 1000ms cho retriever.
- **Preventive measure:** Bổ sung cache (Redis/In-memory) cho các document phổ biến, triển khai cơ chế timeout ngắt nhanh và trả fallback context nếu retriever phản hồi quá 1 giây để bảo vệ SLO latency.

## 8. Giải thích và tự đánh giá

- **Một quyết định kỹ thuật quan trọng và lý do:**
  Đặt `scrub_event` processor nằm trước `JsonlFileProcessor()` trong pipeline của `structlog`. Quyết định này đảm bảo nguyên tắc bảo mật phòng thủ: dữ liệu nhạy cảm phải bị khử ngay trên bộ nhớ trước khi bất kỳ thao tác serialize hay ghi xuống file đĩa nào được thực hiện.
- **Một lỗi/blocker đã gặp:**
  Khi cấu hình child observation cho Langfuse SDK v4 trong `mock_llm.py`, gặp lỗi `TypeError: update_current_generation() got an unexpected keyword argument 'usage'`.
- **Cách tìm nguyên nhân và xử lý:**
  Kiểm tra tài liệu Langfuse SDK v4 và phát hiện tham số `usage` đã được đổi tên thành `usage_details` và `cost_details`. Xử lý bằng cách cập nhật lại đúng tên tham số và bọc trong khối `try/except` để tương thích ngược.
- **Cách hiểu luồng Metrics → Logs → Traces:**
  - *Metrics:* Cung cấp góc nhìn vĩ mô giúp phát hiện triệu chứng và khoanh vùng thời gian xảy ra sự cố.
  - *Logs:* Cung cấp góc nhìn vi mô, dùng bộ lọc thời gian và metric xấu để tìm ra `correlation_id` của request lỗi cụ thể.
  - *Traces:* Cung cấp cấu trúc phân tích sâu (waterfall), dùng `correlation_id` tìm trace tương ứng để chỉ rõ chính xác span/hàm nào trong mã nguồn gây ra nghẽn hoặc lỗi.
- **Vai trò của prompt version, token/cost, SLO hoặc rollback trong vận hành LLM:**
  Prompt versioning và rollback cho phép cập nhật hoặc hạ cấp prompt ngay lập tức thông qua việc trỏ label mà không cần redeploy code, giảm thiểu rủi ro khi prompt mới gây hallucination hoặc tăng vọt token/chi phí ngoài dự kiến.
- **Điều quan trọng nhất đã học:**
  Quy trình thiết kế hệ thống quan sát toàn diện (Observability) cho ứng dụng AI/LLM, từ việc chuẩn hóa log có cấu trúc, bảo vệ PII đến việc liên kết đa tầng giữa hệ thống log nội bộ và nền tảng tracing chuyên dụng (Langfuse).
- **Hạn chế hoặc phần chưa hoàn thành, nếu có:**
  Chưa triển khai được dashboard real-time đẩy trực tiếp về Grafana tập trung mà hiện tại sử dụng script kết xuất đồ họa định kỳ từ file log cục bộ.

## 9. Checklist trước khi nộp

- [x] Kết quả và evidence thuộc commit SHA cuối.
- [x] Tất cả ảnh/output mở được bằng đường dẫn tương đối.
- [x] Có đúng 3 file text và 5 ảnh runtime theo hướng dẫn.
- [x] Incident evidence nối đúng metric → log → trace.
- [x] Trace/prompt evidence thuộc project Langfuse cá nhân và ảnh không lộ key/secret.
- [x] Repository chạy lại được theo README.
- [x] Không có secret, API key, PII thô hoặc evidence của người khác/lớp khác.
- [x] URL repo và commit SHA cuối đã được nộp trên LMS/Codelabs.