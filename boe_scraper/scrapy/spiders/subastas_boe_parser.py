import os
from datetime import datetime
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

from scrapy import Request, Spider
from scrapy.http.response import Response

from boe_scraper.settings import settings
from boe_scraper.utils.string_normalization import (
    parse_euro_amount,
    to_snake_no_accents,
)


class SubastasBOEParserSpider(Spider):
    name = "subastas_boe_parser"
    allowed_domains = ["subastas.boe.es"]

    async def start(self):
        cod_provincia = getattr(self, "cod_provincia")
        if not cod_provincia:
            raise ValueError("'cod_provincia' must be set")
        from_start_date = getattr(self, "from_start_date", "")
        to_start_date = getattr(self, "to_start_date", "")
        # Ensure date is stored on the instance for later use
        self.cod_provincia = int(cod_provincia)
        # Cache parse_only and download directory setup
        self.parse_only = getattr(self, "parse_only", "True") == "True"
        self._download_dir = settings.download_path
        os.makedirs(self._download_dir, exist_ok=True)
        query_params = {
            "campo[2]": "SUBASTA.ESTADO.CODIGO",
            "dato[2]": "EJ",
            "campo[3]": "BIEN.TIPO",
            "dato[3]": "I",  # Inmueble
            "dato[4]": "501",  # Vivienda
            "campo[8]": "BIEN.COD_PROVINCIA",
            "dato[8]": str(self.cod_provincia),
            "campo[18]": "SUBASTA.FECHA_INICIO",
            "dato[18][0]": from_start_date,
            "dato[18][1]": to_start_date,
            "page_hits": 100,
            "sort_field[0]": "SUBASTA.FECHA_FIN",
            "sort_order[0]": "desc",
            "accion": "Buscar",
        }
        encoded_query_params = urlencode(query_params)
        url = f"https://subastas.boe.es/subastas_ava.php?{encoded_query_params}"
        yield Request(
            url,
            callback=self.parse_search,
            # cookies={"SESSID": "05227cb03eb697b200296af690d474"},
        )

    def parse_search(self, response: Response) -> None:
        # Parse elements in first page
        # Just call parse_search_page for DRY code
        yield from self.parse_search_page(response)
        # Parse elements in the other pages
        other_pages_links = response.css("div.paginar2 a::attr(href)").getall()
        if len(other_pages_links) > 1:
            for link in other_pages_links[:-1]:
                yield response.follow(link, callback=self.parse_search_page)

    def parse_search_page(self, response: Response):
        css_query = "li.puntoHTML a"
        yield from response.follow_all(css=css_query, callback=self.parse_auction)

    def parse_table(self, response: Response, css_query: str):
        result = {}
        for row in response.css(css_query):
            key = row.css("th::text").get()
            value = " ".join(row.css("td ::text").getall()).strip()
            if key:
                result[to_snake_no_accents(key.strip())] = value
        return result

    def parse_auction(self, response: Response):

        # Parse general information
        auction = self.parse_table(response, "#idBloqueDatos1 table tr")

        # Transform fields expected to be a € amount
        euro_fields = [
            "cantidad_reclamada",
            "puja_minima",
            "valor_subasta",
            "tasacion",
            "tramos_entre_pujas",
            "importe_del_deposito",
        ]
        for euro_field in euro_fields:
            if euro_field in auction and auction[euro_field].endswith("€"):
                auction[euro_field] = parse_euro_amount(auction[euro_field])
            else:
                auction[euro_field] = None
        try:
            auction["lotes"] = int(auction["lotes"])
        except ValueError:
            auction["lotes"] = 1

        date_fields = ["fecha_de_inicio", "fecha_de_conclusion"]
        for date_field in date_fields:
            value = auction[date_field]
            dt = datetime.strptime(value[:19], "%d-%m-%Y %H:%M:%S").replace(
                tzinfo=ZoneInfo("Europe/Madrid")  # CET/CEST with DST (+01/+02)
            )
            auction[date_field] = dt

        documents = response.css("div.caja.gris ul.enlaces li.puntoPDF a")
        auction["documents"] = []
        for doc in documents:
            name = doc.css("::text").get()
            link = doc.css("::attr(href)").get()
            auction["documents"].append({"name": name, "link": response.urljoin(link)})

        images = response.css("div.caja.gris ul.enlaces li:not(.puntoPDF) a")
        auction["images"] = []
        for image in images:
            link = image.css("::attr(href)").get()
            auction["images"].append({"link": response.urljoin(link)})

        tab2_link = response.css("ul.navlist li:nth-child(2) a::attr(href)").get()
        yield response.follow(
            tab2_link,
            callback=self.parse_authority,
            meta={"auction": auction},  # pass data forward
        )

    def parse_authority(self, response: Response):
        auction: dict = response.meta["auction"]
        authority_information = self.parse_table(response, "#idBloqueDatos2 table tr")
        auction.update(authority_information)
        tab3_link = response.css("ul.navlist li:nth-child(3) a::attr(href)").get()
        if auction["lotes"] == 1:
            yield response.follow(
                tab3_link,
                callback=self.parse_assets,
                meta={"auction": auction},  # pass data forward
            )
        else:
            auction["assets"] = []
            yield response.follow(
                tab3_link,
                callback=self.parse_batch,
                meta={"auction": auction},  # pass data forward
            )

    def parse_assets(self, response: Response):
        auction: dict = response.meta["auction"]
        assets_information = self.parse_table(response, "#idBloqueLote1 table tr")
        for field in [
            "cantidad_reclamada",
            "puja_minima",
            "valor_subasta",
            "tasacion",
            "tramos_entre_pujas",
            "importe_del_deposito",
        ]:
            assets_information[field] = auction[field]
        auction["assets"] = [assets_information]
        yield auction

    def parse_batch(self, response: Response):
        auction: dict = response.meta["auction"]
        # Current block
        current_batch = response.css("div.bloque[id^='idBloqueLote']")
        block_id = current_batch.attrib.get("id")

        asset = {}

        # title/description
        title = current_batch.css("div.caja::text").get(default="").strip()
        asset = {"title": title}

        # auction related data
        auction_data = self.parse_table(
            current_batch, "h3:contains('Datos relacionados') + table tr"
        )
        asset.update(auction_data)

        # property data
        property_data = self.parse_table(current_batch, "h4 + table tr")
        asset.update(property_data)
        asset["tasacion"] = asset["valor_de_tasacion"]
        asset.pop("valor_de_tasacion")
        euro_fields = [
            "cantidad_reclamada",
            "puja_minima",
            "valor_subasta",
            "tasacion",
            "tramos_entre_pujas",
            "importe_del_deposito",
        ]
        for euro_field in euro_fields:
            if euro_field in asset and asset[euro_field].endswith("€"):
                asset[euro_field] = parse_euro_amount(asset[euro_field])
            else:
                asset[euro_field] = None

        auction["assets"].append(asset)

        index = int(block_id.replace("idBloqueLote", ""))
        next_batch_link = response.css(f"a#idTabLote{index + 1}::attr(href)").get()
        if not next_batch_link:
            yield auction

        else:
            yield response.follow(
                next_batch_link,
                callback=self.parse_batch,
                meta={"auction": auction},  # pass data forward
            )
