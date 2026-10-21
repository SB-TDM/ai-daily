MAX_IMAGE_BYTES = 2_097_152

def accept_image(png: bytes) -> bytes:
    if not png.startswith(b"\x89PNG") or len(png) > MAX_IMAGE_BYTES:
        raise RuntimeError("image rejected")
    return png

def screenshot_html(html: str) -> bytes:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 780, "height": 1280})
        page.set_content(html, wait_until="load")
        png = page.screenshot(full_page=True, type="png")
        browser.close()
    return accept_image(png)
