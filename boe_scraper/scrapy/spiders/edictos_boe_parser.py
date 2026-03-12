import os
import re
from datetime import datetime

import scrapy

from boe_scraper.settings import settings


class EdictosBOEParserSpider(scrapy.Spider):
    name = "edictos_boe_parser"
    allowed_domains = ["www.boe.es"]
    pattern_obj = None

    async def start(self):
        date_str = getattr(self, "date")
        # Ensure date is stored on the instance for later use
        self.date = date_str
        date = datetime.strptime(date_str, "%Y-%m-%d")

        pattern = getattr(self, "pattern")
        self.pattern_obj = re.compile(pattern)

        # Cache parse_only and download directory setup
        self.parse_only = getattr(self, "parse_only", "True") == "True"
        download_path = settings.download_path
        self._download_dir = os.path.join(download_path, f"date={self.date}")
        os.makedirs(self._download_dir, exist_ok=True)

        url = (
            f"https://www.boe.es/boe_j/dias/{date.year}/{date.month:02d}/"
            f"{date.day:02d}/index.php?l=J"
        )
        yield scrapy.Request(url, callback=self.parse)

    def parse(self, response):
        yield from response.follow_all(css="li.puntoHTML a", callback=self.parse_edicto)

    def parse_edicto(self, response):
        parse_only = getattr(self, "parse_only", "True") == "True"

        header = response.css("dl dd::text").getall()
        if not header:
            return

        if not parse_only:
            reference = header[-1]
            # Use precomputed download directory
            file_path = os.path.join(self._download_dir, f"{reference}.html")
            with open(file_path, "wb") as f:
                f.write(response.body)

        # Use Scrapy's decoded text to avoid re-decoding the body
        text = response.text
        match = self.pattern_obj.search(text)
        if not match:
            return

        department = header[-2]
        reference_id = header[-1]
        yield {
            "department": department,
            "reference_id": reference_id,
            "date": self.date,
            "occurrence": " ".join(match.groups()),
        }
