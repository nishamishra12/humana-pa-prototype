"""Turn a clean packet into a bad fax: a handwritten cover sheet, handwritten margin notes,
fax resolution, 1-bit black and white, skew, speckle and streaks. Image only, no text layer.

Run: python scripts/make_bad_fax.py <clean.pdf> <out.pdf>
"""
import os, random, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFont, ImageFilter

random.seed(7)
DPI = 200
INK = "C:/Windows/Fonts/Inkfree.ttf"


def hand(img, x, y, text, size=44, wobble=2.5):
    """Write text in a handwriting font, one word at a time, with a wobbly baseline and tilt."""
    font = ImageFont.truetype(INK, size)
    for word in text.split(" "):
        w = int(font.getlength(word)) + 12
        tile = Image.new("L", (w, size + 30), 255)
        ImageDraw.Draw(tile).text((4, 6), word, font=font, fill=random.randint(0, 50), stroke_width=1, stroke_fill=0)
        tile = tile.rotate(random.uniform(-wobble, wobble), fillcolor=255, expand=True)
        img.paste(tile, (int(x), int(y + random.uniform(-4, 4))), Image.eval(tile, lambda p: 255 - p))
        x += w + int(size * 0.18)
    return img


def cover_sheet(size):
    img = Image.new("L", size, 255)
    d = ImageDraw.Draw(img)
    big = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 64)
    small = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 30)
    d.text((140, 160), "FAX TRANSMITTAL", font=big, fill=0)
    d.text((140, 250), "Riverbend Bariatric Surgery Center", font=small, fill=0)
    rows = [("To:", "Humana UM / Prior Auth"), ("Fax:", "1-800-555-0199"), ("From:", "Sheila B. - auth coordinator"),
            ("Date:", "10/6/26"), ("Pages:", "7 incl. cover")]
    y = 380
    for lab, val in rows:
        d.text((140, y), lab, font=small, fill=0)
        d.line((330, y + 40, 1500, y + 40), fill=0, width=2)
        hand(img, 350, y - 18, val)
        y += 95
    d.text((140, y + 30), "Notes:", font=small, fill=0)
    d.rectangle((140, y + 80, 1520, y + 820), outline=0, width=2)
    notes = ["Pt: Denise Walker  DOB 2/23/1978",
             "Member ID MBR-41003",
             "Req: lap Roux-en-Y gastric bypass  CPT 43644",
             "BMI 45.9  -  T2DM, HTN, OSA on CPAP",
             "7 mo supervised diet program done 8/18",
             "Psych cleared 9/2.  Non-smoker.",
             "Please call 937-555-0120 w/ questions. Thx!"]
    for i, line in enumerate(notes):
        hand(img, 180, y + 110 + i * 95, line, size=46)
    d.text((140, size[1] - 220), "CONFIDENTIAL: This fax contains protected health information.", font=small, fill=0)
    d.text((140, size[1] - 170), "Made-up data for a software prototype. Not a real patient.", font=small, fill=0)
    return img


def fax_it(img, page_no, total):
    w, h = img.size
    img = img.point(lambda p: 0 if p < 200 else p)  # a fax machine darkens grey print instead of dropping it
    # fax resolution: 204 x 98 dpi standard mode, then back up to page size
    img = img.resize((int(w * 204 / DPI), int(h * 98 / DPI)), Image.BILINEAR).resize((w, h), Image.NEAREST)
    img = img.rotate(random.uniform(-1.6, 1.6), fillcolor=255, resample=Image.BILINEAR)
    img = img.filter(ImageFilter.GaussianBlur(0.8))
    px = img.load()
    for _ in range(int(w * h * 0.004)):  # speckle
        px[random.randrange(w), random.randrange(h)] = random.choice((0, 0, 255))
    d = ImageDraw.Draw(img)
    for _ in range(2):  # roller streaks
        x = random.randrange(w)
        d.line((x, 0, x + random.randint(-6, 6), h), fill=150, width=2)
    img = img.point(lambda p: 0 if p < 150 else 255).convert("1")  # 1-bit, like a real fax
    hdr = Image.new("1", (w, 60), 1)
    ImageDraw.Draw(hdr).text((30, 12), f"OCT-06-2026 14:3{page_no % 10}  FROM: RIVERBEND BARIATRIC  9375550121    TO: HUMANA UM    P.{page_no:03d}/{total:03d}",
                             font=ImageFont.truetype("C:/Windows/Fonts/cour.ttf", 30), fill=0)
    img.paste(hdr, (0, 0))
    return img


def main(src, out):
    tmp = tempfile.mkdtemp()
    subprocess.run(["pdftoppm", "-r", str(DPI), "-gray", "-png", src, os.path.join(tmp, "p")], check=True)
    pages = [Image.open(os.path.join(tmp, f)).convert("L") for f in sorted(os.listdir(tmp))]
    # handwritten notes on the clinical pages
    hand(pages[1], 160, 1650, "seen 9/21 - wt 276 confirmed. A.R.", size=44)
    hand(pages[3], 160, 1000, "cleared - SL 9/2", size=44)
    hand(pages[5], 160, 1050, "Alan Reyes MD", size=60, wobble=6)
    pages = [cover_sheet(pages[0].size)] + pages
    faxed = [fax_it(p, i + 1, len(pages)) for i, p in enumerate(pages)]
    faxed[0].save(out, save_all=True, append_images=faxed[1:], resolution=DPI)
    print("wrote", out, len(faxed), "pages, image only")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
