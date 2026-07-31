#!/usr/bin/env python3
"""Capture real Odoo UI screenshots for the Apps Store description page."""
from __future__ import annotations

import sys
import traceback
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parents[1] / "static" / "description"
BASE = "http://127.0.0.1:8070"
DB = "StickyNotesTest"
USER = "admin"
PASSWORD = "admin"
PARTNER_ID = 10


def save_shot(page, name: str, width: int = 1280, height: int = 800) -> Path:
    path = OUT / name
    page.screenshot(path=str(path), full_page=False)
    img = Image.open(path).convert("RGB")
    if img.size != (width, height):
        img = img.resize((width, height), Image.Resampling.LANCZOS)
    img.save(path, "PNG", optimize=True)
    print(f"Saved {path} ({img.size[0]}x{img.size[1]}) url={page.url}")
    return path


def dbg(page, name: str) -> None:
    path = OUT / f"_debug_{name}.png"
    page.screenshot(path=str(path), full_page=False)
    print(f"DEBUG {name}: url={page.url} -> {path}")


def login(page) -> None:
    page.goto(f"{BASE}/web/login?db={DB}", wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(1000)
    dbg(page, "login_page")
    if page.locator('input[name="login"]').count():
        page.fill('input[name="login"]', USER)
        page.fill('input[name="password"]', PASSWORD)
        with page.expect_navigation(wait_until="domcontentloaded", timeout=60000):
            page.click('button[type="submit"]')
    page.wait_for_timeout(2500)
    dbg(page, "after_login")


def dismiss_overlays(page) -> None:
    selectors = [
        "button:has-text('Skip')",
        "button:has-text('Maybe later')",
        "button:has-text('Close')",
        ".o_tooltip_button",
        ".o_notification .o_notification_close",
        ".modal-header .btn-close",
        ".o-overlay-item .btn-close",
    ]
    for sel in selectors:
        try:
            loc = page.locator(sel)
            for i in range(min(loc.count(), 3)):
                item = loc.nth(i)
                if item.is_visible():
                    item.click(timeout=800)
                    page.wait_for_timeout(300)
        except Exception:
            pass


def main() -> int:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--disable-dev-shm-usage"])
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            device_scale_factor=1,
        )
        page = context.new_page()
        page.set_default_timeout(30000)

        try:
            login(page)
            dismiss_overlays(page)

            # Partner form
            page.goto(
                f"{BASE}/odoo/contacts/{PARTNER_ID}",
                wait_until="domcontentloaded",
                timeout=60000,
            )
            page.wait_for_timeout(3500)
            dismiss_overlays(page)
            dbg(page, "partner")
            # Wait a bit for OWL panel RPC
            for _ in range(10):
                if page.locator(".o_quick_sticky_notes_panel").count():
                    break
                page.wait_for_timeout(500)
            if page.locator(".o_quick_sticky_notes_panel.o_qsn_collapsed").count():
                page.locator(".o_qsn_toggle").first.click()
                page.wait_for_timeout(400)
            save_shot(page, "main_screenshot.png")

            # Colors close-up
            panel = page.locator(".o_quick_sticky_notes_panel").first
            if panel.count():
                box = panel.bounding_box()
                if box:
                    path = OUT / "screenshot_colors.png"
                    page.screenshot(
                        path=str(path),
                        clip={
                            "x": max(0, box["x"] - 24),
                            "y": max(0, box["y"] - 16),
                            "width": min(720, box["width"] + 48),
                            "height": min(820, box["height"] + 32),
                        },
                    )
                    img = Image.open(path).convert("RGB").resize(
                        (1280, 800), Image.Resampling.LANCZOS
                    )
                    img.save(path, "PNG", optimize=True)
                    print(f"Saved {path} (panel crop)")
                else:
                    save_shot(page, "screenshot_colors.png")
            else:
                print("WARNING: panel missing; colors shot = main form")
                save_shot(page, "screenshot_colors.png")

            # My Notes via menu click if possible
            opened = False
            try:
                # App switcher
                app = page.locator(".o_navbar_apps_menu button, .o_menu_toggle, button.o_grid").first
                if app.count():
                    app.click()
                    page.wait_for_timeout(800)
                    sticky_app = page.get_by_text("Sticky Notes", exact=False).first
                    if sticky_app.count():
                        sticky_app.click()
                        page.wait_for_timeout(1500)
                        my_notes = page.get_by_role("link", name="My Notes").first
                        if not my_notes.count():
                            my_notes = page.get_by_text("My Notes", exact=True).first
                        if my_notes.count():
                            my_notes.click()
                            page.wait_for_timeout(2000)
                            opened = True
            except Exception as exc:
                print("menu navigation failed:", exc)
            if not opened:
                page.goto(
                    f"{BASE}/web#action=quick_sticky_notes.action_quick_sticky_note_my&model=quick.sticky.note&view_type=list",
                    wait_until="domcontentloaded",
                    timeout=60000,
                )
                page.wait_for_timeout(3000)
            dismiss_overlays(page)
            dbg(page, "mynotes")
            save_shot(page, "screenshot_mynotes.png")

            # Settings
            page.goto(f"{BASE}/odoo/settings", wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(3000)
            dismiss_overlays(page)
            try:
                search = page.locator(
                    'input[placeholder*="Search"], .o_searchview_input, input.o_searchview'
                ).first
                if search.count() and search.is_visible():
                    search.click()
                    search.fill("Quick Sticky")
                    page.wait_for_timeout(1500)
            except Exception:
                pass
            try:
                block = page.get_by_text("Quick Sticky Notes").first
                if block.count():
                    block.scroll_into_view_if_needed()
                    page.wait_for_timeout(700)
            except Exception:
                pass
            dbg(page, "settings")
            save_shot(page, "screenshot_settings.png")

            # Banner from main screenshot
            main = Image.open(OUT / "main_screenshot.png").convert("RGB")
            banner = main.resize((1280, 640), Image.Resampling.LANCZOS).convert("RGBA")
            overlay = Image.new("RGBA", banner.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)
            for y in range(400, 640):
                alpha = int(175 * (y - 400) / 240)
                draw.line([(0, y), (1280, y)], fill=(18, 22, 30, alpha))
            banner = Image.alpha_composite(banner, overlay)
            draw = ImageDraw.Draw(banner)
            try:
                font_title = ImageFont.truetype(
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 46
                )
                font_sub = ImageFont.truetype(
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22
                )
            except OSError:
                font_title = ImageFont.load_default()
                font_sub = font_title
            draw.text((44, 470), "Quick Sticky Notes", fill=(255, 255, 255, 255), font=font_title)
            draw.text(
                (44, 530),
                "Colorful private & shared notes on any Odoo record",
                fill=(235, 238, 245, 255),
                font=font_sub,
            )
            banner.convert("RGB").save(OUT / "banner.png", "PNG", optimize=True)
            print(f"Saved {OUT / 'banner.png'}")
            return 0
        except Exception:
            traceback.print_exc()
            try:
                dbg(page, "exception")
            except Exception:
                pass
            return 1
        finally:
            browser.close()


if __name__ == "__main__":
    raise SystemExit(main())
