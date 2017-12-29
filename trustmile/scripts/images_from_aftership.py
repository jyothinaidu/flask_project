from app.deliveries.model import Courier
import cairosvg
import requests
import PIL
from PIL import Image

couriers = Courier.query.all()
asset_url_base = 'https://assets.aftership.com/couriers/svg/'
for c in couriers:
    slug = c.courier_slug
    url = asset_url_base + slug + '.svg'
    resp = requests.get(url)
    filename = './pngs/' + slug + '.png'
    file_output = open(filename, 'w')

    cairosvg.svg2png(bytestring=resp.content, write_to=file_output)

    file_output.close()

    img = Image.open(filename)
    img = img.resize((50, 50), PIL.Image.ANTIALIAS)
    img.save('./pngs/' + slug + '50x50' + '.png')
