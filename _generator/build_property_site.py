"""
Single-property website generator for ryansellsnola.com.

Outputs a static page at [repo root]/[slug]/index.html, matching the design system
of the existing index.html (sell) and fsbo/index.html pages: black hero, green accent,
white form-card with shadow, light-gray about section, black footer. Same lead-capture
pattern, posting to the shared /submit Cloudflare Pages Function, but type: "showing"
instead of "sell"/"fsbo" -- no PDF download, just a confirmation message.

Per-listing config is intentionally close to the OM generator's config shape
(.claude/skills/om/om_helpers.py in the RyanOS vault) since both are built from the
same listing data, financing math mirrors compute_financing() there. Keep the two in
sync if the mortgage formula ever changes.

Usage:
    python3 build_property_site.py /path/to/config.json
"""

import json
import shutil
import sys
from pathlib import Path

from PIL import Image

REPO_ROOT = Path(__file__).resolve().parent.parent

AGENT_PHONE = "(504) 708-2257"
AGENT_PHONE_TEL = "5047082257"
AGENT_EMAIL = "ryan@ryansellsnola.com"
BROKERAGE_LINE = "Snap Realty, LLC &nbsp;|&nbsp; (504) 301-3826 &nbsp;|&nbsp; New Orleans, Louisiana &nbsp;|&nbsp; Licensed in Louisiana"
AGENT_BIO = (
    "I'm a New Orleans listing agent who specializes in helping sellers prepare, price, and "
    "close for the most money the market will bear. I work in Lakeview, Gentilly, Mid-City, "
    "the Irish Channel, and neighborhoods across Orleans and Jefferson Parish. I don't filter "
    "information, you'll know exactly what a property is worth and what it takes to get the "
    "best outcome."
)


def compute_monthly_payment(price, down_pct, rate_pct, term_years,
                             annual_property_tax, monthly_insurance, monthly_hoa, monthly_flood=0):
    """Mirrors compute_financing() in the OM generator -- same formula, trimmed to just
    the monthly payment since the website shows a simple estimate, not a full closing-cost
    breakdown."""
    loan = price * (1 - down_pct / 100)
    r = (rate_pct / 100) / 12
    n = term_years * 12
    pi = loan * (r * (1 + r) ** n) / ((1 + r) ** n - 1)
    return pi + (annual_property_tax / 12) + monthly_insurance + monthly_hoa + monthly_flood


def resize_for_web(src_dir: str, dest_dir: str, filenames: list, max_dim=1920, quality=82) -> list:
    """Downsizes MLS photos (8000px+, 7-9MB each) to web-friendly JPEGs. Returns output filenames."""
    dst = Path(dest_dir)
    dst.mkdir(parents=True, exist_ok=True)
    out = []
    for i, fname in enumerate(filenames):
        im = Image.open(Path(src_dir) / fname).convert("RGB")
        im.thumbnail((max_dim, max_dim), Image.LANCZOS)
        out_name = f"photo-{i+1}.jpg"
        im.save(dst / out_name, "JPEG", quality=quality, optimize=True)
        out.append(out_name)
    return out


def gallery_html(photo_files: list) -> str:
    items = "".join(
        f'<div class="gallery-item"><img src="photos/{f}" alt="Property photo {i+1}" loading="lazy"></div>'
        for i, f in enumerate(photo_files)
    )
    return f'<div class="gallery-grid">{items}</div>'


def build_site(cfg: dict):
    slug = cfg["slug"]
    out_dir = REPO_ROOT / slug
    photos_dir = out_dir / "photos"

    photo_files = resize_for_web(cfg["photos_source_dir"], str(photos_dir), cfg["photo_order"])
    hero_photo = photo_files[cfg.get("hero_photo_index", 0)]

    monthly = None
    if cfg.get("financing"):
        monthly = compute_monthly_payment(**cfg["financing"])

    stats_html = "".join(
        f'<div class="stat"><span class="stat-num">{k}</span><span class="stat-label">{v}</span></div>'
        for k, v in cfg["quick_facts"].items()
    )

    highlights_html = "".join(f"<li>{h}</li>" for h in cfg["highlights"])

    monthly_block = ""
    if monthly:
        monthly_block = f'''
<section class="financing">
  <div class="financing-inner">
    <h2>Estimated Monthly Payment</h2>
    <div class="financing-num">${monthly:,.0f}<span>/mo</span></div>
    <p class="financing-note">{cfg["financing_note"]}</p>
  </div>
</section>'''

    html = HTML_TEMPLATE.format(
        title=cfg["title"],
        meta_description=cfg["meta_description"],
        address_line1=cfg["address_line1"],
        address_line2=cfg["address_line2"],
        price=f'{cfg["list_price"]:,.0f}',
        hero_photo=hero_photo,
        hook=cfg["hook"],
        stats_html=stats_html,
        description_html="".join(f"<p>{p}</p>" for p in cfg["description_paragraphs"]),
        highlights_html=highlights_html,
        gallery_html=gallery_html(photo_files),
        monthly_block=monthly_block,
        headshot_path=cfg.get("headshot_web_path", "/assets/ryan-headshot.png"),
        bio=AGENT_BIO,
        phone=AGENT_PHONE,
        phone_tel=AGENT_PHONE_TEL,
        email=AGENT_EMAIL,
        brokerage_line=BROKERAGE_LINE,
        property_label=cfg["address_line1"],
    )

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.html").write_text(html)
    return str(out_dir / "index.html")


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title}</title>
  <meta name="description" content="{meta_description}" />
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

    :root {{
      --green:      #2B7A2B;
      --green-dark: #1A4A1A;
      --black:      #0D0D0D;
      --lgray:      #F5F5F5;
      --white:      #FFFFFF;
      --text:       #222222;
      --muted:      #666666;
    }}

    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      color: var(--text);
      background: var(--white);
    }}

    .hero {{
      background: var(--black);
      color: var(--white);
      padding: 56px 24px 64px;
      position: relative;
      overflow: hidden;
    }}
    .hero::before {{
      content: '';
      position: absolute;
      inset: 0;
      background: url('photos/{hero_photo}') center/cover no-repeat;
      opacity: 0.32;
    }}
    .bottom-logo {{ text-align: center; padding: 40px 24px; background: var(--lgray); }}
    .bottom-logo img {{ height: 68px; display: inline-block; }}
    .hero-inner {{
      position: relative;
      max-width: 1000px;
      margin: 0 auto;
      display: grid;
      grid-template-columns: 1.2fr 1fr;
      gap: 48px;
      align-items: start;
    }}
    .hero-inner > * {{ min-width: 0; }}
    .hero-eyebrow {{
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 2px;
      color: var(--green);
      text-transform: uppercase;
      margin-bottom: 14px;
    }}
    .hero h1 {{
      font-size: clamp(24px, 3.6vw, 34px);
      font-weight: 800;
      line-height: 1.25;
      margin-bottom: 6px;
    }}
    .hero .addr2 {{ font-size: 15px; color: #CCCCCC; margin-bottom: 18px; }}
    .hero .price {{ font-size: clamp(28px, 4vw, 38px); font-weight: 800; color: var(--green); margin-bottom: 18px; }}
    .hero-hook {{ font-size: 16px; color: #DDDDDD; line-height: 1.6; margin-bottom: 28px; max-width: 480px; }}

    .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(90px, 1fr)); gap: 14px; max-width: 480px; }}
    .stat {{ text-align: center; background: rgba(255,255,255,0.06); border-radius: 8px; padding: 12px 6px; }}
    .stat-num {{ font-size: 20px; font-weight: 800; color: var(--white); display: block; }}
    .stat-label {{ font-size: 10px; color: #999; text-transform: uppercase; letter-spacing: 0.5px; }}

    .form-card {{
      background: var(--white);
      border-radius: 10px;
      padding: 28px 26px;
      color: var(--text);
      box-shadow: 0 8px 40px rgba(0,0,0,0.4);
    }}
    .form-card h2 {{ font-size: 19px; font-weight: 700; margin-bottom: 6px; }}
    .form-card > p {{ font-size: 13px; color: var(--muted); margin-bottom: 18px; line-height: 1.5; }}
    .form-card input {{
      display: block; width: 100%; padding: 12px 13px; margin-bottom: 10px;
      border: 1.5px solid #DDDDDD; border-radius: 6px; font-size: 14px; font-family: inherit;
      outline: none; transition: border 0.2s;
    }}
    .form-card input:focus {{ border-color: var(--green); }}
    .form-card button {{
      width: 100%; padding: 13px; background: var(--green); color: var(--white);
      font-size: 15px; font-weight: 700; border: none; border-radius: 6px; cursor: pointer;
      transition: background 0.2s;
    }}
    .form-card button:hover {{ background: var(--green-dark); }}
    .form-card button:disabled {{ opacity: 0.6; cursor: not-allowed; }}
    .form-note {{ font-size: 11px; color: #999; text-align: center; margin-top: 10px; }}
    .err-msg {{ color: #cc3300; font-size: 13px; margin-top: 8px; display: none; }}
    .form-success {{ display: none; text-align: center; padding: 8px 0; }}
    .form-success h3 {{ font-size: 18px; color: var(--green); margin-bottom: 8px; }}
    .form-success p {{ font-size: 13px; color: var(--muted); }}

    .gallery {{ padding: 56px 24px; background: var(--white); }}
    .gallery-grid {{
      max-width: 1100px; margin: 0 auto; display: grid;
      grid-template-columns: repeat(3, 1fr); gap: 12px;
    }}
    .gallery-item {{ aspect-ratio: 4/3; overflow: hidden; border-radius: 6px; }}
    .gallery-item img {{ width: 100%; height: 100%; object-fit: cover; display: block; }}

    .description {{ padding: 56px 24px; background: var(--lgray); }}
    .description-inner {{ max-width: 700px; margin: 0 auto; }}
    .description h2 {{ font-size: 24px; font-weight: 800; margin-bottom: 18px; }}
    .description p {{ font-size: 15px; color: var(--text); line-height: 1.7; margin-bottom: 14px; }}
    .highlights {{ max-width: 700px; margin: 28px auto 0; list-style: none; }}
    .highlights li {{
      font-size: 14px; color: var(--text); padding: 7px 0 7px 22px; position: relative;
    }}
    .highlights li::before {{ content: '✓'; color: var(--green); position: absolute; left: 0; font-weight: 700; }}

    .financing {{ padding: 48px 24px; background: var(--white); text-align: center; }}
    .financing h2 {{ font-size: 18px; font-weight: 700; color: var(--muted); margin-bottom: 10px; }}
    .financing-num {{ font-size: 42px; font-weight: 800; color: var(--green); }}
    .financing-num span {{ font-size: 18px; color: var(--muted); font-weight: 600; }}
    .financing-note {{ font-size: 12px; color: #999; margin-top: 10px; max-width: 480px; margin-left: auto; margin-right: auto; }}

    .about {{ padding: 56px 24px; background: var(--lgray); }}
    .about-inner {{
      max-width: 700px; margin: 0 auto; display: grid;
      grid-template-columns: 160px 1fr; gap: 32px; align-items: center;
    }}
    .about-photo img {{ width: 100%; border-radius: 6px; display: block; }}
    .about-text h2 {{ font-size: 20px; font-weight: 800; margin-bottom: 8px; }}
    .about-text p {{ font-size: 14px; color: var(--muted); line-height: 1.7; margin-bottom: 8px; }}

    footer {{
      background: var(--black); color: #888; text-align: center;
      padding: 28px 24px; font-size: 12px; line-height: 1.8;
    }}
    footer a {{ color: var(--green); text-decoration: none; }}

    @media (max-width: 700px) {{
      .hero {{ padding-left: 16px; padding-right: 16px; }}
      .hero-inner {{ grid-template-columns: 1fr; }}
      .stats {{ grid-template-columns: repeat(2, 1fr); max-width: 100%; gap: 10px; }}
      .stat {{ padding: 10px 4px; }}
      .stat-num {{ font-size: 17px; }}
      .gallery-grid {{ grid-template-columns: repeat(2, 1fr); }}
      .about-inner {{ grid-template-columns: 1fr; text-align: center; }}
      .about-photo {{ max-width: 120px; margin: 0 auto; }}
    }}
  </style>
</head>
<body>

<section class="hero">
  <div class="hero-inner">
    <div class="hero-text">
      <p class="hero-eyebrow">New Orleans Listing</p>
      <h1>{address_line1}</h1>
      <p class="addr2">{address_line2}</p>
      <p class="price">${price}</p>
      <p class="hero-hook">{hook}</p>
      <div class="stats">{stats_html}</div>
    </div>

    <div class="form-card">
      <h2>Schedule a Showing</h2>
      <p>Tell us when works and Ryan will confirm a time.</p>

      <form id="showing-form">
        <input type="text"  id="sh-name"  placeholder="Your name"     required autocomplete="name" />
        <input type="tel"   id="sh-phone" placeholder="Phone number"  required autocomplete="tel" />
        <button type="submit" id="sh-btn">Request a Showing</button>
        <p class="err-msg" id="sh-err"></p>
        <p class="form-note">Your info goes directly to Ryan. No spam, no third parties.</p>
      </form>

      <div class="form-success" id="sh-success">
        <h3>Got it!</h3>
        <p>Ryan will reach out shortly to confirm your showing time.</p>
      </div>
    </div>
  </div>
</section>

<section class="gallery">
  {gallery_html}
</section>

<section class="description">
  <div class="description-inner">
    <h2>About This Home</h2>
    {description_html}
    <ul class="highlights">
      {highlights_html}
    </ul>
  </div>
</section>
{monthly_block}

<section class="about">
  <div class="about-inner">
    <div class="about-photo">
      <img src="{headshot_path}" alt="Ryan Curtis Rogers, REALTOR®" onerror="this.style.display='none'" />
    </div>
    <div class="about-text">
      <h2>Ryan Curtis Rogers, REALTOR®</h2>
      <p>{bio}</p>
      <p><strong>{phone} &nbsp;|&nbsp; {email}</strong></p>
    </div>
  </div>
</section>

<div class="bottom-logo">
  <img src="/assets/snap-logo-green.png" alt="Snap Realty" />
</div>

<footer>
  <p>Ryan Curtis Rogers, REALTOR® &nbsp;|&nbsp; <a href="tel:{phone_tel}">{phone}</a> &nbsp;|&nbsp; <a href="mailto:{email}">{email}</a></p>
  <p style="margin-top:6px;">{brokerage_line}</p>
  <p style="margin-top:8px;">&copy; 2026 Ryan Curtis Rogers. Snap Realty is an Equal Housing Opportunity brokerage.</p>
</footer>

<script>
  const form    = document.getElementById('showing-form');
  const btn     = document.getElementById('sh-btn');
  const errMsg  = document.getElementById('sh-err');
  const success = document.getElementById('sh-success');

  form.addEventListener('submit', async (e) => {{
    e.preventDefault();
    btn.disabled = true;
    btn.textContent = 'Sending…';
    errMsg.style.display = 'none';

    const payload = {{
      name:  document.getElementById('sh-name').value.trim(),
      phone: document.getElementById('sh-phone').value.trim(),
      type:  'showing',
      property: '{property_label}',
    }};

    try {{
      const res  = await fetch('/submit', {{ method: 'POST', headers: {{ 'Content-Type': 'application/json' }}, body: JSON.stringify(payload) }});
      const data = await res.json();
      if (data.ok) {{
        form.style.display = 'none';
        success.style.display = 'block';
      }} else {{
        throw new Error(data.error || 'Something went wrong.');
      }}
    }} catch (err) {{
      errMsg.textContent = err.message;
      errMsg.style.display = 'block';
      btn.disabled = false;
      btn.textContent = 'Request a Showing';
    }}
  }});
</script>

</body>
</html>
"""


if __name__ == "__main__":
    config_path = sys.argv[1]
    with open(config_path) as fh:
        cfg = json.load(fh)
    out = build_site(cfg)
    print(f"Built: {out}")
