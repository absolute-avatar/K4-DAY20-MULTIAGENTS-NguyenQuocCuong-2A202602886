# Báo cáo Lab: Self evolving Agentic

## 1. Thông tin nhóm và cấu hình

| Họ tên | Mã sinh viên | Phần đóng góp |
|---|---|---|
| Nguyễn Quốc Cường | 2A202602886 | Cài đặt harness, chạy thí nghiệm, phân tích và viết báo cáo |

- Cấu hình sáu lượt Linux Phần 2: `LAB_MODEL=openai:gpt-4o-mini`, `LAB_TEMPERATURE=0`, `recursion_limit=60`.
- Môi trường bộ kết quả chính: Docker Linux, Python 3.12.15, Deep Agents 0.7.21. Test môi trường/harness trước Phần 2 đạt 30/30; sau khi cài curator đạt 32/32.
- Chín lượt có `run.json` và `trace.md` hiện còn trong kho dùng 703.091 token: sáu lượt `baseline`/`subagents` dùng 553.165, ba lượt thử `skills-auto-dev` dùng 149.926. Ngân sách tối đa chưa được khai báo.
- Commit của tag `freeze`: điền sau khi tạo tag ở Phần 4.1.

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

Bộ chính thức cho phân tích Phần 2 là sáu lượt chạy lại trong Docker Linux ngày 2026-10-06, cùng `openai:gpt-4o-mini`, nhiệt độ 0, giới hạn 60 bước và image `lab-deepagents`. Đã xác nhận 30/30 test môi trường/harness đạt trước khi gọi model. Báo cáo hiện chỉ dùng sáu lượt Linux còn lưu ở `results/baseline/` và `results/subagents/`.

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

Có 20 check thất bại: G = 13 (65%), E = 6 (30%), C = 1 (5%). G chiếm đa số. Số check không đồng nghĩa số nguyên nhân độc lập: riêng việc thiếu `errors.json` làm cả 9 check log cùng thất bại. Skill có thể hướng dẫn kiểm tra dependency, dùng thư viện chuẩn nếu thư viện ngoài không có, xác nhận tệp đầu ra tồn tại và xử lý log bằng script thay vì sinh JSON dài trực tiếp. Hiệu quả của skill vẫn cần được đo ở các phần sau.

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

Không gọi subagent là kết quả hợp lệ dù `SUBAGENTS_NOTE` khuyến khích giao. Các trace còn lưu không cho thấy lời giao hay báo cáo subagent, nên không thể đánh giá chất lượng lời giao; riêng lượt `subagents/data-learn` có trace rỗng nên không thể kết luận về việc giao việc.

**Không quan sát được quá trình phối hợp đa tác tử trong các trace còn lưu.** Điều kiện này bổ sung lựa chọn công cụ và lời khuyến khích vào prompt, nhưng không có bằng chứng tác tử con đã làm việc. Vì vậy không thể diễn giải điểm thấp hơn như bằng chứng rằng một tác tử con làm việc yếu hơn tác tử chính.

| Tác vụ | Điểm baseline → subagents | Token baseline | Token subagents | Chênh lệch | Tỷ lệ subagents/baseline | Giây baseline → subagents |
|---|---|---:|---:|---:|---:|---|
| code-learn | 6/10 → 4/10 | 47.495 | 33.979 | -13.516 | 0,72× | 29,7 → 19,5 |
| data-learn | 1/8 → 0/8* | 25.633 | 396.776 | +371.143 | 15,48× | 19,4 → 124,2 |
| logs-learn | 0/9 → 1/9 | 29.140 | 20.142 | -8.998 | 0,69× | 251,0 → 12,3 |
| Tổng | 7/27 → 5/27 check | 102.268 | 450.897 | +348.629 | 4,41× | 300,1 → 156,0 |

*Lượt `subagents/data-learn` bị giới hạn bước; vẫn chấm trên trạng thái workspace hiện có và vẫn tính toàn bộ token đã sử dụng. Không loại lượt này khỏi trung bình để làm kết quả tốt hơn. `trace.md` rỗng theo hạn chế runner, nên không thể xác định chính xác các lệnh đã yêu cầu hoặc số lần giao việc thực tế.*

Token trung bình: baseline 34.089,33 và subagents 150.299; script dùng chia nguyên nên in baseline 34.089. Điểm trung bình theo tác vụ: baseline 0,2417 và subagents 0,1704. Tỷ lệ tổng check 7/27 và 5/27 là cách tổng hợp khác vì số check mỗi tác vụ khác nhau.

**Diễn giải chênh lệch:** `code-learn` ở cả hai điều kiện đều vượt visible tests và giữ nguyên test nguồn. Nhưng subagents còn sai giá âm `(12.00)`, `low_stock` và escape CSV; baseline chỉ còn sai CSV trong nhóm kỹ thuật. Visible tests không bao phủ hết docstring. Với `data-learn`, phần tăng token đến từ chuỗi yêu cầu shell kéo dài đến giới hạn bước, không phải chi phí giao việc. Với `logs-learn`, cấu hình subagents tạo được JSON hợp lệ nhưng nhiều nội dung sai; baseline không tạo được tệp. Do đó, xu hướng không đồng nhất giữa ba tác vụ.

| Điều kiện | Kỹ thuật đạt/tổng | Quy ước đạt/tổng | Số lượt đọc skill |
|---|---:|---:|---:|
| baseline | 7/18 | 0/9 | 0/3 |
| subagents | 5/18 | 0/9 | 0/3 |

Mỗi điều kiện chỉ có một lượt cho mỗi tác vụ; chưa có lặp để ước lượng nhiễu, và vẫn có một lượt giới hạn bước. Không thể khái quát thành kết luận đa tác tử luôn yếu hơn hoặc luôn tốn hơn.

Đã đủ ba tác vụ học ở mỗi điều kiện. Nguồn: [subagents/code-learn](../results/subagents/code-learn/run.json), [subagents/data-learn](../results/subagents/data-learn/run.json), [subagents/logs-learn](../results/subagents/logs-learn/run.json) và các trace cùng thư mục. Tác vụ đánh giá chưa được chạy.

## 6. Self-evolving: skill do curator sinh (Phần 3)

- `curate_skills` đọc duy nhất các `run.json` có `role=learn` ở `baseline`, ghép tên và `detail` của check thất bại với tối đa 6.000 ký tự cuối của trace, gọi mô hình một lần, rồi chỉ ghi khối qua `validate_skill`. Test ngoại tuyến trên Docker Linux: 32/32 test đạt, gồm `test_04_curator.py`.
- Đã chạy curator 3 lần (ban đầu và tối đa 2 lần chạy lại). Lần 1 sinh 3 skill nhưng loại cả 3: `data-cleaning` tự đề xuất lọc số âm và điền giá trị thiếu khi đặc tả không yêu cầu; `error-handling` đề xuất cài package trong sandbox thay vì dùng thư viện chuẩn; `testing-and-validation` quá chung, không chuyển feedback thành bước kiểm chứng cụ thể. Sau đó prompt được siết theo feedback của checker.
- Lần 2 sinh 3 skill. Loại `changelog-updates` vì ép ít nhất 3 bullet trong mọi tình huống là chi tiết riêng của tác vụ học. Hai skill `output-verification` và `type-annotations` có quy tắc kiểm chứng tổng quát và đúng. Trước lần chạy lại cuối, các tệp được bỏ khỏi thư mục; sau khi đánh giá lượt cuối, hai tệp này được khôi phục **nguyên văn từ đầu ra lần 2**, không sửa nội dung skill.
- Lần 3 sinh 2 skill, đều bị loại: `code-quality-checks` nêu tên hàm của tác vụ học và đưa ra chỉ dẫn quote CSV sai; `log-processing` cố định chỉ nhận `ERROR/CRITICAL`, dễ bỏ sót mức lỗi của tác vụ mới. Không chạy curator lần thứ tư để tuân thủ giới hạn trong guide. Bộ cuối cùng gồm 2 skill của lần 2; không có skill nào từ lượt 3.

| Skill | Tổng quát hay riêng cho tác vụ học? | Đúng hay sai (nêu chỗ sai nếu có) | Độ dài, `description` và `skills_read` ở Phần 3.4 |
|---|---|---|---|
| `output-verification` | Tổng quát cho tệp đầu ra có schema | Đúng với feedback thiếu `errors.json` và schema; yêu cầu đọc đặc tả trước khi xác nhận | 11 dòng (7 dòng thân); `description` nói rõ tình huống kiểm tra đầu ra; `skills_read=0` ở cả 3 lượt thử |
| `type-annotations` | Tổng quát cho mã Python có public API | Đúng với check `rule_type_hints`; chưa bao phủ CSV, regression test hay dữ liệu | 10 dòng (6 dòng thân); `description` kích hoạt khi cần kiểm tra type hints; `skills_read=0` ở cả 3 lượt thử |

Lượt thử Phần 3.4 (đã lưu ở `results/skills-auto-dev/`): `code-learn` 5/10, 65.236 token; `data-learn` 2/8, 53.991 token; `logs-learn` 0/9, 30.699 token. Cả ba có `skills_modified=false`, `error=null`, và `skills_read=0`, nên không quy thay đổi điểm cho việc đọc skill. Số check học đạt là 7/27, trùng tổng baseline 7/27 nhưng phân bố theo tác vụ khác.

## 7. Kết quả so sánh (Phần 4.3, 4.4)

Chưa có bảng chính thức: chưa tạo commit `hypotheses` và tag `freeze`, nên chưa chạy ba điều kiện trên tác vụ đánh giá hoặc lượt `skills-auto` sau đóng băng. Sau khi có đủ `run.json`, chạy `python -m lab.compare > report/table.md` và `python scripts/check_breakdown.py`, rồi chèn số liệu vào mục này.

## 8. Phân tích

Chưa thể kết luận về điểm đánh giá, check quy ước mới, hiệu quả theo token hay chênh lệch giữa lượt thử skill và lượt sau đóng băng khi các lượt chính thức chưa chạy. Dữ liệu hiện có chỉ cho thấy tổng check học là 7/27 (`baseline`), 5/27 (`subagents`) và 7/27 (lượt thử `skills-auto-dev`); cả ba lượt thử skill đều có `skills_read=0`. Phần phân tích cuối phải trả lời sáu câu hỏi của `REPORT_TEMPLATE.md` sau khi có bảng mục 7.

## 9. Hạn chế và tính hợp lệ

1. Mỗi vai trò chỉ có ba tác vụ thuộc ba họ khác nhau. Một lỗi thiếu tệp ở `logs-learn` làm cả chín check thất bại, nên số check không tương ứng với chín nguyên nhân độc lập và trung bình dễ bị một tác vụ chi phối.
2. Mỗi điều kiện mới có một lượt trên từng tác vụ học. Dù đặt nhiệt độ 0, lời gọi mô hình và chuỗi công cụ vẫn có nhiễu; chênh lệch nhỏ giữa điều kiện chưa đủ chứng minh cải tiến. Lượt thử skill và lượt sau đóng băng cần được so riêng để thấy mức dao động.
3. Chỉ dùng một cấu hình mô hình và một môi trường Docker. Kết quả không tự suy rộng sang mô hình hoặc môi trường khác; ví dụ lượt `subagents/data-learn` chạm giới hạn 60 bước và dùng phần lớn token.
4. Khi `agent.invoke` ném lỗi, runner không nhận được messages nên trace và số tool call có thể rỗng dù mô hình đã dùng token. Vì vậy không thể xác định từ `run.json` rằng lượt lỗi hoàn toàn không giao subagent.
5. Các skill được nạp nhưng `skills_read=0` trong ba lượt thử. Điểm của lượt đó không đo tác dụng của việc *làm theo* skill, chỉ đo kết quả dưới cấu hình có cung cấp skill.

## 10. Kết luận

Chưa có kết luận cuối cho ba điều kiện trên tác vụ đánh giá vì quy trình đóng băng chưa hoàn tất. Sau khi có kết quả chính thức, mục này cần tổng kết bằng tối đa năm câu dựa trên bảng so sánh và nêu một cải tiến tiếp theo.

## Phụ lục

- Thứ tự lượt Linux: baseline `data-learn`, `code-learn`, `logs-learn`; subagents `code-learn`, `data-learn`, `logs-learn`.
- Lệnh preflight trong Docker: `python -m pytest tests/test_01_provided.py tests/test_02_agent.py tests/test_03_runner.py` (30 passed).
- Các kết quả hiện lưu ở `results/baseline/`, `results/subagents/` và `results/skills-auto-dev/`; mỗi thư mục tác vụ có `run.json` và `trace.md`. Không lưu API key trong báo cáo.
- Các TODO/comment mã harness giữ nguyên. Thay đổi chuẩn bị môi trường gồm khôi phục LF cho tệp test gốc và thêm `.gitattributes`; không sửa prompt chuẩn, checker, đáp án tác vụ hoặc tự cải thiện đầu ra của tác tử.
- Thử thách mở rộng: chưa thực hiện.
