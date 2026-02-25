import re
from datetime import datetime
from posixpath import join as urljoin

import scrapy

from boe_scraper.settings import settings
from boe_scraper.utils.writter import fsopen


class EdictosBOEParserSpider(scrapy.Spider):
    name = "edictos_boe_parser"
    allowed_domains = ["www.boe.es"]
    pattern_obj = None

    async def start(self):
        dates_str = getattr(self, "dates")
        # Ensure date is stored on the instance for later use
        dates = []
        for date_str in dates_str.split(","):
            dates.append(datetime.strptime(date_str, "%Y-%m-%d"))

        pattern = getattr(self, "pattern")
        self.pattern_obj = re.compile(pattern)
        # Cache parse_only and download directory setup
        self.parse_only = getattr(self, "parse_only", "True") == "True"
        self._download_dir = settings.download_path

        for date in dates:
            url = (
                f"https://www.boe.es/boe_j/dias/{date.year}/{date.month:02d}/"
                f"{date.day:02d}/index.php?l=J"
            )
            yield scrapy.Request(url, callback=self.parse, meta={"date": date})

    def parse(self, response):
        date = response.meta["date"]
        yield from response.follow_all(
            css="li.puntoHTML a", callback=self.parse_edicto, meta={"date": date}
        )

    def parse_edicto(self, response):
        date = response.meta["date"]
        parse_only = getattr(self, "parse_only", "True") == "True"

        header = response.css("dl dd::text").getall()
        if not header:
            return

        if not parse_only:
            reference = header[-1]
            # Use precomputed download directory
            file_path = urljoin(
                self._download_dir,
                f"date={date.year}-{date.month:02d}-{date.day:02d}",
                f"{reference}.html",
            )
            with fsopen(file_path, "wb") as f:
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
