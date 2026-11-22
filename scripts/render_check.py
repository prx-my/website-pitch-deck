"""Render a Slides-artifact deck locally with headless Chrome and build contact sheets (3 slides per image).

usage: python3 -I render_check.py <deck_root> <blob_map.json> <out_dir>
  deck_root     folder holding project/deck.json, project/deck.css, project/slides/*.html
  blob_map.json {"<asset id>": "path/to/local/image", ...} so /_blob/<id> srcs resolve offline
                (relative paths resolve against the json file's folder)
  out_dir       where <id>.png and sheet<N>.png are written

Set CHROME to your Chrome/Chromium binary if it isn't the macOS default.
Check every sheet: nothing may sit below y=920 except the footer row, and no text may overflow its box.
"""
import json, os, subprocess, sys
from PIL import Image

CHROME = os.environ.get("CHROME", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
BASE = """* { margin: 0 } body { font: 32px/1.2 sans-serif }
body > section { width: 1920px !important; height: 1080px !important; overflow: hidden !important; box-sizing: border-box !important; position: relative; isolation: isolate }
aside { display: none !important } h1{font-size:96px;font-weight:600} h2{font-size:64px;font-weight:600} h3{font-size:44px;font-weight:600}
p, li, h1, h2, h3, td, th { overflow-wrap: break-word; text-wrap: pretty }
table { width: 100%; border-collapse: separate; border-spacing: 0; border: solid #0003; border-width: 2px 0 0 2px }
th, td { padding: .35em .6em; text-align: left; border: solid #0003; border-width: 0 2px 2px 0 }"""

root, out = sys.argv[1], sys.argv[3]
map_dir = os.path.dirname(os.path.abspath(sys.argv[2]))
blob_map = {k: os.path.join(map_dir, v) for k, v in json.load(open(sys.argv[2])).items()}
os.makedirs(out, exist_ok=True)
deck = json.load(open(f"{root}/project/deck.json"))
css = open(f"{root}/project/deck.css").read()
fonts = "".join(f'<link rel="stylesheet" href="{f["href"]}">' for f in deck.get("faces", {}).values() if "href" in f)
pngs = []
for sid in deck["order"]:
    html = open(f"{root}/project/slides/{sid}.html").read()
    for k, v in blob_map.items():
        html = html.replace(f"/_blob/{k}", f"file://{v}")
    page = os.path.abspath(f"{out}/{sid}.html")  # file:// needs an absolute path
    open(page, "w").write(f"<!doctype html><html><head><meta charset=\"utf-8\">{fonts}<style>{BASE}\n{css}</style></head><body>{html}</body></html>")
    png = os.path.abspath(f"{out}/{sid}.png")
    if os.path.exists(png):
        os.remove(png)  # never let a stale image pass as a fresh render
    for _ in range(2):  # Chrome occasionally exits before writing; one retry is enough
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--allow-file-access-from-files",
                        "--virtual-time-budget=6000", "--window-size=1920,1080", f"--screenshot={png}", f"file://{page}"],
                       capture_output=True)
        if os.path.exists(png):
            break
    assert os.path.exists(png), f"render failed for slide {sid}"
    pngs.append(png)

for n in range(0, len(pngs), 3):
    sheet = Image.new("RGB", (960, 1640), "white")
    for i, p in enumerate(pngs[n:n + 3]):
        sheet.paste(Image.open(p).resize((960, 540)), (0, i * 550))
    sheet.save(f"{out}/sheet{n // 3}.png")
print("sheets:", [f"{out}/sheet{i}.png" for i in range((len(pngs) + 2) // 3)])
