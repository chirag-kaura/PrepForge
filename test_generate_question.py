import asyncio
import time

from playwright.async_api import async_playwright


URL = "https://prepforge-3xvw.onrender.com"


async def generate_question(browser, user_number):
    context = await browser.new_context()
    page = await context.new_page()

    await page.goto(URL, wait_until="networkidle")

    start_time = time.perf_counter()

    old_question = await page.locator('[data-testid="stAlert"]').inner_text()

    await page.get_by_text("Generate Question", exact=True).click()

    await page.wait_for_function(
        """old => {
            const alerts = document.querySelectorAll('[data-testid="stAlert"]');
            return alerts.length > 0 && alerts[0].innerText !== old;
        }""",
        arg=old_question,
    )

    latency = time.perf_counter() - start_time

    await context.close()

    return user_number, latency


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        start = time.perf_counter()

        results = await asyncio.gather(
            *[
                generate_question(browser, user_number)
                for user_number in range(1, 6)
            ]
        )

        total_time = time.perf_counter() - start

        await browser.close()

    for user_number, latency in results:
        print(f"User {user_number}: {latency:.2f}s")

    print(f"Total test time: {total_time:.2f}s")


asyncio.run(main())