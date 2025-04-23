import json
import time
import datetime
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import undetected_chromedriver as uc

# Load URLs from urls.json
with open('urls.json', 'r') as f:
    sites = json.load(f)

# Setup Selenium browser
options = uc.ChromeOptions()
options.headless = True
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
driver = uc.Chrome(options=options)

results = {
    "run_time": datetime.datetime.now(datetime.timezone.utc).isoformat() + "Z",
    "total_sites": len(sites),
    "passed": [],
    "failed": [],
    "warnings": []
}

for site in sites:
    url = site["url"]
    label = site.get("label", url)
    alert = site.get("alert", True)

    try:
        start = time.time()
        driver.get(url)
        load_time = round(time.time() - start, 2)

        # Check for visible text content
        visible_elements = driver.find_elements("xpath", "//*[string-length(normalize-space()) > 30]")
        has_visible_content = len(visible_elements) > 0

        # Check for Gravity Forms indicator
        page_source = driver.page_source
        has_gravity_form = "form_id=" in page_source

        # Check console errors
        console_errors = [log for log in driver.get_log("browser") if log["level"] in ["SEVERE", "ERROR"]]

        if not has_visible_content and not has_gravity_form:
            results["failed"].append({
                "url": url,
                "label": label,
                "reason": "No meaningful content or Gravity Form found",
                "load_time": load_time
            })
        elif console_errors:
            results["failed"].append({
                "url": url,
                "label": label,
                "reason": "JavaScript console errors",
                "errors": console_errors,
                "load_time": load_time
            })
        elif load_time > 5:
            results["warnings"].append({"url": url, "label": label, "load_time": load_time})
        else:
            results["passed"].append({"url": url, "label": label, "load_time": load_time})

    except Exception as e:
        results["failed"].append({"url": url, "label": label, "error": str(e)})

# Save output log
os.makedirs("logs", exist_ok=True)
outfile = f"logs/output_{datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d_%H-%M-%S')}.json"
with open(outfile, 'w') as f:
    json.dump(results, f, indent=2)

print("Check complete. Results saved to:", outfile)

driver.quit()

