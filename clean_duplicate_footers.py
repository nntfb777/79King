import argparse
import re
from pathlib import Path

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".wrangler", ".github"}

# Khối footer chuẩn dùng chung (sử dụng <div id="footer"> khớp CSS hiện tại của 79King)
STANDARD_FOOTER = """<div id="footer">
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
                <p>Copyright © 79KING.COM Reserved</p>
            </div>
        </div>"""


def collect_html_files(root: Path) -> list[Path]:
    return sorted(
        p for p in root.rglob("*.html")
        if not any(part in SKIP_DIRS for part in p.parts)
    )


def remove_all_footer_blocks(html: str) -> tuple[str, int]:
    """
    Xóa toàn bộ các khối <div id="footer">...</div> (tính cả thẻ đóng tương ứng theo độ sâu <div>)
    hoặc thẻ <footer>...</footer>. Trả về (html_đã_gỡ, số_khối_đã_gỡ).
    """
    removed_count = 0

    # 1. Gỡ các thẻ <footer ...>...</footer> nếu có
    html, n_tag = re.subn(r"<footer\b[^>]*>.*?</footer>", "", html, flags=re.IGNORECASE | re.DOTALL)
    removed_count += n_tag

    # 2. Gỡ các khối <div id="footer"...>...</div> theo độ sâu thẻ <div> để không xóa nhầm </div> bên ngoài
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
            # Nếu thiếu thẻ đóng, cắt tới trước </body> hoặc cuối file
            body_m = re.search(r"</body>", html[m.start() :], re.IGNORECASE)
            end_idx = m.start() + body_m.start() if body_m else len(html)

        html = html[: m.start()] + html[end_idx:]
        removed_count += 1

    return html, removed_count


def fix_file_footer(file_path: Path) -> tuple[str, int]:
    original = file_path.read_text(encoding="utf-8")
    stripped_html, count = remove_all_footer_blocks(original)

    if count <= 1:
        return original, 0

    # Dọn các dòng trống thừa liên tiếp sinh ra sau khi gỡ khối lặp
    stripped_html = re.sub(r"\n{3,}", "\n\n", stripped_html)

    # Chèn lại đúng 1 khối footer chuẩn ngay trước </body>
    if re.search(r"</body>", stripped_html, re.IGNORECASE):
        updated = re.sub(
            r"</body>",
            f"        {STANDARD_FOOTER}\n    </div>\n</body>",
            stripped_html,
            count=1,
            flags=re.IGNORECASE,
        )
    else:
        updated = stripped_html + f"\n{STANDARD_FOOTER}\n"

    return updated, count


def main() -> None:
    parser = argparse.ArgumentParser(description="Xóa lỗi trùng footer và giữ đúng 1 footer chuẩn cho mỗi file HTML.")
    parser.add_argument("--apply", action="store_true", help="Ghi đè sửa trực tiếp lên file.")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent
    html_files = collect_html_files(root)

    fixed_files = 0
    for f in html_files:
        updated, count = fix_file_footer(f)
        if count > 1:
            fixed_files += 1
            rel = f.relative_to(root).as_posix()
            tag = "[APPLY]" if args.apply else "[FOUND]"
            print(f"{tag} {rel}: phát hiện {count} khối footer -> gộp còn 1 khối chuẩn.")
            if args.apply:
                f.write_text(updated, encoding="utf-8")

    print(f"\nTổng kết: {fixed_files}/{len(html_files)} file có lỗi lặp footer.")
    if not args.apply and fixed_files > 0:
        print("Chạy kèm --apply để dọn sạch ngay.")


if __name__ == "__main__":
    main()