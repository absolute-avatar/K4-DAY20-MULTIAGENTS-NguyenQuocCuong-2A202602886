"""GUIDE Phần 1 - Định nghĩa subagent (tác tử con).   >>> SINH VIÊN CÀI ĐẶT <<<

Pseudo-code: guides/pseudocode/02_subagents.md
Kiểm tra:    pytest tests/test_02_agent.py
"""


def get_subagents() -> list[dict]:
    """Trả về danh sách subagent (ít nhất 2, tên khác nhau).

    Mỗi phần tử là một dict có các khóa bắt buộc:
      "name":          tên duy nhất (chữ thường, có thể có dấu gạch ngang)
      "description":   khi nào tác tử chính nên giao việc cho subagent này (viết như một hướng dẫn hành động)
      "system_prompt": chỉ dẫn cho subagent
    Gợi ý vai trò: explorer (đọc và báo cáo), implementer (thực hiện), reviewer (kiểm tra độc lập).
    """
    # TODO: cài đặt get_subagents (xem guides/pseudocode/02_subagents.md)
    # Ghi chú: mỗi lần gọi trả về các dict mới để build_agent có thể cấu hình
    # prompt mà không làm thay đổi định nghĩa cho những lần chạy sau.
    # description giúp tác tử chính chọn người nhận; system_prompt hướng dẫn
    # subagent xử lý lời giao việc, vì nó không tự thấy hội thoại của tác tử chính.
    return [
        # Explorer chỉ khảo sát; tách bước đọc đặc tả khỏi bước sửa để người
        # thực hiện không phải đoán các ràng buộc còn ẩn trong README/docstring.
        {
            "name": "explorer",
            "description": (
                "Use when requirements or file contents need investigation before implementation: "
                "inspect README files, docstrings, and data samples and report findings."
            ),
            "system_prompt": (
                "You are an explorer. Read the supplied task requirements and relevant files. "
                "Identify constraints, data formats, edge cases, and likely causes of problems. "
                "Do not modify files. Return a concise report with file paths and evidence; "
                "distinguish observations from assumptions and mention missing context."
            ),
        },
        # Implementer chịu trách nhiệm sửa và chạy kiểm tra, rồi báo cáo đúng
        # tệp đã đổi và lỗi còn lại để tác tử chính có thể kiểm chứng tiếp.
        {
            "name": "implementer",
            "description": (
                "Use when a concrete change or multi-step processing task is ready to implement "
                "and verify with tests or scripts."
            ),
            "system_prompt": (
                "You are an implementer. Follow all requirements in the delegation message, "
                "read relevant specifications, and implement the requested changes. "
                "Run appropriate tests or scripts and inspect their results. "
                "Report files actually changed, commands run, results, and unresolved issues. "
                "Do not claim success without verification."
            ),
        },
        # Reviewer đọc lại kết quả một cách độc lập và không sửa tệp; vai trò
        # này giúp phát hiện trường hợp test hiện có đạt nhưng đặc tả chưa đạt.
        {
            "name": "reviewer",
            "description": (
                "Use after implementation when results need independent verification against "
                "the task requirements, output formats, and edge cases."
            ),
            "system_prompt": (
                "You are an independent reviewer. Compare the actual files and outputs against "
                "every requirement provided in the delegation message. Inspect edge cases and "
                "run checks as needed without editing files. Return findings with evidence, "
                "verification results, and any remaining uncertainty."
            ),
        },
    ]
