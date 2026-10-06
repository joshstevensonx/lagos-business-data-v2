from pathlib import Path

from lagosdata.sources.directories.finelib import FinelibSource


def test_finelib_area_listing_fixture():
    html = (Path(__file__).parent / 'fixtures/finelib/area.html').read_text()
    rows = FinelibSource().parse(html, 'https://www.finelib.com/cities/lagos/areas-and-suburbs/anthony-village')
    assert rows == [{
        'name': 'Apostolic Faith Secondary School',
        'addr': '1, Apostolic Faith Campground Road, Anthony Village, Lagos',
        'phone': '+234-8037130271',
        'source': 'Finelib',
        'source_url': 'https://www.finelib.com/listing/Apostolic-Faith-Secondary-School/26175/',
    }]
