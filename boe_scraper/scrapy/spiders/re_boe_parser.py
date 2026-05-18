import os
import re
from datetime import datetime

import scrapy

from boe_scraper.settings import settings


class BOEReParserSpider(scrapy.Spider):
    name = "re_boe_parser"
    pattern_obj = None

    @classmethod
    def update_settings(cls, settings):
        super().update_settings(settings)
        # Local file:// reads are I/O bound; higher concurrency speeds things up
        settings.set("CONCURRENT_REQUESTS", 128, priority="spider")

    async def start(self):
        pattern = getattr(self, "pattern", "")
        self.pattern_obj = re.compile(pattern)
        download_path = settings.download_path
        for directory in os.listdir(download_path):
            if directory.startswith("date="):
                date = datetime.strptime(directory.split("=")[1], "%Y-%m-%d").date()
                folder_path = os.path.join(download_path, directory)
                files = [
                    os.path.join(folder_path, f)
                    for f in os.listdir(folder_path)
                    if os.path.isfile(os.path.join(folder_path, f))
                ]
                # Schedule all files at once so Scrapy can process them in parallel
                for path in files:
                    yield scrapy.Request(
                        f"file://{path}",
                        self.parse,
                        dont_filter=True,
                        meta={"date": date},
                    )

    def parse(self, response):
        date = response.meta["date"]
        # response.text uses Scrapy's encoding; avoid decoding the same body twice
        text = response.text
        match = self.pattern_obj.search(text)
        if match:
            header = response.css("dl dd::text").getall()
            department = header[-2]
            reference_id = header[-1]
            yield {
                "department": department,
                "reference_id": reference_id,
                "date": date,
                "occurrence": match.group(0),
            }
