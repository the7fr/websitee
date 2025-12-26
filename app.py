from flask import Flask, jsonify, render_template
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import threading
import time
import requests
import re
import os

app = Flask(__name__)

URL = "https://goldpump.com"
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")
ROLE_ID = os.getenv("ROLE_ID")

rain_data = {
    "active": False,
    "amount": None,
    "ends_at": None
}

def start_scraper():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )

    driver.get(URL)

    try:
        driver.find_element(By.CLASS_NAME, "chat-toggle").click()
        time.sleep(1)
    except:
        pass

    rain_sent = False

    while True:
        try:
            join = driver.find_elements(By.XPATH, "//span[contains(@class,'BaseElement') and text()='JOIN']")

            if join and not rain_sent:
                try:
                    el = driver.find_element(By.XPATH, '//*[@id="root"]/div[4]/div/div/div[2]/div/div[1]/div/div/div/div/div[2]/div/span')
                    amount = int(re.sub(r'\D', '', el.text))
                except:
                    amount = None

                ends = int(time.time()) + 119

                rain_data.update({
                    "active": True,
                    "amount": amount,
                    "ends_at": ends
                })

                requests.post(DISCORD_WEBHOOK, json={
                    "content": f"<@&{ROLE_ID}>",
                    "embeds": [{
                        "title": "🌧 Rain Started!",
                        "color": 0x3498db,
                        "fields": [
                            {"name": "💰 Amount", "value": f"``{amount:,}``" if amount else "Unknown", "inline": True},
                            {"name": "⏰ Ends in", "value": f"<t:{ends}:R>", "inline": True}
                        ]
                    }]
                })

                rain_sent = True

            if not join:
                rain_data["active"] = False
                rain_sent = False

        except:
            pass

        time.sleep(1)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/rain")
def rain():
    return jsonify(rain_data)

threading.Thread(target=start_scraper, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port)
