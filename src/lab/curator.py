"""GUIDE Phần 3 - Người tuyển chọn skill (skill curator): tự viết skill từ các lần chạy thất bại.   >>> SINH VIÊN CÀI ĐẶT curate_skills <<<

Pseudo-code: guides/pseudocode/04_curator.md
Kiểm tra:    pytest tests/test_04_curator.py
Chạy thật:   python -m lab.curator
"""
import json
import re
from pathlib import Path

from .tasks import ROOT, eval_markers   # có sẵn: định danh của tác vụ đánh giá, tính lúc chạy

# ---- CÓ SẴN, KHÔNG SỬA: kiểm tra và tách khối skill (phần dễ sai và liên quan bảo mật) ----------------
SAFE_NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def validate_skill(text: str, expected_name: str | None = None) -> list[str]:
    """Kiểm tra nội dung một SKILL.md. Trả về danh sách vấn đề (rỗng = hợp lệ).

    Quy tắc: có khối YAML frontmatter; `name` chữ thường/số/gạch ngang (tối đa 64 ký tự) và bằng `expected_name`
    nếu được truyền; có `description` (tối đa 1024 ký tự); phần thân tối đa 80 dòng; không chứa chuỗi nào của
    `eval_markers()`. Quy tắc về `name` cũng là biện pháp bảo mật: tên khối do LLM sinh ra được dùng để tạo
    đường dẫn, nên `../evil` không được lọt qua.
    """
    problems = []
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text.strip() + "\n", re.S)
    if not m:
        return ["missing YAML frontmatter"]
    front, body = m.groups()
    name = re.search(r"^name:\s*(.+)$", front, re.M)
    desc = re.search(r"^description:\s*(.+)$", front, re.M)
    n = name.group(1).strip() if name else ""
    if not SAFE_NAME.fullmatch(n) or len(n) > 64:
        problems.append("invalid name")
    elif expected_name is not None and n != expected_name:
        problems.append("name differs from the block name")
    if not desc or len(desc.group(1).strip()) > 1024:
        problems.append("missing or too long description")
    if len(body.strip().splitlines()) > 80:
        problems.append("body longer than 80 lines")
    low = text.lower()
    for marker in eval_markers():
        if marker in low:
            problems.append(f"mentions evaluation material: {marker}")
    return problems


def parse_skill_blocks(reply: str) -> list[tuple[str, str]]:
    """Tách câu trả lời của LLM thành danh sách (name, nội dung SKILL.md).

    Khuôn dạng: `=== SKILL: <name> ===` ... `=== END ===`. Một khối kết thúc ở điểm nào đến trước trong ba điểm:
    `=== END ===`, tiêu đề `=== SKILL:` kế tiếp, hoặc cuối văn bản (LLM đôi khi quên dòng END).
    """
    pattern = re.compile(r"^=== SKILL: (\S+) ===[ \t]*\n(.*?)(?=^=== END ===|^=== SKILL: |\Z)", re.S | re.M)
    return [(name, text.strip()) for name, text in pattern.findall(str(reply))]
# --------------------------------------------------------------------------------------------------


def curate_skills(results_dir="results", source_condition="baseline", out_dir=None, model=None, max_skills: int = 3) -> list[Path]:
    """Đọc các lần chạy của TÁC VỤ HỌC (role == "learn") trong `source_condition`, nhờ LLM viết skill, ghi file.

    Các bước: nạp run.json + trace.md -> (nếu không có check nào thất bại: in cảnh báo và trả về [] mà KHÔNG gọi LLM)
    -> dựng prompt -> model.invoke(prompt) -> parse_skill_blocks -> validate_skill(text, expected_name=name)
    -> ghi `<out_dir>/<name>/SKILL.md`. Mặc định `out_dir` = <gốc lab>/skills/auto (dùng `ROOT` từ lab.tasks).
    Giữ tối đa `max_skills` skill hợp lệ; skill không hợp lệ bị bỏ qua.
    Prompt chứa, với mỗi check thất bại, TÊN và trường `detail` (lời nhận xét của bot đánh giá: phát biểu quy tắc bị vi phạm)
    cùng phần cuối của vết (trace). Với tác vụ học, `detail` chỉ phát biểu quy tắc, không chứa đáp án.
    Tuyệt đối KHÔNG đưa dữ liệu của tác vụ đánh giá (role == "eval") vào prompt.
    model mặc định: make_model() (lab.model).
    Trả về: danh sách đường dẫn SKILL.md đã ghi.
    """
    # TODO (Phần 3): chỉ học từ feedback và trace của role == "learn".
    # Lọc role trước khi đọc trace: tác vụ đánh giá tuyệt đối không vào prompt.
    # Giới hạn phần đuôi trace để prompt tập trung vào bước gần kết quả chấm.
    runs = []
    for run_path in sorted((Path(results_dir) / source_condition).glob("*/run.json")):
        run = json.loads(run_path.read_text(encoding="utf-8"))
        if run.get("role") != "learn":
            continue
        failed = [
            (check["name"], check.get("detail", ""))
            for check in run.get("checks", []) if check.get("passed") is False
        ]
        trace_path = run_path.with_name("trace.md")
        trace = trace_path.read_text(encoding="utf-8")[-6000:] if trace_path.exists() else ""
        runs.append((run.get("task", run_path.parent.name), failed, trace))

    if not any(failed for _, failed, _ in runs):
        # Không có tín hiệu lỗi thì không tiêu token để tạo skill võ đoán.
        print("Không có check thất bại ở tác vụ học; curator không gọi mô hình.")
        return []

    sections = []
    for task, failed, trace in runs:
        feedback = "\n".join(f"- {name}: {detail}" for name, detail in failed) or "- None"
        sections.append(f"Task: {task}\nFailed checks:\n{feedback}\nTrace tail:\n{trace}")
    prompt = (
        # Prompt dùng feedback làm căn cứ, nhưng model vẫn có thể sinh quy tắc
        # sai; vì thế các skill đầu ra phải được đọc và đánh giá trước khi giữ.
        "Write up to {limit} short, reusable SKILL.md files for a coding and data-analysis agent.\n"
        "Infer general process errors from the failed checks and execution traces below.\n"
        "Use only learning-task evidence. Do not mention task IDs, task-specific input files, "
        "answers, or particular numbers.\n"
        "Treat checker feedback as the authority: turn each relevant RULE into a verification step. "
        "Do not invent filters, imputations, package installations, or output formats. "
        "When an optional library is missing, use the Python standard library if practical. "
        "Check that every required output file exists and matches its specified schema before finishing.\n"
        "Prefer 2-3 focused skills over broad advice. Every instruction should be testable, "
        "and should say to read the task specification before deciding details.\n"
        "Cover the distinct failure families when evidence supports them: code changes, "
        "dirty structured data, and log processing. Avoid fixed counts or values that "
        "only fit a single learning example.\n"
        "Each skill needs YAML frontmatter with a lowercase hyphenated name and a one-sentence "
        "description starting 'Use when'; follow with at most 40 lines of actionable instructions.\n"
        "Return each skill in exactly this format:\n"
        "=== SKILL: <name> ===\n---\nname: <name>\n"
        "description: Use when ...\n---\n<instructions>\n=== END ===\n\n{runs}"
    ).format(limit=max_skills, runs="\n\n".join(sections))

    # TODO: mô hình có thể trả skill sai định dạng hoặc cố tạo đường dẫn nguy hiểm.
    # validate_skill kiểm tra cả tên thư mục và frontmatter trước khi ghi file.
    if model is None:
        from .model import make_model
        model = make_model()
    reply = model.invoke(prompt).content
    destination = Path(out_dir) if out_dir is not None else ROOT / "skills" / "auto"
    written = []
    seen = set()
    for name, skill_text in parse_skill_blocks(reply):
        if len(written) >= max_skills:
            break
        # validate_skill chặn tên đường dẫn nguy hiểm, frontmatter sai và
        # marker của tác vụ đánh giá; tên trùng không được ghi đè trong lượt này.
        if name in seen or validate_skill(skill_text, expected_name=name):
            continue
        path = destination / name / "SKILL.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(skill_text.rstrip() + "\n", encoding="utf-8")
        written.append(path)
        seen.add(name)
    return written


if __name__ == "__main__":
    for p in curate_skills():
        print("wrote", p)
