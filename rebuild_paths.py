import argparse
import json
import re
from pathlib import Path

BASE_URL = "https://79king.ai"
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".wrangler", ".github"}
ASSET_DIRS = ("css", "js", "images")


def collect_html_files(root: Path) -> list[Path]:
    return sorted(
        p for p in root.rglob("*.html")
        if not any(part in SKIP_DIRS for part in p.parts)
    )


def build_page_index(root: Path, html_files: list[Path]) -> dict[str, str]:
    """
    Tự dò vị trí thực tế của mọi file .html trong dự án để trả về đường dẫn chuẩn từ root (/).
    Ví dụ: nếu 'huong-dan.html' nằm ở 'chuyen-muc/huong-dan.html' -> '/chuyen-muc/huong-dan.html'.
    """
    index_map: dict[str, str] = {}
    for p in html_files:
        rel = p.relative_to(root).as_posix()
        root_href = f"/{rel}"
        index_map[rel.lower()] = root_href
        # Ưu tiên giữ file ở gốc nếu trùng tên, hoặc gán theo tên file nếu chỉ có 1 nơi
        filename_key = p.name.lower()
        if filename_key not in index_map or len(p.parts) == 1:
            index_map[filename_key] = root_href
    return index_map


def get_asset_prefix(file_path: Path, root: Path, use_relative: bool) -> str:
    if not use_relative:
        return "/"
    rel = file_path.relative_to(root)
    depth = max(0, len(rel.parts) - 1)
    return "../" * depth


def transform_html(html: str, rel_posix: str, asset_prefix: str, page_map: dict[str, str]) -> tuple[str, list[str]]:
    logs: list[str] = []
    target_full_url = f"{BASE_URL}/{rel_posix}"

    # 1. Sửa đường dẫn asset (css/, js/, images/)
    dirs_re = "|".join(re.escape(d) for d in ASSET_DIRS)
    asset_pat = re.compile(
        rf"""(?P<prefix>\b(?:href|src)\s*=\s*["'])(?P<val>(?:\.\./|/)*(?:{dirs_re})/[^"']+)(?P<suffix>["'])""",
        re.IGNORECASE,
    )

    def _fix_asset(m: re.Match) -> str:
        old_val = m.group("val")
        stripped = re.sub(rf"^(?:\.\./|/)+(?=(?:{dirs_re})/)", "", old_val)
        new_val = f"{asset_prefix}{stripped}"
        if new_val != old_val:
            logs.append(f"asset: {old_val} -> {new_val}")
        return f"{m.group('prefix')}{new_val}{m.group('suffix')}"

    html = asset_pat.sub(_fix_asset, html)

    # 2. Sửa link nội bộ tới các file .html khác trong dự án
    link_pat = re.compile(
        r"""(?P<prefix>\bhref\s*=\s*["'])(?P<val>(?:\.\./|/)*[a-zA-Z0-9_./-]+\.html)(?P<anchor>#[^"']*)?(?P<suffix>["'])""",
        re.IGNORECASE,
    )

    def _fix_link(m: re.Match) -> str:
        old_val = m.group("val")
        anchor = m.group("anchor") or ""
        clean_key = re.sub(r"^(?:\.\./|/)+", "", old_val).lower()
        if clean_key in page_map:
            new_val = page_map[clean_key]
            if new_val != old_val:
                logs.append(f"link: {old_val} -> {new_val}{anchor}")
            return f"{m.group('prefix')}{new_val}{anchor}{m.group('suffix')}"
        return m.group(0)

    html = link_pat.sub(_fix_link, html)

    # 3. Cập nhật canonical
    canon_pat = re.compile(
        r"""(<link\b[^>]*\brel\s*=\s*["']canonical["'][^>]*\bhref\s*=\s*["'])([^"']+)(["'][^>]*>)""",
        re.IGNORECASE,
    )

    def _fix_canon(m: re.Match) -> str:
        if m.group(2) != target_full_url:
            logs.append(f"canonical: {m.group(2)} -> {target_full_url}")
        return f"{m.group(1)}{target_full_url}{m.group(3)}"

    html = canon_pat.sub(_fix_canon, html)

    # 4. Cập nhật og:url
    og_pat = re.compile(
        r"""(<meta\b[^>]*\bproperty\s*=\s*["']og:url["'][^>]*\bcontent\s*=\s*["'])([^"']+)(["'][^>]*>)""",
        re.IGNORECASE,
    )

    def _fix_og(m: re.Match) -> str:
        if m.group(2) != target_full_url:
            logs.append(f"og:url: {m.group(2)} -> {target_full_url}")
        return f"{m.group(1)}{target_full_url}{m.group(3)}"

    html = og_pat.sub(_fix_og, html)

    # 5. Cập nhật item cuối của BreadcrumbList JSON-LD
    ld_pat = re.compile(
        r"""(<script\b[^>]*type\s*=\s*["']application/ld\+json["'][^>]*>)(.*?)(</script>)""",
        re.IGNORECASE | re.DOTALL,
    )
    for m in ld_pat.finditer(html):
        raw_block = m.group(2).strip()
        try:
            parsed = json.loads(raw_block)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict) and parsed.get("@type") == "BreadcrumbList":
            steps = parsed.get("itemListElement")
            if isinstance(steps, list) and len(steps) >= 2 and isinstance(steps[-1], dict):
                if steps[-1].get("item") != target_full_url:
                    old_bc = steps[-1].get("item")
                    steps[-1]["item"] = target_full_url
                    dumped = json.dumps(parsed, ensure_ascii=False, indent=8)
                    html = html[: m.start(2)] + "\n" + dumped + "\n    " + html[m.end(2) :]
                    logs.append(f"breadcrumb: {old_bc} -> {target_full_url}")

    return html, logs


def main() -> None:
    parser = argparse.ArgumentParser(description="Sửa đồng bộ asset, link trang nội bộ và URL SEO cho HTML.")
    parser.add_argument("--apply", action="store_true", help="Ghi thay đổi vào file.")
    parser.add_argument("--relative", action="store_true", help="Dùng ../ cho asset thay vì /.")
    parser.add_argument("--backup", action="store_true", help="Tạo file .bak trước khi ghi.")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent
    html_files = collect_html_files(root)
    page_map = build_page_index(root, html_files)

    print(f"Thư mục gốc: {root}")
    print(f"Tìm thấy {len(html_files)} file .html\n")

    changed_files = 0
    for file_path in html_files:
        rel_path = file_path.relative_to(root)
        rel_posix = rel_path.as_posix()
        prefix = get_asset_prefix(file_path, root, args.relative)

        original = file_path.read_text(encoding="utf-8")
        updated, logs = transform_html(original, rel_posix, prefix, page_map)

        if logs:
            changed_files += 1
            tag = "[APPLY]" if args.apply else "[PREVIEW]"
            print(f"{tag} {rel_posix} ({len(logs)} thay đổi):")
            for item in logs[:6]:
                print(f"   - {item}")
            if len(logs) > 6:
                print(f"   - ... và {len(logs) - 6} thay đổi khác")
            if args.apply:
                if args.backup:
                    file_path.with_suffix(file_path.suffix + ".bak").write_text(original, encoding="utf-8")
                file_path.write_text(updated, encoding="utf-8")

    print(f"\nTổng kết: {changed_files}/{len(html_files)} file có thay đổi.")
    if not args.apply:
        print("Hãy chạy kèm --apply để ghi đè thực tế.")


if __name__ == "__main__":
    main()