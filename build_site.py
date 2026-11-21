import argparse
import json
import os
import re
from datetime import date
from pathlib import Path

BASE_URL = "https://79king.ai"
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".wrangler", ".github"}
ASSET_DIRS = ("css", "js", "images")

# Bỏ qua không đưa vào sitemap.xml (ví dụ file nháp/template nếu có)
EXCLUDE_FROM_SITEMAP = {
    "_template-bai-viet.html",
    "bai-viet-mau.html",
}

# Khối footer chuẩn dùng chung cho toàn bộ trang HTML
# Mỗi lần chỉnh sửa mẫu này và chạy `python build_site.py --apply`, toàn bộ file sẽ cập nhật theo.
FOOTER_HTML = """<div id="footer">
            <div class="fBox">
                <nav class="footer-seo-links" aria-label="Liên kết hữu ích">
                    <ul>
                        <li><a href="/ho-tro/ve-chung-toi.html" title="Về Chúng Tôi - 79King">Về Chúng Tôi</a></li>
                        <li><a href="/ho-tro/doi-tac-hop-tac.html" title="Đối Tác Hợp Tác 79King">Đối Tác Hợp Tác</a></li>
                        <li><a href="/ho-tro/huong-dan-gui-tien.html" title="Hướng Dẫn Gửi Tiền 79King">Gửi Tiền Như Nào</a></li>
                        <li><a href="/ho-tro/huong-dan-rut-tien.html" title="Hướng Dẫn Rút Tiền 79King">Rút Tiền Như Nào</a></li>
                        <li><a href="/ho-tro/lien-he.html" title="Liên Hệ Với Chúng Tôi - 79King">Liên Hệ Với Chúng Tôi</a></li>
                    </ul>
                </nav>
                <!-- ĐẶT NGAY DƯỚI KHỐI ABOUT US -->
                <section class="after-about-extra" aria-label="Sản phẩm và thông tin 79King">
                    <div class="after-about-grid">
                        <div class="after-about-col">
                            <h4 class="after-about-title">SẢN PHẨM 79KING</h4>
                            <ul class="after-about-list">
                                <li><a href="/chuyen-muc/casino.html">Casino 79King</a></li>
                                <li><a href="/chuyen-muc/no-hu.html">Nổ hũ 79King</a></li>
                                <li><a href="/chuyen-muc/the-thao.html">Thể thao 79King</a></li>
                                <li><a href="/chuyen-muc/ban-ca.html">Bắn Cá 79King</a></li>
                                <li><a href="/chuyen-muc/game-bai.html">Game bài 79King</a></li>
                                <li><a href="/chuyen-muc/da-ga.html">Đá gà 79King</a></li>
                                <li><a href="/chuyen-muc/xo-so.html">Xổ số 79King</a></li>
                            </ul>
                        </div>

                        <div class="after-about-col">
                            <h4 class="after-about-title">THÔNG TIN</h4>
                            <p class="after-about-text">Giấy phép quốc tế: Giấy phép Pagcor (Philippines)</p>
                            <p class="after-about-text">Giấy phép Isle Of Man (Đảo Man) và giấy phép Curacao eGaming (Curacao)</p>
                            <p class="after-about-text after-about-tags">#79king #nhacai79king #code79king</p>
                            <p class="after-about-bg-match"><a href="/sitemap.xml">Sơ đồ trang web</a></p>
                            <p class="after-about-bg-match">By: 79king.ai</p>
                        </div>
                    </div>
                </section>

                <div class="fImg"></div>
                <p>Copyright © 79KING.AI Reserved</p>
            </div>
        </div>"""


def collect_html_files(root: Path) -> list[Path]:
    return sorted(
        p for p in root.rglob("*.html")
        if not any(part in SKIP_DIRS for part in p.parts)
    )


def build_page_index(root: Path, html_files: list[Path]) -> dict[str, str]:
    """Lập bản đồ mọi file .html thực tế -> đường dẫn tuyệt đối từ root (/)."""
    exact_map: dict[str, str] = {}
    name_candidates: dict[str, list[str]] = {}

    for p in html_files:
        rel_posix = p.relative_to(root).as_posix()
        root_url = f"/{rel_posix}"
        exact_map[rel_posix.lower()] = root_url
        name_candidates.setdefault(p.name.lower(), []).append(root_url)

    lookup: dict[str, str] = dict(exact_map)
    for fname, urls in name_candidates.items():
        if len(urls) == 1:
            lookup[fname] = urls[0]
        else:
            non_root = [u for u in urls if u.count("/") > 1]
            lookup[fname] = sorted(non_root)[-1] if non_root else sorted(urls)[0]

    return lookup


def compute_relative_href(from_file: Path, target_root_url: str, root: Path) -> str:
    target_abs = root / target_root_url.lstrip("/")
    return Path(os.path.relpath(target_abs, start=from_file.parent)).as_posix()


def format_path(target_root_url: str, current_file: Path, root: Path, mode: str) -> str:
    if mode == "root":
        return target_root_url
    return compute_relative_href(current_file, target_root_url, root)


def remove_existing_footers(html: str) -> str:
    """
    Gỡ sạch mọi khối <div id="footer">...</div> (đếm đúng độ sâu thẻ <div> lồng nhau)
    và thẻ <footer>...</footer> cũ để không bao giờ bị trùng 2 footer.
    """
    # 1. Xóa thẻ <footer>...</footer> nếu có
    html = re.sub(r"<footer\b[^>]*>.*?</footer>", "", html, flags=re.IGNORECASE | re.DOTALL)

    # 2. Xóa các khối <div id="footer"...>...</div> theo độ sâu thẻ <div>
    start_pat = re.compile(r'<div\b[^>]*\bid=["\']footer["\'][^>]*>', re.IGNORECASE)
    div_open_pat = re.compile(r"<div\b[^>]*>", re.IGNORECASE)
    div_close_pat = re.compile(r"</div\s*>", re.IGNORECASE)

    while True:
        m = start_pat.search(html)
        if not m:
            break

        depth = 1
        pos = m.end()
        end_idx = None

        tokens = sorted(
            [(t.start(), t.end(), "open") for t in div_open_pat.finditer(html, pos)]
            + [(t.start(), t.end(), "close") for t in div_close_pat.finditer(html, pos)],
            key=lambda x: x[0],
        )

        for t_start, t_end, kind in tokens:
            if kind == "open":
                depth += 1
            else:
                depth -= 1
                if depth == 0:
                    end_idx = t_end
                    break

        if end_idx is None:
            body_m = re.search(r"</body>", html[m.start() :], re.IGNORECASE)
            end_idx = m.start() + body_m.start() if body_m else len(html)

        html = html[: m.start()] + html[end_idx:]

    return html


def sync_footer_block(html: str) -> tuple[str, bool]:
    """
    Xóa footer cũ (nếu có) và chèn bản FOOTER_HTML mới nhất ngay trước thẻ đóng </div> cuối cùng của #app
    (hoặc ngay trước </body>).
    """
    cleaned = remove_existing_footers(html)
    # Dọn bớt các comment footer cũ & dòng trống thừa
    cleaned = re.sub(r"<!--\s*FOOTER ĐỒNG BỘ TRANG CHỦ\s*-->\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

    # Chèn trước thẻ đóng </div> cuối cùng trước </body> (chính là thẻ đóng của <div id="app">)
    body_close_match = re.search(r"(\s*</div>\s*)(</body>)", cleaned, re.IGNORECASE)
    if body_close_match:
        insert_pos = body_close_match.start(1)
        updated = (
            cleaned[:insert_pos].rstrip()
            + f"\n\n        <!-- FOOTER ĐỒNG BỘ TRANG CHỦ -->\n        {FOOTER_HTML}"
            + cleaned[insert_pos:]
        )
    elif re.search(r"</body>", cleaned, re.IGNORECASE):
        updated = re.sub(
            r"</body>",
            f"\n        {FOOTER_HTML}\n</body>",
            cleaned,
            count=1,
            flags=re.IGNORECASE,
        )
    else:
        updated = cleaned.rstrip() + f"\n\n{FOOTER_HTML}\n"

    return updated, updated != html


def process_html_file(
    file_path: Path,
    root: Path,
    page_map: dict[str, str],
    mode: str,
    sync_footer: bool,
) -> tuple[str, list[str]]:
    logs: list[str] = []
    html = file_path.read_text(encoding="utf-8")
    rel_posix = file_path.relative_to(root).as_posix()
    expected_full_url = f"{BASE_URL}/" if rel_posix == "index.html" else f"{BASE_URL}/{rel_posix}"

    # 1. Đồng bộ footer mới nhất từ mẫu FOOTER_HTML
    if sync_footer:
        html, footer_changed = sync_footer_block(html)
        if footer_changed:
            logs.append('footer: đã cập nhật theo mẫu <div id="footer"> mới nhất')

    # 2. Chuẩn hóa đường dẫn tài nguyên (css/, js/, images/)
    dirs_re = "|".join(re.escape(d) for d in ASSET_DIRS)
    asset_pat = re.compile(
        rf"""(?P<prefix>\b(?:href|src)\s*=\s*["'])(?P<val>(?:\.\./|/)*(?:{dirs_re})/[^"']+)(?P<suffix>["'])""",
        re.IGNORECASE,
    )

    def _fix_asset(m: re.Match) -> str:
        old_val = m.group("val")
        clean_rel = re.sub(rf"^(?:\.\./|/)+(?=(?:{dirs_re})/)", "", old_val, flags=re.IGNORECASE)
        new_val = format_path(f"/{clean_rel}", file_path, root, mode)
        if new_val != old_val:
            logs.append(f"asset: {old_val} -> {new_val}")
        return f"{m.group('prefix')}{new_val}{m.group('suffix')}"

    html = asset_pat.sub(_fix_asset, html)

    # 3. Chuẩn hóa link nội bộ tới các file .html trong dự án
    link_pat = re.compile(
        r"""(?P<prefix>\bhref\s*=\s*["'])(?P<val>(?!https?://|//|mailto:|tel:|#)(?:\.\./|/)*[a-zA-Z0-9_./-]+\.html)(?P<anchor>#[^"']*)?(?P<suffix>["'])""",
        re.IGNORECASE,
    )

    def _fix_link(m: re.Match) -> str:
        old_val = m.group("val")
        anchor = m.group("anchor") or ""
        clean_key = re.sub(r"^(?:\.\./|/)+", "", old_val).lower()
        if clean_key in page_map:
            new_val = format_path(page_map[clean_key], file_path, root, mode)
            if new_val != old_val:
                logs.append(f"link: {old_val} -> {new_val}{anchor}")
            return f"{m.group('prefix')}{new_val}{anchor}{m.group('suffix')}"
        return m.group(0)

    html = link_pat.sub(_fix_link, html)

    # 4. Đồng bộ canonical, og:url và BreadcrumbList JSON-LD
    canon_pat = re.compile(
        r"""(<link\b[^>]*\brel\s*=\s*["']canonical["'][^>]*\bhref\s*=\s*["'])([^"']+)(["'][^>]*>)""",
        re.IGNORECASE,
    )

    def _fix_canon(m: re.Match) -> str:
        if m.group(2) != expected_full_url:
            logs.append(f"canonical: {m.group(2)} -> {expected_full_url}")
        return f"{m.group(1)}{expected_full_url}{m.group(3)}"

    html = canon_pat.sub(_fix_canon, html)

    og_pat = re.compile(
        r"""(<meta\b[^>]*\bproperty\s*=\s*["']og:url["'][^>]*\bcontent\s*=\s*["'])([^"']+)(["'][^>]*>)""",
        re.IGNORECASE,
    )

    def _fix_og(m: re.Match) -> str:
        if m.group(2) != expected_full_url:
            logs.append(f"og:url: {m.group(2)} -> {expected_full_url}")
        return f"{m.group(1)}{expected_full_url}{m.group(3)}"

    html = og_pat.sub(_fix_og, html)

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
                if steps[-1].get("item") != expected_full_url:
                    old_bc = steps[-1].get("item")
                    steps[-1]["item"] = expected_full_url
                    dumped = json.dumps(parsed, ensure_ascii=False, indent=8)
                    html = html[: m.start(2)] + "\n" + dumped + "\n    " + html[m.end(2) :]
                    logs.append(f"breadcrumb: {old_bc} -> {expected_full_url}")

    return html, logs


def generate_sitemap_xml(root: Path, html_files: list[Path]) -> str:
    today_str = date.today().isoformat()
    urls: list[str] = []

    for p in html_files:
        if p.name in EXCLUDE_FROM_SITEMAP:
            continue
        rel_posix = p.relative_to(root).as_posix()
        if rel_posix == "index.html":
            loc = f"{BASE_URL}/"
            priority = "1.0"
        else:
            loc = f"{BASE_URL}/{rel_posix}"
            priority = "0.8" if p.parent.name == "chuyen-muc" else "0.7"

        urls.append(
            f"  <url>\n"
            f"    <loc>{loc}</loc>\n"
            f"    <lastmod>{today_str}</lastmod>\n"
            f"    <priority>{priority}</priority>\n"
            f"  </url>"
        )

    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(urls)
        + "\n</urlset>\n"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Build & đồng bộ toàn bộ HTML + sitemap.xml cho 79King.")
    parser.add_argument("--apply", action="store_true", help="Ghi thay đổi thực tế vào các file.")
    parser.add_argument("--mode", choices=["root", "relative"], default="root", help="Kiểu đường dẫn.")
    parser.add_argument("--no-footer", action="store_true", help="Không ghi đè khối footer.")
    parser.add_argument("--no-sitemap", action="store_true", help="Không cập nhật sitemap.xml.")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent
    html_files = collect_html_files(root)
    page_map = build_page_index(root, html_files)
    sync_footer = not args.no_footer

    print(f"Thư mục: {root}")
    print(f"Tổng file .html: {len(html_files)} | Mode: {args.mode} | Footer: {'ON' if sync_footer else 'OFF'}\n")

    changed_html = 0
    for file_path in html_files:
        rel_posix = file_path.relative_to(root).as_posix()
        original = file_path.read_text(encoding="utf-8")
        updated, logs = process_html_file(file_path, root, page_map, args.mode, sync_footer)

        if logs or updated != original:
            changed_html += 1
            tag = "[APPLY]" if args.apply else "[PREVIEW]"
            print(f"{tag} {rel_posix} ({len(logs)} mục)")
            for item in logs[:5]:
                print(f"   - {item}")
            if len(logs) > 5:
                print(f"   - ... +{len(logs) - 5} mục khác")
            if args.apply:
                file_path.write_text(updated, encoding="utf-8")

    if not args.no_sitemap:
        sitemap_path = root / "sitemap.xml"
        new_sitemap = generate_sitemap_xml(root, html_files)
        old_sitemap = sitemap_path.read_text(encoding="utf-8") if sitemap_path.exists() else ""
        if new_sitemap != old_sitemap:
            tag = "[APPLY]" if args.apply else "[PREVIEW]"
            print(f"\n{tag} sitemap.xml: cập nhật danh sách {len(html_files)} trang.")
            if args.apply:
                sitemap_path.write_text(new_sitemap, encoding="utf-8")
        else:
            print("\nsitemap.xml: đã đồng bộ.")

    print(f"\nHoàn tất: {changed_html}/{len(html_files)} file HTML có thay đổi.")
    if not args.apply:
        print("Chạy lại với --apply để áp dụng thay đổi.")


if __name__ == "__main__":
    main()