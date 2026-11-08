"""Render the share preview as a simple, readable typography card."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
root = Path(__file__).resolve().parents[1]
im = Image.new('RGB', (1200, 630), '#0c1d29')
d = ImageDraw.Draw(im)
fontdir = Path('/System/Library/Fonts/Supplemental')
def font(size, bold=False):
    return ImageFont.truetype(str(fontdir / ('Arial Bold.ttf' if bold else 'Arial.ttf')), size)
def text(x,y,value,size=24,color='#fffaf0',bold=False):
    d.text((x,y),value,font=font(size,bold),fill=color)
d.rounded_rectangle((26,26,1174,604), radius=24, outline='#b99651',width=2)
text(66,58,'TCSO',38,'#efd99f',True)
text(66,108,'THIRD-COUNTRY SUPPORTERS ORGANIZATION',16,'#c3ced0')
text(66,161,'Your community. More possibilities.',48,bold=True)
text(66,229,'Learn, connect and grow with TCSO membership.',25,'#c3ced0')
for x,label,cost,detail in [(66,'FREE MEMBER','US$0','Community + subscription benefits'),(616,'COMMUNITY SUPPORTER','US$30','One-time membership fee · Not monthly')]:
    d.rounded_rectangle((x,296,x+518,500),radius=18,fill='#f5ecd6')
    text(x+26,320,label,19,'#294a3f',True)
    text(x+26,357,cost,58,'#0c1d29',True)
    text(x+26,439,detail,22,'#294a3f')
text(66,543,'Explore benefits, durations and apply',24,'#efd99f',True)
text(845,545,'tcso.world/membership',21,'#fffaf0')
im.save(root/'assets/tcso-membership-preview.png',optimize=True)
