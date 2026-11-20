---
name: website-pitch-deck
description: Build a web-agency sales pitch deck from a prospect's website URL, or from their Facebook page or listing when they have no website (optionally with notes or voice notes about the prospect). Researches the live site, captures real screenshots, scores it, and publishes a slide deck that shows where the site falls short and what the new site would do instead. Use when the user sends a business website and asks for a pitch deck, sales deck, audit deck or teardown deck.
---

# Website pitch deck

You build a sales deck for a web agency pitching a **new website** to a local business. Every slide shows the prospect, with their own screenshots and checkable numbers, where their current site falls short and what the new site does about it.

`<skill-dir>` below means the folder this file is in (usually `~/.claude/skills/website-pitch-deck`).

- `agency.md` in `<skill-dir>` holds the agency's name, presenter, contact details, accent colour and proof points. If it's missing, copy `agency.example.md`, ask the user for the real values, and do not publish a deck with the example's placeholder agency.
- `reference/` is a finished 11-slide deck for a **fictional** roofing company (`deck.json`, `deck.css`, `slides/*.html`). Use its CSS and markup as the template. Its `/_blob/ASSET_*` image names are placeholders: replace them with your own uploads.
- `scripts/cdp-shot.mjs` captures section screenshots; `scripts/render_check.py` renders the deck locally so you can catch overflow before publishing.

## What the deck must do

- **Core sell:** the new website (real pages behind every menu link, a page per town and service, FAQ, reviews, accessibility and speed scores, local SEO).
- **Gaps, not praise.** No slides crediting what already works. The one exception: a report-card row marked as a pass when a metric really is good (for example page speed), because claiming otherwise gets caught.
- **Optional add-ons** get one slide, clearly titled "Optional add-on" (e.g. an AI receptionist for after-hours calls). The deck never leans on them.
- **Next step:** a free homepage mockup in the prospect's colours, run through the same Lighthouse test as their live site, plus a short strategy call.

## Inputs

1. The prospect's URL (required).
2. Notes from the user or their team. Voice notes (`.ogg`, `.m4a`, `.mp3`) can be transcribed locally with whisper.cpp and any English ggml model (find one with `find ~ -name 'ggml-*.en.bin' 2>/dev/null`):
   ```bash
   ffmpeg -loglevel error -y -i "<note>" -ar 16000 -ac 1 note.wav
   whisper-cli -m <model.bin> -f note.wav -nt -np 2>/dev/null
   ```
   Anything the notes say the agency already promised the prospect ("every menu link gets its own page", "we'll add an FAQ", "keep his colours") must show up in the deck.
3. The prospect owner's first name, for "Prepared for …". Never invent staff names.
4. Which offers are confirmed. An unconfirmed offer stays as a visible `[CONFIRM: …]` placeholder.

## Step 1: research the live site (facts only)

Keep a fact sheet with the source of every fact. Work in a scratch folder.

- **Homepage HTML** (`curl -sSL <url>`): menu links in `<header>` (how many are `#anchors` that only scroll the homepage vs real pages), H1 and hero wording, whether the phone number shows digits or only an icon, FAQ or `FAQPage` schema, the reviews block (rating? count? dates?), the booking widget (how many copies), hours, and trust proof (warranty, manufacturer certification, financing, BBB, licence).
- **Sitemap** (`curl -sSL <url>/sitemap.xml | grep -oE '<loc>[^<]+'`): build the **town × service grid** showing which combinations have a page, plus odd pages (out-of-area towns, recruiting pages).
- **Brand:** exact hex colours from the compiled CSS (`:root` variables, button and CTA classes, `<meta name="theme-color">`), fonts from the Google Fonts `<link>`, and the logo URL.
- **Scores:** Lighthouse mobile, twice. If Google PageSpeed Insights is rate-limited, run Lighthouse locally and label every score "local Lighthouse mobile run". If SEO or Best Practices score 100, say so: they're technical checks, so the deck must not call them weak.
- **Listings and reviews:** Google rating and count if findable, plus Yelp, Angi/HomeAdvisor, Houzz, BBB and Facebook. Note conflicting hours. Never invent a rating: if you can't find one, write "Not found in our check".
- **Competitors (3–6 local):** displayed rating and count with the source labelled ("As displayed", "Places data", "Own site claim"), plus 24/7 claims, warranties and certifications.
- **AI-answer check:** ask an AI search tool for the service in the home town and in 3 neighbouring towns, and record who gets named. Always label it "Indicative checks, not Google rankings".
- **Unverified list:** anything you couldn't confirm goes in the speaker notes and on the sources slide, never on a slide as fact.

## Step 2: screenshots

Full-viewport shots with headless Chrome (macOS path shown; use your Chrome or Chromium binary elsewhere):

```bash
C="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
"$C" --headless=new --disable-gpu --hide-scrollbars --virtual-time-budget=15000 --window-size=1440,900 --screenshot=shots/hero-desktop.png <url>
```

Section crops (reviews block, footer hours, claim or FAQ boxes, mobile header):

```bash
"$C" --headless=new --disable-gpu --hide-scrollbars --remote-debugging-port=9333 --user-data-dir=chrome-prof about:blank >/dev/null 2>&1 &
node <skill-dir>/scripts/cdp-shot.mjs 9333 <url> 1440 900 0 shots '[{"name":"reviews","text":"Reviews","up":3,"maxH":1400},{"name":"footer","text":"AM","tag":"footer","pad":0}]'
node <skill-dir>/scripts/cdp-shot.mjs 9333 <url> 390 844 1 shots '[{"name":"mobile-top","viewport":true}]'
kill %1
```

Look at every shot before using it. Crop and resize with Pillow, keep JPGs around 250 KB, cut the menu bar as a thin strip (`crop((80,0,1360,72))` of the 1440-wide shot), and download the prospect's logo (convert webp to png).

Frames worth having: desktop hero, mobile hero with header and sticky bar, menu bar, reviews block, footer hours and contact, booking widget, any claim or FAQ box, before/after gallery.

## Step 3: build the deck

**In Claude Code with Artifacts (the Slides type):**
1. `Artifact` `action:"quickstart"` with `intent:"slides"` and `design_systems:false`, since the prospect's own brand is the look. Create the deck from the returned Slides `type_url` with a `title` and `auto_open:"after_first_write"`, then follow the type's own instructions: files under `project/`, `deck.json` first with the full `order`, then `deck.css` with the cover, then three slides per publish.
2. Upload assets with `Artifact` publish (`url`, `asset:true`, `file_paths:[…]`) and use each returned `/_blob/<id>` exactly as given.

**Without Artifacts:** the same `deck.css` and slide files render as plain HTML at 1920×1080 per `<section>`. Use `scripts/render_check.py` to get PNGs, then assemble a PDF.

**Look:**
- Fonts: the prospect's heading and body Google Fonts go in `deck.json` `faces`. The example uses Barlow Condensed with Inter.
- `deck.css`: start from `reference/deck.css` and swap in the prospect's palette:
  - **Dark brand colour:** cover and closing band.
  - **CTA colour:** "missing".
  - **Primary blue:** "what we do".
  - **Green:** only for a genuine pass.
- The agency accent from `agency.md` appears only on the footer mark and the closing CTA button.

### Slide structure (11 slides; adapt, but keep this spine)

| # | id | Title pattern (uppercase, at most 2 lines at 72px) | Visual |
|---|----|------|------|
| 1 | cover | "Where your website falls short, and the site we'll build instead" | Dark brand background, both logos, "Prepared for <Owner> · <Company> · <Month Year>" |
| 2 | report | "Your website's report card" | Table with columns Area / today / the new site. Today is red, or green for a true pass; the new site is blue. 8–10 rows: speed, accessibility, menu, town × service pages, FAQ, reviews, trust proof, hours, AI answers |
| 3 | menu | "Your menu scrolls the homepage instead of opening pages" (when true) | Menu-bar screenshot + table: link / today / new site |
| 4 | coverage | "Only N of M town-and-service pages exist" | Grid table of towns × services, "Page" (green) / "No page" (red) |
| 5 | homepage | The real hero problem, e.g. "Your homepage speaks to one kind of job" | Desktop hero screenshot with a red flag + strip of what competitors show |
| 6 | reviews | e.g. "Neighbours show stars. You show undated quotes." | Reviews-block screenshot + strip: prospect vs 3 competitors, each source labelled |
| 7 | scores | "The scores we'll build the new site to" | 4 cards (Performance, Accessibility, Best Practices, SEO): today vs "Target: 100"; what costs points; "your mockup goes through the same test" |
| 8 | nearby | "In N neighbouring towns, AI answers name someone else" | Table town / AI answer + "Named instead" strip |
| 9 | addon | "Optional add-on: …" | Evidence screenshot + problem / optional add-on |
| 10 | offer | "The new <domain>" | Included in the new site / Optional add-on; dark band with the next step, CTA button, presenter contact, both logos, agency proof |
| 11 | sources | "Sources" | Pages checked and when, competitors, agency pages, benchmarks, "Not verified" |

Slides 3–9 share one layout. The left side (860px) holds a screenshot or table. The right side holds two blocks with 3–4 short bullets each: a red-ruled **"What's missing"** and a blue-ruled **"What the new site does"**. Drop any slide whose gap doesn't exist for this prospect, and add one if the research turns up a bigger gap.

### Copy rules

- **Factual:** be direct, and trace every claim to the fact sheet. Keep bullets around 55 characters.
- **Colour:** red means missing, blue means what we do, green means a genuine pass. The words always say it too.
- **Labels:** label the source of every third-party number: "As displayed", "Places data", "Own site claim", "local Lighthouse run", "Indicative checks, not Google rankings".
- **Targets:** call targets targets ("Target: 100"). No promised rankings, review counts or call volumes.
- **Money:** no pricing, budgets or lost-revenue maths.
- **Legal wording:** for insurance or legal copy, only suggest "match the wording on your own <claim/terms> page". Never cite statutes or call anything illegal, non-compliant or risky.
- **Reviews and proof:** no negative review quotes on slides. Never invent testimonials, certifications, warranties, financing, awards or client names. The prospect's trust items appear as "once you confirm them".
- **Agency proof:** only from `agency.md`'s Proof list. Items under "Offered but not published" stay in the speaker notes.
- **Style:**
  - no eyebrow or kicker labels, emoji, decorative icons, stock photos, purple, tilted cards or animations
  - avoid: revolutionise, unlock, game-changer, elevate, supercharge, skyrocket, cutting-edge, seamless

### Speaker notes

Each slide ends with an `<aside>`: 3–6 sentences in the presenter's voice, addressed to the owner by first name. Cover the evidence, why it costs calls, what the new site does, and any question to ask (for example "which warranty do you actually offer?"). End with the service labels in square brackets.

## When the prospect has no website

Sometimes the "URL" is a Facebook page, a Google Business Profile or a directory listing. The deck then sells a first website, and the evidence comes from wherever the business does appear.

**Research instead of Step 1:**
- **Their social page, logged out:** screenshot it at 1440×900 and with `cdp-shot.mjs` as a 390-wide phone viewport. Record what a stranger sees: log-in walls or "open app" prompts, follower and post counts, the contact line, any hours or address.
- **Listings:** BBB (service area, rating, address), Google Business Profile, Angi/HomeAdvisor, Yelp. Note when listings disagree on address or hours.
- **Search checks:** "<service> <town>" for the home town and 3–5 nearby towns, using an AI web-search tool. Record who comes up and whether the prospect appears, and how (e.g. "via BBB listing only"). Google often answers headless requests with a CAPTCHA: never try to get around it, just use another tool and label every result "indicative, not Google rankings".
- **Competitors:** who has their own pages per town or service, and their review counts with the source labelled.
- **Brand:** with no site CSS, take colours from the logo, the social page, or the mockup if one exists.

**If a homepage mockup already exists** (see `agency.md`'s mockup workflow), it's the strongest evidence you have:
- Screenshot it on desktop and on a phone.
- Run Lighthouse on its live URL twice and show those measured scores, labelled with the date and "run locally".
- Be honest about its own gaps (a single page, a menu that only scrolls, no FAQ yet) by listing them under "Added in the full site".

If there's no mockup, the scores slide shows targets instead.

**Slide spine (11):**

| # | id | Title pattern | Visual |
|---|----|------|------|
| 1 | cover | "You do the work. Online, it's hard to find." | Dark panel, both logos, one of their own job photos (from their social page) on the right |
| 2 | report | "<Name> online today, scored" | Rows: website (none), social page, searches nearby, town × service pages (0 of N), reviews, estimate request, hours, location, plus one true pass (e.g. BBB rating) |
| 3 | social | "Your Facebook page asks visitors to log in first" (when true) | Logged-out screenshot + strip: followers, posts, what phones see |
| 4 | search | "Search for <service> nearby, and competitors show up instead" | Table: town / what came up / the prospect ("Via BBB listing only", "Not named") |
| 5 | coverage | "0 of N town-and-service pages exist" | Towns × services grid, every cell "No page"; towns from their listing, marked "to confirm" |
| 6 | reviews | "Competitors show their reviews. <Name> has none to show yet." | Card grid: the prospect vs 4–5 competitors, sources labelled |
| 7 | mockup | "Your new homepage is already built" | Desktop + phone screenshots of the mockup; "What's on it" / "Added in the full site" |
| 8 | scores | "Your new homepage already scores 100" (only if measured) | 4 score cards from the live mockup; "Today: no website to score" |
| 9 | addon | "Optional add-on: an answer while you're on a job" | Their phone screenshot + how customers reach them today |
| 10 | offer | "The new <Name> website" | Included / Optional add-on; next step: walk through the homepage, confirm towns, hours and address |
| 11 | sources | "Sources" | What was checked, how, and what isn't verified |

Skip the menu, sitemap and live-site Lighthouse slides: there's nothing to measure. Never say the prospect is invisible when they turn up through directories; say how they turn up.

## Step 4: check, then publish

1. Render locally before every publish:
   ```bash
   python3 -I <skill-dir>/scripts/render_check.py <deck-root> blobs.json preview
   ```
   `blobs.json` maps each asset id to its local file (see `examples/blobs.json`). Look at every `sheet*.png` and fix:
   - anything below y≈920 or touching the footer
   - text that overflows its box
   - a red flag covering the evidence it points at

   The usual fixes: cut the title to one line, shrink a screenshot frame, or merge a strip into one cell.
2. Publish only the changed files. To remove a slide, publish `"project/slides/<id>.html": null` and take it out of `order`.
3. Tell the user:
   - the link, and that the deck is private until shared
   - that it downloads as PDF or PPTX
   - what was verified and what was left out
   - any `[CONFIRM]` placeholders still in the deck

## After the deck: the mockup

If `agency.md` describes a mockup workflow, build the free homepage there:
- Keep the prospect's colours and heading font.
- Put a visible placeholder on anything unverified.
- Mark the page `noindex`.

Then run Lighthouse on both the mockup and the live site, and put both sets of scores on the scores slide.

## Design bar

Strong contrast, restrained colour, confident type, generous space, and one dominant visual per slide. For calibration, look at galleries such as bestsaaswebdesigns.com, stylogeny.com, awwwards.com and godly.design.
