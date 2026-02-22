import asyncio
import os
import re
import shutil
from pathlib import Path

try:
    from dotenv import load_dotenv
    from playwright.async_api import async_playwright
except ImportError as exc:
    raise SystemExit(
        "Missing dependencies. Install with: "
        "pip install playwright python-dotenv && playwright install chromium"
    ) from exc


AI_STUDIO_LIVE_URL = "https://aistudio.google.com/live"

SERVER_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SERVER_DIR.parent

with open(PROJECT_ROOT / "system_instructions.txt", "r", encoding="utf-8") as f:
    TARGET_SYSTEM_INSTRUCTIONS_TEXT = f.read().strip()


def get_chromium_executable() -> str | None:
    override = os.getenv("CHROMIUM_EXECUTABLE", "").strip()
    if override and Path(override).exists():
        return override

    candidates = [
        Path("/usr/bin/chromium-browser"),
        Path("/usr/bin/chromium"),
        Path("/snap/bin/chromium"),
        Path(os.environ.get("PROGRAMFILES", r"C:\\Program Files")) / "Google/Chrome/Application/chrome.exe",
        Path(os.environ.get("PROGRAMFILES(X86)", r"C:\\Program Files (x86)"))
        / "Google/Chrome/Application/chrome.exe",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Google/Chrome/Application/chrome.exe",
    ]
    for bin_name in ("chromium-browser", "chromium"):
        found = shutil.which(bin_name)
        if found:
            return found
    for path in candidates:
        if path.exists():
            return str(path)
    return None


def is_sign_in_url(url: str) -> bool:
    lowered = url.lower()
    return "accounts.google.com" in lowered or "servicelogin" in lowered or "signin" in lowered


async def is_sign_in_visible(page) -> bool:
    candidates = [
        page.get_by_role("button", name=re.compile("sign in", re.I)).first,
        page.get_by_role("link", name=re.compile("sign in", re.I)).first,
        page.get_by_text(re.compile(r"^sign in$", re.I)).first,
    ]
    for candidate in candidates:
        try:
            if await candidate.is_visible(timeout=400):
                return True
        except Exception:
            continue
    return False


async def wait_for_manual_login(page) -> None:
    print("ACTION REQUIRED: Please log in manually in the opened browser window.")
    while is_sign_in_url(page.url) or await is_sign_in_visible(page):
        await page.wait_for_timeout(1500)
    if "/live" not in page.url:
        await page.goto(AI_STUDIO_LIVE_URL, wait_until="domcontentloaded")
        await page.wait_for_timeout(1200)


async def open_run_settings(page) -> bool:
    if await page.get_by_text(re.compile(r"^System instructions$", re.I)).first.is_visible(timeout=500):
        return True

    opener_candidates = [
        page.get_by_role("button", name=re.compile(r"run settings", re.I)).first,
        page.locator(
            "xpath=(//button[contains(translate(@aria-label,'RUN SETTINGS','run settings'),'run settings')])[1]"
        ).first,
        page.locator(
            "xpath=(//*[@role='button' and contains(translate(@aria-label,'RUN SETTINGS','run settings'),'run settings')])[1]"
        ).first,
    ]
    for opener in opener_candidates:
        try:
            if await opener.is_visible(timeout=700):
                await opener.click(timeout=1200)
                await page.wait_for_timeout(350)
                if await page.get_by_text(re.compile(r"^System instructions$", re.I)).first.is_visible(timeout=800):
                    return True
        except Exception:
            continue
    return False


async def create_system_instruction(page, text: str) -> bool:
    if not text:
        return False
    if not await open_run_settings(page):
        return False

    section = page.get_by_text(re.compile(r"^System instructions$", re.I)).first
    try:
        await section.wait_for(state="visible", timeout=3000)
        await section.click(timeout=1200)
        await page.wait_for_timeout(300)
    except Exception:
        return False

    open_create_candidates = [
        page.get_by_role("combobox", name=re.compile(r"create new instruction", re.I)).first,
        page.get_by_role("button", name=re.compile(r"create new instruction", re.I)).first,
        page.get_by_text(re.compile(r"^\+?\s*create new instruction$", re.I)).first,
    ]
    for opener in open_create_candidates:
        try:
            if await opener.is_visible(timeout=700):
                await opener.click(timeout=1200)
                await page.wait_for_timeout(250)
                break
        except Exception:
            continue

    create_new_candidates = [
        page.get_by_role("option", name=re.compile(r"^\+?\s*create new instruction$", re.I)).first,
        page.get_by_role("menuitem", name=re.compile(r"^\+?\s*create new instruction$", re.I)).first,
        page.get_by_text(re.compile(r"^\+?\s*create new instruction$", re.I)).first,
    ]
    for candidate in create_new_candidates:
        try:
            if await candidate.is_visible(timeout=900):
                await candidate.click(timeout=1200)
                await page.wait_for_timeout(250)
                break
        except Exception:
            continue

    input_candidates = [
        page.get_by_role("textbox", name=re.compile(r"instruction|prompt|system", re.I)).first,
        page.get_by_label(re.compile(r"instruction|prompt|system", re.I)).first,
        page.locator("textarea").last,
        page.locator("[contenteditable='true']").last,
    ]
    wrote = False
    for field in input_candidates:
        try:
            await field.wait_for(state="visible", timeout=1800)
            await field.click(timeout=1000)
            tag_name = await field.evaluate("el => (el.tagName || '').toLowerCase()")
            is_editable = await field.evaluate("el => !!el.isContentEditable")
            if tag_name in {"textarea", "input"}:
                await field.fill("", timeout=1000)
                await field.fill(text, timeout=2400)
            elif is_editable:
                await page.keyboard.press("Control+A")
                await page.keyboard.type(text, delay=0)
            else:
                continue
            wrote = True
            await page.wait_for_timeout(250)
            break
        except Exception:
            continue
    if not wrote:
        return False

    close_candidates = [
        page.get_by_role("button", name=re.compile(r"close|schlie", re.I)).first,
        page.locator(
            "xpath=(//*[normalize-space()='System instructions']/following::*[self::button or @role='button'][1])[1]"
        ).first,
        page.locator(
            "xpath=//*[normalize-space()='System instructions']/following::*[normalize-space()='\u00d7'][1]"
        ).first,
    ]
    for close in close_candidates:
        try:
            if await close.is_visible(timeout=700):
                await close.click(timeout=1200)
                await page.wait_for_timeout(200)
                break
        except Exception:
            continue
    return True


async def click_talk(page) -> bool:
    candidates = [
        page.get_by_role("button", name=re.compile(r"^talk$", re.I)).first,
        page.locator("button:has-text('Talk')").first,
    ]
    for candidate in candidates:
        try:
            await candidate.wait_for(state="visible", timeout=4000)
            await candidate.click(timeout=2000)
            return True
        except Exception:
            continue
    return False


async def run() -> None:
    load_dotenv(PROJECT_ROOT / ".env")
    load_dotenv(SERVER_DIR / ".env")

    user_data_dir = SERVER_DIR / "user_data"
    user_data_dir.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        launch_kwargs = {
            "headless": False,
            "args": [
                "--use-fake-ui-for-media-stream",
                "--ignore-certificate-errors",
                "--disable-blink-features=AutomationControlled",
            ],
            "permissions": ["microphone", "camera"],
        }

        chromium_executable = get_chromium_executable()
        if chromium_executable:
            launch_kwargs["executable_path"] = chromium_executable

        context = await p.chromium.launch_persistent_context(str(user_data_dir), **launch_kwargs)
        page = context.pages[0] if context.pages else await context.new_page()

        try:
            await page.goto(AI_STUDIO_LIVE_URL, wait_until="domcontentloaded")
            await page.wait_for_timeout(1200)

            if is_sign_in_url(page.url) or await is_sign_in_visible(page):
                await wait_for_manual_login(page)

            if await create_system_instruction(page, TARGET_SYSTEM_INSTRUCTIONS_TEXT):
                print("System instructions created and configured.")
            else:
                print("Could not create system instructions.")

            if await click_talk(page):
                print("Talk control activated.")
            else:
                print("Could not find Talk control.")
                await page.screenshot(path=str(SERVER_DIR / "last_failure.png"), full_page=True)

            print("Script is running. Press Ctrl+C to stop.")
            while True:
                await asyncio.sleep(60)
        finally:
            await context.close()


if __name__ == "__main__":
    asyncio.run(run())
