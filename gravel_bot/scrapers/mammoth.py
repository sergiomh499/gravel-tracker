"""
gravel_bot.scrapers.mammoth - Scraper para Mammoth Bikes
"""

import re
from typing import List, Dict, Any
from gravel_bot.scrapers.base import BaseScraper

class MammothScraper(BaseScraper):
    name = "mammoth"
    store_slug = "mammoth"
    store_name = "Mammoth Bikes"
    store_type = "online"
    base_url = "https://www.mammothbikes.com/bicicletas-gravel/c-3103"

    def scrape(self) -> List[Dict[str, Any]]:
        html_content = self.fetch_html(self.base_url)
        if not html_content:
            return []

        cards = re.split(r'<div\s+Class=\"card-content\">', html_content, flags=re.IGNORECASE)[1:]
        results = []

        for c in cards:
            link_m = re.search(r'<a[^>]*href=\"([^\"]+)\"', c)
            name_m = re.search(r'<div Class=\"card-product-name\">(.*?)</div>', c, re.DOTALL | re.IGNORECASE)
            disc_m = re.search(r'<span class=\"price is__discount\">([^<]+)</span>', c)
            std_m = re.search(r'<span class=\"price(?: is__final)?\">([^<]+)</span>', c)
            old_m = re.search(r'<span class=\"price is__old\">([^<]+)</span>', c)
            sizes_sec = re.search(r'<div Class=\"card--product-sizes[^\"]*\">(.*?)</div>', c, re.DOTALL | re.IGNORECASE)
            sizes = re.findall(r'<label>([^<]+)</label>', sizes_sec.group(1)) if sizes_sec else []

            if link_m and name_m:
                title = self.clean_text(name_m.group(1))
                link = link_m.group(1)
                if not link.startswith("http"):
                    link = "https://www.mammothbikes.com" + link

                price_raw = disc_m.group(1) if disc_m else (std_m.group(1) if std_m else "")
                old_raw = old_m.group(1) if old_m else price_raw

                price = self.clean_price(price_raw)
                pvp = self.clean_price(old_raw)
                if pvp == 0.0 or pvp < price:
                    pvp = price

                if price > 200:
                    results.append({
                        "title": title,
                        "price": price,
                        "pvp": pvp,
                        "discount_str": f"{round((pvp - price) / pvp * 100)}%" if pvp > price else "0%",
                        "sizes": [s.strip().upper() for s in sizes],
                        "url": link,
                        "store_slug": self.store_slug,
                        "store_name": self.store_name,
                        "store_type": self.store_type
                    })

        return results
