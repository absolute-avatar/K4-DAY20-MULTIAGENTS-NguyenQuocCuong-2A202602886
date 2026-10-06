# Báo cáo Lab: Self evolving Agentic

## 1. Thông tin nhóm và cấu hình

| Họ tên | Mã sinh viên | Phần đóng góp |
|---|---|---|
| Nguyễn Quốc Cường | 2A202602886 | Cài đặt harness, chạy thí nghiệm, phân tích và viết báo cáo |

- Cấu hình mô hình: `LAB_MODEL=openai:gpt-4o-mini`, `LAB_TEMPERATURE=0`; các lệnh runner dùng giới hạn mặc định 60 bước và các lỗi lưu trong bản ghi đều xác nhận giới hạn 60. `run.json` không lưu tên model, nên cấu hình này dựa trên thiết lập thí nghiệm, không phải metadata độc lập của từng lượt.
- Môi trường: sáu lượt học của `baseline`/`subagents` và ba lượt thử skill Phần 3.4 chạy trong Docker Linux (Python 3.12.15, Deep Agents 0.7.21). Sáu lượt eval mới nhất của `baseline`/`subagents` chạy trong Docker/WSL theo xác nhận của người thực hiện. Sáu lượt `skills-auto` hiện lưu chạy trực tiếp trên Windows; môi trường `.venv` hiện có Python 3.11.9 và Deep Agents 0.7.21. Đây là khác biệt môi trường làm hạn chế phép so sánh, xem mục 8–9.
- Bộ test ngoại tuyến trên Docker Linux đạt 32/32 sau khi cài curator. Kết quả này xác nhận harness trong Linux; không chứng minh shell của agent hoạt động khi chạy trực tiếp trên Windows.
- Bộ kết quả dùng trong bảng có 18 lượt và 2.361.448 token. Ba lượt thử `skills-auto-dev` có thêm 149.926 token; tổng 21 bản ghi còn lưu là 2.511.374 token. Đây không phải tổng chi phí cả quá trình: các lượt đã ghi đè và ba lời gọi curator không có đủ bản ghi token để cộng chính xác. Ngân sách tối đa chưa được khai báo.
- Commit giả thuyết: `831dc072e0018826431194a806caace366e36c50`, lúc 23:44:50 ngày 06/10/2026 (UTC+7). Tag `freeze`: `b229e44ec346245af32cb5d93d4fc0502864b5f0`, lúc 23:44:57 cùng ngày. Các lượt `skills-auto` hiện lưu bắt đầu từ 00:54:42 đến 00:56:35 ngày 07/10/2026 (UTC+7), sau mốc đóng băng.

## 2. Giả thuyết (commit TRƯỚC tag `freeze`, Phần 4.0)

Các dự đoán này được ghi trước khi chạy bất kỳ tác vụ đánh giá nào. Căn cứ định lượng là sáu lượt học Phần 2 và ba lượt thử skill Phần 3.4; chưa có điểm đánh giá tại thời điểm viết.

- H1 (subagents so với baseline): Dự đoán `baseline` đạt điểm đánh giá cao hơn hoặc bằng `subagents`. Điểm học trung bình là 0,2417 so với 0,1704; hai trace còn quan sát được không có lời giao việc, còn lượt bị giới hạn bước có trace rỗng. Chưa có bằng chứng cấu hình subagent tạo lợi ích.
- H2 (skills-auto so với baseline): Dự đoán `baseline` đạt điểm đánh giá cao hơn hoặc bằng `skills-auto`. Hai skill được giữ hợp lệ nhưng cả ba lượt học thử có `skills_read=0`; vì thế chưa có bằng chứng tác tử dùng được chúng. Kết quả nghiên cứu được nhắc trong `guides/pseudocode/04_curator.md` cũng cảnh báo skill tự sinh có thể không giúp tác vụ mới.
- H3 (tác vụ học so với tác vụ đánh giá): Dự đoán điểm của cùng điều kiện trên tác vụ đánh giá không cao hơn điểm học một cách ổn định, vì mỗi tác vụ đánh giá đổi dữ liệu và thêm quy ước. Nếu một điều kiện tăng trên tập học mà không tăng trên tập đánh giá, đó là dấu hiệu quá khớp hoặc nhiễu, chưa đủ để khẳng định nguyên nhân khi mỗi tác vụ chỉ chạy một lần.

## 3. Làm quen Deep Agents (Phần 0.3)

Căn cứ: đầu ra của `python scripts/tour.py`, sử dụng mô hình giả và không tốn token.

1. Trong kết quả tour, tác tử mặc định có 9 công cụ với các chức năng sau:

   | Công cụ | Chức năng |
   |---|---|
   | `ls` | Liệt kê các tệp và thư mục tại đường dẫn được chỉ định. |
   | `read_file` | Đọc nội dung tệp để tìm hiểu dữ liệu, mã nguồn hoặc yêu cầu. |
   | `write_file` | Ghi nội dung vào tệp, chẳng hạn tạo tệp kết quả. |
   | `edit_file` | Chỉnh sửa nội dung trong tệp bằng cách thay thế đoạn văn bản được chỉ định. |
   | `delete` | Xóa tệp. |
   | `glob` | Tìm tệp theo mẫu đường dẫn hoặc tên tệp, ví dụ `**/*.py`. |
   | `grep` | Tìm nội dung khớp với mẫu tìm kiếm bên trong các tệp. |
   | `execute` | Chạy lệnh shell trong môi trường thực thi của backend; trả về đầu ra chuẩn, đầu ra lỗi và mã thoát. |
   | `task` | Giao một tác vụ cho subagent và nhận báo cáo kết quả. |

   Công cụ cho phép chạy lệnh là **`execute`**, ví dụ chạy `pytest tests/test_01_provided.py` để kiểm tra mã. Trong tour, công cụ này được cung cấp bởi `LocalShellBackend`.

2. Subagent `general-purpose` dùng để nghiên cứu câu hỏi phức tạp, tìm tệp và nội dung, và thực hiện tác vụ nhiều bước; nó có quyền truy cập các công cụ như tác tử chính. Mặc định, mỗi lần gọi là độc lập (stateless): subagent chỉ thấy prompt được giao, không tự kế thừa lịch sử hội thoại của tác tử chính, và trả về một báo cáo cuối cùng. Vì vậy, tác tử chính cần cung cấp đầy đủ ngữ cảnh, yêu cầu và định dạng kết quả trong lời giao việc.

3. System prompt in ra trong tour là chuỗi rỗng `''`, nhưng mô tả công cụ vẫn chứa hướng dẫn hành vi:

   - Từ `task`: “The agent's report is not shown to the user; relay a summary yourself.” — Tác tử chính phải tự tóm tắt báo cáo của subagent để gửi cho người dùng.
   - Từ `execute`: “Use read_file rather than cat/head/tail.” — Dùng công cụ `read_file` để đọc tệp thay vì các lệnh shell `cat`, `head`, `tail`.

## 4. Đường cơ sở và phân loại lỗi (Phần 2.2)

Bộ dùng cho phân tích Phần 2 là sáu lượt học chạy lại trong Docker Linux ngày 2026-10-06, cùng `openai:gpt-4o-mini`, nhiệt độ 0, giới hạn 60 bước và image `lab-deepagents`. Đã xác nhận 30/30 test môi trường/harness đạt trước khi gọi model. Mục 4 và phần phân tích Phần 2 ở mục 5 dùng các tác vụ `*-learn` còn lưu trong `results/baseline/` và `results/subagents/`.

Đã khôi phục LF cho `tasks/code-learn/workspace/tests/test_report.py`, SHA-256 khớp chuẩn `79e05f4cc2e62a4f606d210b0b08a2cc21777245bc2f6ad244a126e9a2aee00d`. Thay đổi chỉ là byte xuống dòng, không sửa nội dung test hoặc checker. `.gitattributes` giữ LF cho các tệp test tác vụ khi checkout sau này. Trong hai lượt `code-learn` Linux, `tests_not_modified` đều đạt; lỗi shell Windows không còn xuất hiện.

Mỗi check baseline thất bại dưới đây có một nhóm chính. Phân loại dựa trên đầu ra thực tế; tên `rule_*` không tự động được gán E nếu checker chưa đọc được tệp đầu ra để đánh giá quy ước.

| Tác vụ | Check thất bại | Nhóm lỗi (A-G) | Bằng chứng từ detail hoặc trace |
|---|---|---|---|
| code-learn | `csv_quoting_follows_docstring` | C — sửa theo triệu chứng test | `to_csv_row returned 'Desk, large "oak",10.00,2'`. Tác tử bỏ hoàn toàn nháy bao tên để vượt test nhìn thấy, nhưng không đáp ứng yêu cầu quote/escape của docstring. |
| code-learn | `rule_type_hints` | E | `RULE: every public function ... has type annotations on all parameters and on the return value.` |
| code-learn | `rule_regression_tests` | E | `RULE: add tests/test_regressions.py ... (at least 3); the file must pass.` |
| code-learn | `rule_changelog` | E | `RULE: record each fix in CHANGELOG.md under the heading '## Unreleased' ...` |
| data-learn | `north_q1_revenue` | G — phụ thuộc không có và đầu ra placeholder | `wrong value (got 0)`. Sau lỗi cú pháp lệnh Python và `ModuleNotFoundError: No module named 'pandas'`, tác tử ghi giá trị 0. |
| data-learn | `north_q1_orders` | G — phụ thuộc không có và đầu ra placeholder | `wrong value (got 0)`; không có phép tính thành công trước khi ghi JSON. |
| data-learn | `missing_amount_orders` | G — phụ thuộc không có và đầu ra placeholder | `wrong value (got 0)`; câu trả lời cuối thừa nhận chỉ tạo placeholder vì thiếu pandas. |
| data-learn | `duplicate_rows_removed` | G — phụ thuộc không có và đầu ra placeholder | `wrong value (got 0)`; chưa có kết quả khử trùng được thực thi thành công. |
| data-learn | `rule_money_in_cents` | E | `RULE: money values in answer.json are integer cents ...` |
| data-learn | `rule_meta_block` | E | `RULE: answer.json has an object meta` gồm `source`, `rows_in`, `rows_used`. |
| data-learn | `rule_clean_csv` | E | `RULE: write workspace/clean.csv with the header order_id,timestamp_utc,region,amount_cents ...` |
| logs-learn | `valid_structure` | G — không tạo đầu ra | `FileNotFoundError ... workspace/errors.json`; trace chỉ có hai lệnh đọc log và `final_message` rỗng. |
| logs-learn | `entry_count` | G — không tạo đầu ra | `FileNotFoundError ... workspace/errors.json`. |
| logs-learn | `timestamps_utc` | G — không tạo đầu ra | `FileNotFoundError ... workspace/errors.json`; chưa có nội dung để đánh giá chuyển múi giờ. |
| logs-learn | `exception_fields` | G — không tạo đầu ra | `FileNotFoundError ... workspace/errors.json`; chưa có nội dung để đánh giá traceback. |
| logs-learn | `repeat_counts` | G — không tạo đầu ra | `FileNotFoundError ... workspace/errors.json`. |
| logs-learn | `counts_by_service` | G — không tạo đầu ra | `FileNotFoundError ... workspace/errors.json`. |
| logs-learn | `rule_service_names` | G — không tạo đầu ra | `FileNotFoundError ... workspace/errors.json`, chưa phải bằng chứng riêng về chuẩn hóa tên service. |
| logs-learn | `rule_sorted_errors` | G — không tạo đầu ra | `FileNotFoundError ... workspace/errors.json`, chưa có danh sách để kiểm tra thứ tự. |
| logs-learn | `rule_schema_header` | G — không tạo đầu ra | `FileNotFoundError ... workspace/errors.json`, chưa có tệp để kiểm tra header. |

Nguồn: [baseline/code-learn](../results/baseline/code-learn/run.json), [baseline/data-learn](../results/baseline/data-learn/run.json), [baseline/logs-learn](../results/baseline/logs-learn/run.json) và `trace.md` cùng thư mục.

| Tác vụ baseline | Kỹ thuật đạt/tổng | Quy ước đạt/tổng | Tổng điểm |
|---|---:|---:|---:|
| code-learn | 6/7 | 0/3 | 6/10 |
| data-learn | 1/5 | 0/3 | 1/8 |
| logs-learn | 0/6 | 0/3 | 0/9 |
| Tổng check | **7/18** | **0/9** | **7/27** |

Có 20 check thất bại: G = 13 (65%), E = 6 (30%), C = 1 (5%). G chiếm đa số. Số check không đồng nghĩa số nguyên nhân độc lập: riêng việc thiếu `errors.json` làm cả 9 check log cùng thất bại. Skill có thể hướng dẫn kiểm tra dependency, dùng thư viện chuẩn nếu thư viện ngoài không có, xác nhận tệp đầu ra tồn tại và xử lý log bằng script thay vì sinh JSON dài trực tiếp. Hiệu quả của skill được đối chiếu ở mục 8.

`pandas` không nằm trong dependency của đề. Python và shell đã hoạt động; việc tác tử chọn pandas rồi không chuyển sang `csv`/`datetime` là hạn chế chiến lược xử lý, khác với lỗi không có Python ở Windows. Giữ nguyên dependency cho cả hai điều kiện trong lần chạy lại này để không thay đổi môi trường giữa chừng.

`code-learn` đã chạy lại visible test và đạt `6 passed`, nên có bằng chứng phủ định lỗi B trên bước kiểm chứng visible test. Tuy nhiên, điều đó không bao phủ mọi docstring. `top_region` của data-learn đạt từ giá trị placeholder `North`, không chứng minh quy trình phân tích đúng. Vì vậy, 7/18 check kỹ thuật đạt chưa ủng hộ kỳ vọng rằng các lỗi kỹ thuật đều hiếm. Không gán F chỉ vì điểm thấp: tệp JSON placeholder có thật và tác tử thừa nhận hạn chế.

Baseline `logs-learn` dùng 16.422 token output nhưng không tạo tệp và không có câu trả lời cuối; không có metadata kết thúc của lượt này để xác định chắc chắn nguyên nhân. `error=null` không đồng nghĩa hoàn thành tác vụ. Không sửa điểm, không tự tạo đáp án thay cho tác tử và không chạy thêm để chọn kết quả đẹp.

## 5. Điều kiện `subagents` (Phần 2.3)

Ba subagent được định nghĩa trong `src/lab/subagents.py`:

| Tên | Vai trò và thời điểm nên gọi | Lý do thiết kế |
|---|---|---|
| `explorer` | Đọc đặc tả, README, docstring và dữ liệu trước khi sửa; không chỉnh sửa tệp. | Làm rõ yêu cầu và cung cấp bằng chứng trước khi thực hiện. |
| `implementer` | Thực hiện thay đổi hoặc xử lý dữ liệu nhiều bước, chạy test/script và báo cáo. | Tập trung thực hiện nhiệm vụ được giao đầy đủ ngữ cảnh. |
| `reviewer` | Kiểm tra độc lập kết quả theo đề và trường hợp biên; không chỉnh sửa tệp. | Đối chiếu lời báo cáo với tệp và kết quả kiểm chứng thực tế. |

| Tác vụ | `subagent_calls` trong record | Bằng chứng và diễn giải |
|---|---:|---|
| code-learn | 0 | Trace không có `task`: tác tử chính tự sửa mã và chạy lại test đến `6 passed`. Có thể nó coi công việc đủ nhỏ để tự làm, nhưng trace không ghi rõ lý do nội tại. |
| data-learn | 0* | `GraphRecursionError` ở giới hạn 60 bước khiến runner không nhận được messages; vì thế số 0 trong record không đủ để khẳng định tác tử không giao việc. |
| logs-learn | 0 | Trace có 2 lần `read_file`, 1 lần `write_file` và câu trả lời cuối; không có `task`. Có thể tác tử chọn tự dựng JSON từ log đã đọc, nhưng không thể xác định chắc chắn lý do không giao việc. |

Không gọi subagent là kết quả hợp lệ dù `SUBAGENTS_NOTE` khuyến khích giao. Các trace tác vụ học còn lưu không cho thấy lời giao hay báo cáo subagent, nên không thể đánh giá chất lượng lời giao; riêng lượt `subagents/data-learn` có trace rỗng nên không thể kết luận về việc giao việc.

**Không quan sát được quá trình phối hợp đa tác tử trong các trace tác vụ học còn lưu.** Điều kiện này bổ sung lựa chọn công cụ và lời khuyến khích vào prompt, nhưng không có bằng chứng tác tử con đã làm việc. Vì vậy không thể diễn giải điểm thấp hơn như bằng chứng rằng một tác tử con làm việc yếu hơn tác tử chính.

| Tác vụ | Điểm baseline → subagents | Token baseline | Token subagents | Chênh lệch | Tỷ lệ subagents/baseline | Giây baseline → subagents |
|---|---|---:|---:|---:|---:|---|
| code-learn | 6/10 → 4/10 | 47.495 | 33.979 | -13.516 | 0,72× | 29,7 → 19,5 |
| data-learn | 1/8 → 0/8* | 25.633 | 396.776 | +371.143 | 15,48× | 19,4 → 124,2 |
| logs-learn | 0/9 → 1/9 | 29.140 | 20.142 | -8.998 | 0,69× | 251,0 → 12,3 |
| Tổng | 7/27 → 5/27 check | 102.268 | 450.897 | +348.629 | 4,41× | 300,1 → 156,0 |

*Lượt `subagents/data-learn` bị giới hạn bước; vẫn chấm trên trạng thái workspace hiện có và vẫn tính toàn bộ token đã sử dụng. Không loại lượt này khỏi trung bình để làm kết quả tốt hơn. `trace.md` rỗng theo hạn chế runner, nên không thể xác định chính xác các lệnh đã yêu cầu hoặc số lần giao việc thực tế.*

Token trung bình: baseline 34.089,33 và subagents 150.299; script dùng chia nguyên nên in baseline 34.089. Điểm trung bình theo tác vụ: baseline 0,2417 và subagents 0,1704. Tỷ lệ tổng check 7/27 và 5/27 là cách tổng hợp khác vì số check mỗi tác vụ khác nhau.

**Diễn giải chênh lệch:** `code-learn` ở cả hai điều kiện đều vượt visible tests và giữ nguyên test nguồn. Nhưng subagents còn sai giá âm `(12.00)`, `low_stock` và escape CSV; baseline chỉ còn sai CSV trong nhóm kỹ thuật. Visible tests không bao phủ hết docstring. Với `data-learn`, phần tăng token tập trung ở lượt kéo dài đến giới hạn bước; trace rỗng nên chưa xác định được đóng góp của từng loại công cụ hay giao việc. Với `logs-learn`, cấu hình subagents tạo được JSON hợp lệ nhưng nhiều nội dung sai; baseline không tạo được tệp. Do đó, xu hướng không đồng nhất giữa ba tác vụ.

| Điều kiện | Kỹ thuật đạt/tổng | Quy ước đạt/tổng | Số lượt đọc skill |
|---|---:|---:|---:|
| baseline | 7/18 | 0/9 | 0/3 |
| subagents | 5/18 | 0/9 | 0/3 |

Mỗi điều kiện chỉ có một lượt cho mỗi tác vụ; chưa có lặp để ước lượng nhiễu, và vẫn có một lượt giới hạn bước. Không thể khái quát thành kết luận đa tác tử luôn yếu hơn hoặc luôn tốn hơn.

Đã đủ ba tác vụ học ở mỗi điều kiện. Nguồn: [subagents/code-learn](../results/subagents/code-learn/run.json), [subagents/data-learn](../results/subagents/data-learn/run.json), [subagents/logs-learn](../results/subagents/logs-learn/run.json) và các trace cùng thư mục. Các tác vụ đánh giá và phép so sánh cuối được trình bày ở mục 7–8.

## 6. Self-evolving: skill do curator sinh (Phần 3)

- `curate_skills` đọc duy nhất các `run.json` có `role=learn` ở `baseline`, ghép tên và `detail` của check thất bại với tối đa 6.000 ký tự cuối của trace, gọi mô hình một lần, rồi chỉ ghi khối qua `validate_skill`. Test ngoại tuyến trên Docker Linux: 32/32 test đạt, gồm `test_04_curator.py`.
- Đã chạy curator 3 lần (ban đầu và tối đa 2 lần chạy lại). Lần 1 sinh 3 skill nhưng loại cả 3: `data-cleaning` tự đề xuất lọc số âm và điền giá trị thiếu khi đặc tả không yêu cầu; `error-handling` đề xuất cài package trong sandbox thay vì dùng thư viện chuẩn; `testing-and-validation` quá chung, không chuyển feedback thành bước kiểm chứng cụ thể. Sau đó prompt được siết theo feedback của checker.
- Lần 2 sinh 3 skill. Loại `changelog-updates` vì ép ít nhất 3 bullet trong mọi tình huống là chi tiết riêng của tác vụ học. Hai skill `output-verification` và `type-annotations` có quy tắc kiểm chứng tổng quát và đúng. Trước lần chạy lại cuối, các tệp được bỏ khỏi thư mục; sau khi đánh giá lượt cuối, hai tệp này được khôi phục **nguyên văn từ đầu ra lần 2**, không sửa nội dung skill.
- Lần 3 sinh 2 skill, đều bị loại: `code-quality-checks` nêu tên hàm của tác vụ học và đưa ra chỉ dẫn quote CSV sai; `log-processing` cố định chỉ nhận `ERROR/CRITICAL`, dễ bỏ sót mức lỗi của tác vụ mới. Không chạy curator lần thứ tư để tuân thủ giới hạn trong guide. Bộ cuối cùng gồm 2 skill của lần 2; không có skill nào từ lượt 3.

| Skill | Tổng quát hay riêng cho tác vụ học? | Đúng hay sai (nêu chỗ sai nếu có) | Độ dài, `description` và `skills_read` ở Phần 3.4 |
|---|---|---|---|
| `output-verification` | Tổng quát cho tệp đầu ra có schema | Đúng với feedback thiếu `errors.json` và schema; yêu cầu đối chiếu schema theo đặc tả | 11 dòng (7 dòng thân); `description` nói rõ tình huống kiểm tra đầu ra; `skills_read=0` ở cả 3 lượt thử |
| `type-annotations` | Tổng quát cho mã Python có public API | Đúng với check `rule_type_hints`; chưa bao phủ CSV, regression test hay dữ liệu | 10 dòng (6 dòng thân); `description` kích hoạt khi cần kiểm tra type hints; `skills_read=0` ở cả 3 lượt thử |

Lượt thử Phần 3.4 (đã lưu ở `results/skills-auto-dev/`): `code-learn` 5/10, 65.236 token; `data-learn` 2/8, 53.991 token; `logs-learn` 0/9, 30.699 token. Cả ba có `skills_modified=false`, `error=null`, và `skills_read=0`, nên không quy thay đổi điểm cho việc đọc skill. Số check học đạt là 7/27, trùng tổng baseline 7/27 nhưng phân bố theo tác vụ khác.

## 7. Kết quả so sánh (Phần 4.3, 4.4)

Bảng dưới được sinh bằng `lab.compare` từ 18 bản ghi hiện tại và trùng với [table.md](table.md). Không dùng các điểm của lượt đã bị ghi đè để thay vào bảng. Một tác vụ chỉ thành công hoàn toàn khi đạt mọi check; hiện không có lượt nào đạt mức đó. Điểm trung bình được làm tròn hai chữ số; token trung bình dùng phép chia nguyên của script. Mục 8 dùng thêm số chưa làm tròn khi tính chênh lệch.

| Task | baseline | subagents | skills-auto |
|---|---|---|---|
| code-learn | 6/10 | 4/10 | 3/10 |
| data-learn | 1/8 | 0/8 | 0/8 |
| logs-learn | 0/9 | 1/9 | 0/9 |
| code-eval | 1/11 | 1/11 | 3/11 |
| data-eval | 0/9 | 0/9 | 0/9 |
| logs-eval | 1/10 | 1/10 | 0/10 |
| **Mean score - learning tasks** | 0.24 | 0.17 | 0.10 |
| **Mean score - evaluation tasks** | 0.06 | 0.06 | 0.09 |
| **Mean tokens per run** | 134,649 | 189,416 | 69,509 |
| **Runs that read a skill** | 0/6 | 0/6 | 0/6 |

Đầu ra của `python scripts/check_breakdown.py`:

```text
condition     role    technical  house rules  mean tokens  read a skill
baseline      eval      2/18         0/12         235,209      0/3
baseline      learn     7/18         0/9           34,089      0/3
subagents     eval      2/18         0/12         228,533      0/3
subagents     learn     5/18         0/9          150,299      0/3
skills-auto   eval      3/18         0/12          78,233      0/3
skills-auto   learn     3/18         0/9           60,785      0/3
```

Có 6/18 lượt có `error`, đều là `GraphRecursionError` với giới hạn 60 bước:

| Điều kiện / tác vụ | Điểm | Token | Lỗi |
|---|---:|---:|---|
| [baseline/code-eval](../results/baseline/code-eval/run.json) | 1/11 | 272.575 | Giới hạn 60 bước |
| [baseline/data-eval](../results/baseline/data-eval/run.json) | 0/9 | 415.245 | Giới hạn 60 bước |
| [skills-auto/logs-eval](../results/skills-auto/logs-eval/run.json) | 0/10 | 187.706 | Giới hạn 60 bước |
| [subagents/code-eval](../results/subagents/code-eval/run.json) | 1/11 | 246.085 | Giới hạn 60 bước |
| [subagents/data-eval](../results/subagents/data-eval/run.json) | 0/9 | 421.255 | Giới hạn 60 bước |
| [subagents/data-learn](../results/subagents/data-learn/run.json) | 0/8 | 396.776 | Giới hạn 60 bước |

Runner vẫn chấm workspace khi lỗi, nên điểm và token của các lượt này được giữ trong trung bình. Các trace của lượt lỗi rỗng vì `invoke` không trả messages; số tool call, subagent call và skill đã đọc bằng 0 ở những lượt đó không đủ để suy ra chúng chưa được gọi. Đã có các lần chạy lại trong quá trình thực hiện; các thư mục chuẩn hiện chỉ giữ lượt cuối. Vì không còn đầy đủ bản ghi các lần bị ghi đè, không coi đây là thí nghiệm lặp có thể ước lượng phân phối điểm hoặc tổng chi phí lịch sử.

Ngoài lỗi ghi trong `error`, [trace skills-auto/data-learn](../results/skills-auto/data-learn/trace.md) có lỗi shell `'python' is not recognized`, và [trace skills-auto/data-eval](../results/skills-auto/data-eval/trace.md) thừa nhận ghi placeholder. Đây là lỗi thực thi môi trường dù `run.json` có thể ghi `error=null`; không dùng chúng làm bằng chứng riêng về năng lực suy luận hay chất lượng skill.

Tất cả 18 bản ghi có `skills_modified=false`. Trên môi trường Windows tạo sáu lượt `skills-auto` hiện tại, lệnh `python -X utf8 scripts/verify_freeze.py` trả:

```text
checked 6 runs of skill conditions: OK
```

Tùy chọn `-X utf8` khắc phục lỗi đọc báo cáo tiếng Việt từ Git bằng bảng mã `cp1252`. Kết quả OK xác nhận quy trình tag, giả thuyết, thời điểm chạy và hash skill; nó không kiểm tra chất lượng đáp án hoặc tính đồng nhất của môi trường thí nghiệm.

## 8. Phân tích

### 8.1. Điểm học, điểm đánh giá và giả thuyết

Trên tập học, `baseline` đạt trung bình 0,2417, cao hơn `subagents` 0,1704 và `skills-auto` 0,1000. So với baseline, chênh lệch lần lượt là −7,13 và −14,17 điểm phần trăm. Không điều kiện nào cải thiện điểm học trong bộ kết quả cuối.

Trên tập đánh giá, `baseline` và `subagents` cùng đạt 0,0636; `skills-auto` đạt 0,0909, cao hơn 2,73 điểm phần trăm. Theo tổng check, ba điều kiện đạt lần lượt 2/30, 2/30 và 3/30. Skill có thêm hai check kỹ thuật ở `code-eval`, nhưng mất check cấu trúc của `logs-eval` do lượt đó lỗi; tổng chỉ chênh một check. Không có trường hợp tăng điểm học nhưng không tăng điểm đánh giá trong bảng cuối, nên không quan sát được mẫu quá khớp theo tiêu chí này.

H1 phù hợp với số liệu ở trường hợp bằng nhau: subagents không vượt baseline trên eval. H2 không phù hợp với thứ tự điểm quan sát vì skills-auto cao hơn baseline; tuy nhiên chưa thể kết luận skill gây ra cải thiện do không ghi nhận đọc skill và môi trường khác nhau. H3 phù hợp về mặt mô tả: điểm eval thấp hơn điểm học ở cả ba điều kiện (0,0636 < 0,2417; 0,0636 < 0,1704; 0,0909 < 0,1000). Các kết quả này chưa phải kiểm định thống kê hay bằng chứng về quan hệ nhân quả.

### 8.2. Check kỹ thuật và quy ước

Trên tập học, số check kỹ thuật đạt là 7/18, 5/18 và 3/18; trên tập đánh giá là 2/18, 2/18 và 3/18, lần lượt theo baseline, subagents, skills-auto. Mọi điều kiện đều đạt 0/9 check quy ước học và 0/12 check quy ước đánh giá. Bộ skill hiện tại chưa tạo ra lợi ích quan sát được ở nhóm quy ước.

Ba check quy ước mới ở eval là `rule_version_bump`, `rule_sorted_keys_format` và `rule_source_line`; cả ba đều thất bại ở mọi điều kiện. Hai skill giữ lại chỉ hướng dẫn type annotations và kiểm tra đầu ra theo schema đã biết, không cung cấp ba quy ước mới này. Ngoài việc không ghi nhận đọc skill, một chỉ dẫn chung như kiểm tra schema cũng không tự cung cấp một quy ước tổ chức chưa được học.

### 8.3. Bằng chứng về việc dùng skill và tool

Không có ví dụ nào đủ bằng chứng để khẳng định một check đạt *nhờ* skill: cả sáu bản ghi skills-auto có `skills_read=0`, và năm trace không bị lỗi đều không có lần mở `skills/.../SKILL.md`. Với lượt `logs-eval` bị lỗi, trace rỗng nên chỉ có thể nói không đo được việc đọc, thay vì khẳng định chắc chắn không đọc.

Ví dụ về check cải thiện nhưng chưa thể quy cho skill: `billable_blocks_round_up` ở `skills-auto/code-eval` đạt, còn baseline không đạt. [Trace code-eval](../results/skills-auto/code-eval/trace.md) cho thấy agent đọc docstring rồi sửa phép làm tròn thành `(minutes + block - 1) // block`; nó không mở skill. Cùng lượt đó, `rule_type_hints` vẫn thất bại dù `type-annotations` chứa đúng hướng dẫn liên quan: skill được cung cấp nhưng không có bằng chứng đã được đọc hoặc áp dụng.

Ví dụ về đầu ra thiếu: `skills-auto/data-learn` đạt 0/8 vì không có `answer.json`; trace có nhiều lần thử `python`, `python3`, `pip` rồi báo không tìm thấy lệnh. Skill `output-verification` cũng không được mở. Do đó không thể chỉ đổ lỗi cho việc thiếu skill: shell Windows không phù hợp với PATH Unix của backend đã ngăn việc tính toán và kiểm thử. `skills-auto/code-eval` vẫn sửa được tệp bằng tool nhưng chạy `pytest` và `python` đều lỗi, giải thích vì sao có vài check kỹ thuật đạt mà visible suite vẫn không đạt.

Trong bộ kết quả cuối của điều kiện subagents, cả sáu record ghi `subagent_calls=0`. Ba lượt lỗi có trace rỗng, còn ba trace còn lại không có lời giao việc. Vì vậy chưa quan sát được lợi ích của một quá trình phối hợp tác tử con thực sự; không dùng số liệu này để kết luận mọi hệ đa tác tử đều kém hiệu quả.

### 8.4. Chi phí và điểm trên mỗi token

Định nghĩa hiệu quả sử dụng token trong báo cáo là `1.000.000 × tổng điểm chuẩn hóa của các tác vụ / tổng tokens.total`. Điểm chuẩn hóa của mỗi tác vụ nằm trong [0, 1]. Chỉ số dùng toàn bộ token của các lượt đang ở bảng, kể cả lượt lỗi; không bao gồm các lần đã bị ghi đè hoặc curator.

| Điều kiện | Tổng token (6 tác vụ) | Điểm TB (6 tác vụ) | Điểm / triệu token (6 tác vụ) | Điểm / triệu token (eval) |
|---|---:|---:|---:|---:|
| baseline | 807.897 | 0,1527 | 1,1337 | 0,2706 |
| subagents | 1.136.496 | 0,1170 | 0,6177 | 0,2785 |
| skills-auto | 417.055 | 0,0955 | 1,3733 | 1,1620 |

Trên sáu tác vụ, skills-auto có chỉ số điểm/token cao nhất (1,3733), rồi baseline (1,1337) và subagents (0,6177). Đây là thứ hạng mô tả với điểm tuyệt đối rất thấp, không phải bằng chứng đọc skill giúp tiết kiệm token: skills-auto có thể dừng sớm hoặc tạo placeholder do lỗi môi trường. Không chuyển token thành tiền vì giá, cache và hóa đơn nhà cung cấp không được lưu.

Subagents dùng tổng 1.136.496 token so với 807.897 của baseline, tăng khoảng 40,67%, nhưng điểm trung bình cả sáu tác vụ thấp hơn (0,1170 so với 0,1527). Riêng eval, hai điều kiện cùng điểm và subagents dùng ít hơn khoảng 2,84% token. Vì vậy bộ kết quả này chưa cho thấy lợi ích chất lượng đủ để đánh đổi chi phí tổng thể của cấu hình subagents; cũng chưa thể quy chi phí tăng cho tác tử con vì lượt lỗi không có trace đầy đủ.

### 8.5. Rò rỉ dữ liệu và quá khớp

Curator chỉ đưa các lượt `role=learn` vào prompt; `validate_skill` chặn marker của tập đánh giá trước khi ghi tệp. Hai skill cuối không chứa tên riêng hay đáp án eval, và Git xác nhận chúng không đổi từ tag freeze. Ba giả thuyết ở mục 2 được giữ nguyên văn so với commit `hypotheses`, không sửa theo điểm mới.

Lượt curator cuối từng sinh skill gắn với tên hàm cụ thể và mức log riêng của tác vụ học; chúng đã bị loại. Điều này cho thấy nguy cơ quá khớp trong bước sinh skill, nhưng không chứng minh quá khớp của hai skill cuối qua điểm số. Trong quá trình chọn skill, mô tả `logs-eval` đã được xem trước freeze để nhận ra quy tắc mức log quá hẹp; do đó khâu tuyển chọn không hoàn toàn độc lập với mô tả tập đánh giá, dù không dùng điểm hoặc checker eval trong prompt curator. Đây là một hạn chế cần công khai, và kiểm tra marker tự động không đủ loại trừ mọi dạng rò rỉ.

### 8.6. So sánh Phần 3.4 và sau đóng băng

| Tác vụ | Phần 3.4 | Sau freeze | Chênh lệch điểm phần trăm | Token trước → sau |
|---|---:|---:|---:|---|
| code-learn | 5/10 | 3/10 | -20,00 | 65.236 → 65.515 |
| data-learn | 2/8 | 0/8 | -25,00 | 53.991 → 86.142 |
| logs-learn | 0/9 | 0/9 | +0,00 | 30.699 → 30.699 |

Điểm học trung bình giảm từ 0,2500 xuống 0,1000, tức 15,00 điểm phần trăm; tổng check giảm từ 7/27 xuống 3/27. Các lượt trước đóng băng chạy Linux, còn các lượt sau đóng băng hiện lưu chạy Windows. Vì vậy đây là biến động do cả môi trường và lời gọi mô hình, không phải ước lượng nhiễu thuần trên cùng cấu hình. Chênh lệch 2,73 điểm phần trăm trên eval ở mục 8.1 cần được đọc thận trọng trong bối cảnh này.

Cùng nội dung skill nhưng hash trong dev là `1283e140…` còn hash Windows là `5a2b2eb4…`: hàm băm có sẵn dùng chuỗi đường dẫn tương đối nên dấu `/` và `\` khác nhau giữa hệ điều hành. Khi băm nội dung hiện tại với đường dẫn POSIX, kết quả khớp đầy đủ hash dev; Git cũng không có thay đổi skill so với freeze. Khác biệt digest này không phải bằng chứng nội dung skill đã được sửa.

## 9. Hạn chế và tính hợp lệ

1. **Môi trường không đồng nhất.** Baseline/subagents chạy Linux, còn sáu lượt skills-auto hiện lưu chạy Windows và có lỗi không tìm thấy Python/pytest. Điểm chịu ảnh hưởng của khả năng thực thi, nên chưa tách được tác dụng của skill hay cấu hình subagent.
2. **Mẫu nhỏ và không có bộ lặp đầy đủ.** Mỗi điều kiện chỉ giữ một bản ghi cho mỗi tác vụ. Những lượt cũ bị ghi đè không cho phép ước lượng độ lệch chuẩn hoặc khoảng tin cậy; không chọn lại kết quả cũ tốt hơn để đưa vào bảng. Một lỗi thiếu tệp có thể làm nhiều check cùng thất bại, nên các check không độc lập.
3. **Giới hạn bước và mất trace.** Sáu lượt có GraphRecursionError vẫn được chấm và tính token, nhưng không còn messages để giải thích chuỗi hành động. `error=null` cũng không loại trừ lỗi tool được trả như văn bản. Cả hai làm yếu khả năng quy nguyên nhân từ điểm số.
4. **Skill chưa được sử dụng theo quan sát.** Không ghi nhận lượt đọc skill; chưa thể đánh giá tác dụng của việc làm theo skill. Skill hợp lệ về định dạng cũng chưa chắc có trigger đủ rõ hoặc nội dung hữu ích cho mọi họ tác vụ.
5. **Giới hạn phạm vi và tuyển chọn.** Chỉ dùng một cấu hình mô hình, ba họ tác vụ và các quy ước tổ chức được thiết kế sẵn. Việc xem mô tả logs-eval khi chọn skill làm giảm tính độc lập giữa phát triển và đánh giá. Kết luận không tự suy rộng sang mô hình, dữ liệu hay tổ chức khác.
6. **Metadata chưa đủ để tái lập từng lượt chính xác.** Runner không lưu model, phiên bản dependency hoặc hệ điều hành trong từng run.json; báo cáo phải dựa thêm vào cấu hình, trace và xác nhận của người chạy. Tổng token hiện có không bao phủ mọi lần chạy lịch sử.

## 10. Kết luận

Bộ kết quả hiện có đủ 18 lượt và qua kiểm tra freeze, nhưng chưa có tác vụ nào đạt toàn bộ check. Trên tập đánh giá, baseline và subagents cùng đạt trung bình 0,0636, còn skills-auto đạt 0,0909; toàn bộ check quy ước đều thất bại. Không có bằng chứng đủ mạnh về lợi ích của skill hoặc phối hợp đa tác tử vì không ghi nhận đọc skill, nhiều lượt bị giới hạn bước và môi trường giữa các điều kiện khác nhau. Điểm/token của skills-auto cao nhất trong bộ lưu hiện tại nhưng chưa chứng minh hiệu quả cải thiện nhờ skill. Bước tiếp theo nên là một thí nghiệm riêng dùng cùng môi trường Linux đã kiểm tra Python/pytest cho cả ba điều kiện, lưu đầy đủ metadata và lặp mỗi cấu hình để đo nhiễu.

## Phụ lục

Thứ tự quy trình: kiểm tra môi trường → chạy ba tác vụ học ở baseline/subagents → curator và đánh giá skill (ba lần gọi) → chạy thử skills-auto trên học → sao lưu thành `results/skills-auto-dev/` → commit hypotheses → commit/tag freeze → chạy eval và chạy lại skills-auto → so sánh và xác minh. Các lượt eval baseline/subagents đã được chạy lại sau lượt skills-auto; bảng dùng bản ghi mới nhất ở mỗi thư mục, không giả định thời điểm của chúng giống lần chạy đầu.

Các lệnh chính (tại gốc repo):

```bash
python -m pytest tests/test_01_provided.py tests/test_02_agent.py tests/test_03_runner.py tests/test_04_curator.py
python -m lab.runner --condition baseline --tasks learn
python -m lab.runner --condition subagents --tasks learn
python -m lab.curator
python -m lab.runner --condition skills-auto --tasks learn
# Sao lưu kết quả thử vào results/skills-auto-dev trước lượt chính thức.
git add -A
git commit -m hypotheses
git commit --allow-empty -m "freeze skills"
git tag freeze
python -m lab.runner --condition baseline --tasks eval
python -m lab.runner --condition subagents --tasks eval
python -m lab.runner --condition skills-auto --tasks all
python -m lab.compare > report/table.md
python scripts/check_breakdown.py
python -X utf8 scripts/verify_freeze.py
```

Các lệnh tạo commit/tag chỉ ghi lại lịch sử đã thực hiện, không chạy lại nếu tag đã tồn tại. Môi trường của từng giai đoạn được nêu ở mục 1; README yêu cầu Linux/WSL/Docker. Để chạy runner trong Docker từ PowerShell, tiền tố được dùng là `docker run --rm --env-file .env -v "${PWD}:/lab" lab-deepagents`, theo sau bằng lệnh Python tương ứng. Bộ hiện tại vẫn giữ các lượt Windows để phản ánh đúng dữ liệu đã đo và công khai sai lệch môi trường.

Mốc thời gian trong báo cáo dùng UTC+7; trường `timestamp` gốc trong run.json là UTC. Các kết quả chính nằm ở `results/baseline/`, `results/subagents/`, `results/skills-auto/`; dữ liệu trước đóng băng ở `results/skills-auto-dev/`. Không có đủ tệp kết quả trong archive hiện tại để tái dựng mọi lần chạy cũ. Giải thích code nằm trong comment của bốn module; các TODO được giữ để đối chiếu với guide. Không sửa skill sau freeze, không tự sửa đầu ra của agent để tăng điểm, và không đưa API key vào báo cáo. Thử thách mở rộng Phần 6 chưa thực hiện.
