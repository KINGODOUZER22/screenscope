#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_site.py — genera todas las paginas estaticas del sitio de afiliados
de monitores ScreenScope a partir de datos/productos.json. No edites a mano
los archivos HTML generados: edita el JSON (o pega nuevos enlaces de
afiliado en el paso de poblado) y vuelve a ejecutar este script.

Uso (desde la raiz del proyecto):
    python3 tools/build_site.py
"""
import json
import math
import html
import os
import sys
from datetime import date, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(ROOT, "datos", "productos.json")

VER = datetime.now().strftime("%Y%m%d%H%M")

BRAND = {
    "name": "ScreenScope",
    "tagline": "Comparativas de monitores basadas en datos reales.",
    "disclosureShort": "ScreenScope participa en el Programa de Afiliados de Amazon EU. Como afiliados, obtenemos ingresos por las compras que cumplen los requisitos aplicables, sin coste adicional para ti.",
}

SITE_URL = "https://kingodouzer22.github.io/screenscope/"
DEFAULT_OG_IMAGE = ""  # se rellena en main() con la imagen de un producto destacado
GA_MEASUREMENT_ID = "G-YR1FQ2PCWX"

NAV = [
    ("Inicio", "index.html"),
    ("Gaming", "categoria-gaming.html"),
    ("Diseño", "categoria-diseno.html"),
    ("Ultrawide", "categoria-ultrawide.html"),
    ("Comparar", "comparador.html"),
    ("Ofertas", "ofertas.html"),
    ("Guía de compra", "guia-mejor-monitor-gaming-2026.html"),
]

FOOTER_LINKS = [
    ("Sobre nosotros / Cómo puntuamos", "sobre-nosotros.html"),
    ("Aviso de afiliados", "aviso-afiliados.html"),
    ("Política de privacidad", "privacidad.html"),
]

CATEGORIES = [
    {
        "key": "Gaming",
        "slug": "categoria-gaming.html",
        "title": "Monitores Gaming",
        "intro": "Pantallas de alta tasa de refresco y bajo tiempo de respuesta pensadas para gaming competitivo y casual — aquí importan más los Hz, los ms y la tecnología de sincronización que la resolución por sí sola.",
        "seoTitle": "Mejores Monitores Gaming 2026: Comparativa, Precios y Opiniones — ScreenScope",
        "seoDescription": "Compara los mejores monitores gaming de 144Hz, 165Hz y 240Hz por tasa de refresco, tiempo de respuesta y precio en Amazon. Encuentra el monitor gaming barato u oferta que se ajusta a tu presupuesto en 2026.",
        "keywords": "monitor gaming, mejor monitor gaming 2026, monitor gaming barato, monitor 144hz, monitor 240hz, monitor gaming oferta, monitor gaming amazon, comparativa monitores gaming",
    },
    {
        "key": "Design",
        "slug": "categoria-diseno.html",
        "title": "Monitores de Diseño y Productividad",
        "intro": "Monitores de alta resolución y color preciso para foto, vídeo y trabajo diario, donde la calidad del panel y la calibración de fábrica importan más que la tasa de refresco.",
        "seoTitle": "Mejores Monitores para Diseño y Fotografía 2026: Comparativa — ScreenScope",
        "seoDescription": "Compara monitores profesionales para diseño gráfico, edición de vídeo y fotografía por precisión de color, resolución 4K y calibración de fábrica, con precios reales de Amazon.",
        "keywords": "monitor para diseño gráfico, monitor para fotografía, monitor 4k profesional, monitor color preciso, mejor monitor para editar vídeo, monitor para trabajo, monitor productividad",
    },
    {
        "key": "Ultrawide",
        "slug": "categoria-ultrawide.html",
        "title": "Monitores Ultrawide",
        "intro": "Pantallas de formato ancho que sustituyen un escritorio con varios monitores por una sola pantalla curva — el precio a pagar es espacio de mesa y presupuesto a cambio de inmersión.",
        "seoTitle": "Mejores Monitores Ultrawide 2026: Comparativa y Precios — ScreenScope",
        "seoDescription": "Compara monitores ultrawide curvos de 34 y 49 pulgadas para productividad y gaming inmersivo, con ficha técnica completa y precios de Amazon.",
        "keywords": "monitor ultrawide, monitor curvo 34 pulgadas, monitor 49 pulgadas, mejor monitor ultrawide 2026, monitor panorámico, monitor ultrawide gaming, monitor ultrawide oferta",
    },
]

SCORE_AXES = ["scoreSharpness", "scoreSmoothness", "scoreColorHdr", "scoreErgonomics", "scoreGaming", "scoreValue"]
AXIS_LABELS = {
    "scoreSharpness": "Nitidez",
    "scoreSmoothness": "Fluidez",
    "scoreColorHdr": "Color / HDR",
    "scoreErgonomics": "Ergonomía",
    "scoreGaming": "Gaming",
    "scoreValue": "Calidad-precio",
}

SPEC_GROUPS = [
    ("Pantalla", [
        ("panelType", "Tipo de panel", "", None),
        ("sizeInches", "Tamaño de pantalla", "\"", "max"),
        ("resolution", "Resolución", "", None),
        ("curved", "Curvo", "", None),
        ("curvatureRadius", "Curvatura", "", None),
        ("brightnessNits", "Brillo", " nits", "max"),
        ("hdr", "HDR", "", None),
    ]),
    ("Rendimiento gaming", [
        ("refreshRateHz", "Tasa de refresco", " Hz", "max"),
        ("responseTimeMs", "Tiempo de respuesta (GtG)", " ms", "min"),
        ("syncTech", "Tecnología de sincronización", "", None),
    ]),
    ("Ergonomía y construcción", [
        ("heightAdjustable", "Ajuste de altura", "", None),
        ("pivot", "Pivote (modo retrato)", "", None),
        ("weightKg", "Peso", " kg", "min"),
        ("warrantyYears", "Garantía", " años", "max"),
    ]),
]


def esc(s):
    if s is None:
        return ""
    return html.escape(str(s), quote=True)


def fmt_eur(n):
    if n is None:
        return "—"
    s = "{:,.2f}".format(n)
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return s + " €"


def fmt_bool(v):
    if v is None:
        return "—"
    return "Sí" if v else "No"


def load_products():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Partials compartidos
# ---------------------------------------------------------------------------

def render_nav(active_href):
    links = []
    for label, href in NAV:
        cls = ' class="is-active"' if href == active_href else ""
        links.append('<a href="{0}"{1}>{2}</a>'.format(href, cls, esc(label)))
    links_html = "".join(links)
    mobile_html = "".join('<a href="{0}">{1}</a>'.format(href, esc(label)) for label, href in NAV)
    return """
<header class="nav">
  <div class="container nav-inner">
    <a class="brand" href="index.html"><img class="brand-logo" src="assets/img/logo-cat.png" alt="" width="28" height="28">{name}</a>
    <nav class="nav-links" aria-label="Principal">{links}<a class="nav-cta" href="comparador.html">Comparar <span data-compare-count></span></a></nav>
    <button class="nav-toggle" data-nav-toggle aria-expanded="false" aria-controls="mobile-nav" aria-label="Abrir menú">☰</button>
  </div>
  <nav id="mobile-nav" class="nav-mobile" data-nav-mobile aria-label="Móvil">{mobile}</nav>
</header>""".format(name=esc(BRAND["name"]), links=links_html, mobile=mobile_html)


def render_footer():
    links_html = "".join('<a href="{0}">{1}</a>'.format(href, esc(label)) for label, href in FOOTER_LINKS)
    return """
<footer class="footer">
  <div class="container">
    <div class="footer-grid">
      <div>
        <a class="brand" href="index.html"><img class="brand-logo" src="assets/img/logo-cat.png" alt="" width="28" height="28">{name}</a>
        <p style="color:var(--text-dim); margin-top:.6rem; max-width:42ch;">{tagline}</p>
      </div>
      <div class="footer-links">{links}</div>
      <div class="footer-links">
        <span style="color:var(--text-mute); font-size:.82rem;">&copy; {year} {name}</span>
      </div>
    </div>
    <p class="disclosure">{disclosure} Amazon y el logotipo de Amazon son marcas de Amazon.com, Inc. o sus filiales.</p>
  </div>
</footer>""".format(name=esc(BRAND["name"]), tagline=esc(BRAND["tagline"]), links=links_html,
                     year=date.today().year, disclosure=esc(BRAND["disclosureShort"]))


def render_cookie_banner():
    return """
<div class="cookie-banner" data-cookie-banner hidden>
  <p>Usamos Google Analytics para saber cuántas visitas recibe ScreenScope — no identifica a nadie personalmente. Puedes aceptarlo o rechazarlo; más info en la <a href="privacidad.html">política de privacidad</a>.</p>
  <div class="cookie-actions">
    <button class="btn btn-ghost btn-sm" type="button" data-cookie-reject>Rechazar</button>
    <button class="btn btn-primary btn-sm" type="button" data-cookie-accept>Aceptar</button>
  </div>
</div>"""


def page_shell(title, description, body, active_nav="", canonical="", extra_head="", extra_jsonld="",
               keywords="", image=""):
    canonical_abs = SITE_URL + canonical if canonical else SITE_URL
    image_abs = SITE_URL + (image or DEFAULT_OG_IMAGE) if (image or DEFAULT_OG_IMAGE) else ""
    keywords_tag = '<meta name="keywords" content="{0}">'.format(esc(keywords)) if keywords else ""
    image_tags = ""
    if image_abs:
        image_tags = (
            '<meta property="og:image" content="{0}">\n'
            '<meta name="twitter:image" content="{0}">'
        ).format(esc(image_abs))
    return """<!doctype html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{description}">
{keywords_tag}
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{brand}">
<meta property="og:locale" content="es_ES">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:url" content="{canonical}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{description}">
{image_tags}
<link rel="icon" href="assets/img/favicon.png" type="image/png">
<link rel="apple-touch-icon" href="assets/img/favicon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:wght@600;700&family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500&display=swap">
<link rel="stylesheet" href="styles.css?v={ver}">
{extra_head}
</head>
<body>
<a class="skip-link" href="#main">Saltar al contenido</a>
{nav}
<main id="main">
{body}
</main>
{footer}
{cookie_banner}
<script defer src="lib/manifest.js?v={ver}"></script>
<script defer src="lib/db.js?v={ver}"></script>
<script defer src="main.js?v={ver}"></script>
{extra_jsonld}
</body>
</html>""".format(title=esc(title), description=esc(description), canonical=esc(canonical_abs),
                   brand=esc(BRAND["name"]), keywords_tag=keywords_tag, image_tags=image_tags,
                   nav=render_nav(active_nav), body=body, footer=render_footer(), ver=VER,
                   cookie_banner=render_cookie_banner(),
                   extra_head=extra_head, extra_jsonld=extra_jsonld)


def product_href(p):
    return "monitor-{0}.html".format(p["id"])


def render_card(p):
    discount_pct = None
    if p.get("retailPrice") and p.get("discountedPrice") and p["retailPrice"] > p["discountedPrice"]:
        discount_pct = round(100 * (1 - p["discountedPrice"] / p["retailPrice"]))
    badge = ""
    if p.get("sample"):
        badge = '<span class="badge badge-sample">Enlace pendiente</span>'
    elif discount_pct:
        badge = '<span class="badge badge-offer">-{0}%</span>'.format(discount_pct)
    return """
<article class="card" data-sync="{sync}" data-price="{price}" data-rating="{rating}">
  <div class="card-media">
    <img src="{img}" alt="{name}" loading="lazy" decoding="async">
    <div style="position:absolute; top:.6rem; left:.6rem;">{badge}</div>
  </div>
  <div class="card-body">
    <span class="card-cat">{cat}</span>
    <h3 class="card-title"><a href="{href}">{name}</a></h3>
    <p class="card-rating">&#9733; <strong>{rating}</strong> ({reviews} reseñas)</p>
    <div class="card-price">
      <span class="price-now">{price_now}</span>
      {price_before}
    </div>
    <div class="card-actions">
      <a class="btn btn-ghost btn-sm" href="{href}">Ver ficha</a>
      <button class="btn btn-ghost btn-sm" data-add-comparador="{id}">Comparar</button>
    </div>
  </div>
</article>""".format(
        sync=esc(p.get("syncTech", "")), price=p.get("discountedPrice") or 0, rating=p.get("avgRating") or 0,
        img=esc(p["images"][0]), name=esc(p["name"]), badge=badge, cat=esc(CAT_LABEL.get(p["category"], p["category"])),
        href=product_href(p), reviews=p.get("reviewCount") or 0,
        price_now=fmt_eur(p.get("discountedPrice")),
        price_before=('<span class="price-before">{0}</span>'.format(fmt_eur(p["retailPrice"]))
                      if p.get("retailPrice") and p.get("discountedPrice") and p["retailPrice"] > p["discountedPrice"] else ""),
        id=esc(p["id"]),
    )


CAT_LABEL = {"Gaming": "Gaming", "Design": "Diseño", "Ultrawide": "Ultrawide", "Office": "Oficina"}


def radar_svg(series_list, size=320):
    """series_list: [{label, color, scores: {axis: 0-10}}]"""
    cx = cy = size / 2
    r = size * 0.36
    n = len(SCORE_AXES)

    def angle(i):
        return (2 * math.pi * i) / n - math.pi / 2

    def pt(i, frac):
        a = angle(i)
        return (cx + math.cos(a) * r * frac, cy + math.sin(a) * r * frac)

    parts = ['<svg viewBox="0 0 {0} {0}" role="img" aria-label="Gráfico de radar con las puntuaciones del editor">'.format(size)]
    for frac in (0.25, 0.5, 0.75, 1.0):
        pts = " ".join("{0:.1f},{1:.1f}".format(*pt(i, frac)) for i in range(n))
        parts.append('<polygon points="{0}" fill="none" stroke="var(--line)" stroke-width="1"></polygon>'.format(pts))
    for i, axis in enumerate(SCORE_AXES):
        x, y = pt(i, 1)
        parts.append('<line x1="{0}" y1="{1}" x2="{2:.1f}" y2="{3:.1f}" stroke="var(--line)" stroke-width="1"></line>'.format(cx, cy, x, y))
        lx, ly = pt(i, 1.16)
        cos_a = math.cos(angle(i))
        anchor = "start" if cos_a > 0.3 else ("end" if cos_a < -0.3 else "middle")
        parts.append('<text x="{0:.1f}" y="{1:.1f}" font-size="10" fill="var(--text-dim)" text-anchor="{2}" dominant-baseline="middle">{3}</text>'.format(lx, ly, anchor, esc(AXIS_LABELS[axis])))
    for s in series_list:
        pts = []
        for i, axis in enumerate(SCORE_AXES):
            v = s["scores"].get(axis)
            frac = 0 if v is None else max(0, min(10, v)) / 10
            pts.append("{0:.1f},{1:.1f}".format(*pt(i, frac)))
        parts.append('<polygon points="{0}" fill="{1}" fill-opacity="0.22" stroke="{1}" stroke-width="2"></polygon>'.format(" ".join(pts), s["color"]))
    parts.append("</svg>")
    return "".join(parts)


def render_spec_table(p):
    rows = []
    for group_title, fields in SPEC_GROUPS:
        rows.append('<tr><td colspan="2" class="spec-group-title">{0}</td></tr>'.format(esc(group_title)))
        for key, label, unit, best in fields:
            v = p.get(key)
            if v is None:
                display = "—"
            elif isinstance(v, bool):
                display = fmt_bool(v)
            elif isinstance(v, float):
                num = str(int(v)) if v == int(v) else str(v).replace(".", ",")
                display = "{0}{1}".format(num, unit)
            else:
                display = "{0}{1}".format(v, unit)
            rows.append("<tr><th>{0}</th><td>{1}</td></tr>".format(esc(label), esc(display)))
    extra = p.get("specsExtra") or {}
    extra_html = ""
    if extra:
        extra_rows = "".join('<div><strong>{0}:</strong> {1}</div>'.format(esc(k), esc(v)) for k, v in extra.items())
        extra_html = '<details class="specs-extra"><summary>Otros datos</summary><div style="margin-top:.6rem; display:grid; gap:.4rem;">{0}</div></details>'.format(extra_rows)
    return '<table class="spec-table">{0}</table>{1}'.format("".join(rows), extra_html)


def load_accesorios():
    path = os.path.join(ROOT, "datos", "accesorios.json")
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def render_accessories_section():
    items = load_accesorios()
    if not items:
        return ""
    cards = ""
    for a in items:
        cards += """
      <article class="acc-card">
        <img src="{img}" alt="{title}" loading="lazy">
        <p class="acc-title">{title}</p>
        <p class="acc-tagline">{tagline}</p>
        <p class="acc-meta">&#9733; {rating} &middot; {reviews} reseñas</p>
        <p class="acc-price">{price}</p>
        <a class="btn btn-ghost btn-sm" href="{url}" target="_blank" rel="sponsored nofollow noopener">Ver en Amazon</a>
      </article>""".format(
            img=esc(a["image"]), title=esc(a["title"]), tagline=esc(a["tagline"]),
            rating=a.get("avgRating", "—"), reviews=a.get("reviewCount", 0),
            price=esc(a["price"]), url=esc(a["affiliate_url"]),
        )
    return """
  <section class="section">
    <h2>Accesorios recomendados para tu monitor</h2>
    <p class="lede">Complementos populares que suelen comprarse junto a un monitor nuevo — no forman parte de esta comparativa de monitores, pero son útiles para tu montaje.</p>
    <div class="acc-grid">{0}</div>
  </section>""".format(cards)


def render_ficha(p):
    thumbs = "".join(
        '<button data-src="{0}" class="{1}"><img src="{0}" alt="{2} vista {3}" loading="lazy"></button>'.format(
            esc(img), "is-active" if i == 0 else "", esc(p["name"]), i + 1
        ) for i, img in enumerate(p["images"])
    )
    scores = {a: p.get(a) for a in SCORE_AXES}
    radar = radar_svg([{"label": p["name"], "color": "#7dd3fc", "scores": scores}], size=340)
    legend = "".join(
        '<span><span class="dot" style="background:#7dd3fc"></span>{0}: {1}/10</span>'.format(esc(AXIS_LABELS[a]), p.get(a, "—"))
        for a in SCORE_AXES
    )
    pros_html = "".join("<li>{0}</li>".format(esc(x)) for x in p.get("pros", []))
    cons_html = "".join("<li>{0}</li>".format(esc(x)) for x in p.get("cons", []))
    reviews_html = ""
    for rv in p.get("reviews", []) or []:
        reviews_html += """
      <div class="review-item">
        <p class="review-stars">{stars}</p>
        <p><strong>{author}</strong> — {text}</p>
      </div>""".format(stars="&#9733;" * int(round(rv.get("stars", 5))), author=esc(rv.get("author", "Cliente de Amazon")), text=esc(rv.get("text", "")))
    if not reviews_html:
        reviews_html = '<p style="color:var(--text-mute); font-size:.88rem;">Los fragmentos de reseñas individuales se añaden en cuanto se procesan enlaces reales del producto — mientras tanto, consulta el resumen de valoraciones de arriba.</p>'

    sample_banner = ""
    if p.get("sample"):
        sample_banner = ('<p class="sample-banner">Este es un producto real (uno de los más vendidos en Amazon España ahora mismo), '
                          'pero el botón de compra todavía no lleva tu código de afiliado. Se actualiza en cuanto conectes tu cuenta o me pases el enlace de SiteStripe.</p>')

    price_before_html = ""
    if p.get("retailPrice") and p.get("discountedPrice") and p["retailPrice"] > p["discountedPrice"]:
        price_before_html = '<span class="precio-antes">{0}</span>'.format(fmt_eur(p["retailPrice"]))

    buy_label = "Ver en Amazon" if p.get("affiliate_tag") else "Ver en Amazon (sin tu enlace de afiliado todavía)"

    body = """
<article class="ficha container" data-producto-id="{id}">
  <div class="ficha-top">
    <section class="ficha-galeria" data-galeria>
      <div class="ficha-img-main"><img src="{img0}" alt="{name}" fetchpriority="high"></div>
      <div class="ficha-thumbs" data-thumbs>{thumbs}</div>
    </section>
    <header class="ficha-head">
      <p class="ficha-marca">{brand}</p>
      <h1 class="ficha-nombre">{name}</h1>
      <p class="ficha-rating">&#9733; <strong>{rating}</strong> de media &middot; {reviews} valoraciones en Amazon</p>
      <div class="ficha-precio">
        <span class="precio-actual">{price_now}</span>
        {price_before}
        <span class="precio-nota">Precio orientativo &middot; capturado el {date} &middot; consulta el precio actual en Amazon</span>
      </div>
      {sample_banner}
      <a class="btn btn-primary btn-comprar" href="{affiliate_url}" target="_blank" rel="sponsored nofollow noopener">{buy_label}</a>
      <button class="btn btn-ghost btn-sm" style="margin-top:.6rem;" data-add-comparador="{id}">Añadir al comparador</button>
    </header>
  </div>

  <section class="section">
    <h2>Valoración del editor</h2>
    <div class="radar-wrap">
      <figure data-radar style="width:min(340px,100%)">{radar}</figure>
      <div class="radar-legend" data-radar-legend>{legend}</div>
    </div>
    <p class="lede" style="text-align:center; margin-inline:auto;">Puntuaciones editoriales de 0 a 10, calculadas a partir de las especificaciones y comparables entre todos los monitores de esta web — no son una afirmación del fabricante.</p>
  </section>

  <section class="section">
    <h2>Ficha técnica completa</h2>
    {specs}
  </section>

  <section class="section">
    <h2>Nuestra opinión</h2>
    <div class="guide-body">{editorial}</div>
    <div class="pros-contras">
      <ul class="pros">{pros}</ul>
      <ul class="contras">{cons}</ul>
    </div>
    <p class="ideal-para"><strong>Ideal para:</strong> {ideal}</p>
  </section>

  <section class="section">
    <h2>Qué dicen los compradores</h2>
    <p style="color:var(--text-dim)">{reviews_summary}</p>
    {reviews_list}
    <p style="color:var(--text-mute); font-size:.8rem; margin-top:.6rem;">Resumen basado en las reseñas visibles en Amazon en el momento de la captura.</p>
  </section>

  <a class="btn btn-primary btn-comprar" href="{affiliate_url}" target="_blank" rel="sponsored nofollow noopener">{buy_label}</a>

  {accessories}

  <p class="disclosure">{disclosure}</p>
</article>

<script type="application/ld+json">
{jsonld}
</script>
""".format(
        id=esc(p["id"]), img0=esc(p["images"][0]), name=esc(p["name"]), thumbs=thumbs,
        brand=esc(p.get("brand", "")), rating=p.get("avgRating", "—"), reviews=p.get("reviewCount", 0),
        price_now=fmt_eur(p.get("discountedPrice")), price_before=price_before_html,
        date=p.get("priceCapturedAt", ""), sample_banner=sample_banner,
        affiliate_url=esc(p["affiliate_url"]), buy_label=buy_label,
        radar=radar, legend=legend,
        specs=render_spec_table(p),
        editorial=p.get("editorialBody", ""), pros=pros_html, cons=cons_html, ideal=esc(p.get("idealFor", "")),
        reviews_summary=esc(p.get("reviewsSummary", "")), reviews_list=reviews_html,
        accessories=render_accessories_section(),
        disclosure=esc(BRAND["disclosureShort"]),
        jsonld=json.dumps(build_jsonld_product(p), ensure_ascii=False),
    )
    return body


def jsonld_script(*blocks):
    return "\n".join(
        '<script type="application/ld+json">{0}</script>'.format(json.dumps(b, ensure_ascii=False))
        for b in blocks
    )


def build_jsonld_breadcrumb(crumbs):
    """crumbs: [(name, path_or_'' )] — path relativo al sitio, vacio para el actual sin link."""
    items = []
    for i, (name, path) in enumerate(crumbs):
        item = {"@type": "ListItem", "position": i + 1, "name": name}
        if path:
            item["item"] = SITE_URL + path
        items.append(item)
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": items}


def build_jsonld_product(p):
    data = {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": p["name"],
        "brand": {"@type": "Brand", "name": p.get("brand") or BRAND["name"]},
        "image": [SITE_URL + img for img in p.get("images", [])],
        "description": p.get("description", ""),
        "category": CAT_LABEL.get(p["category"], p["category"]),
        "offers": {
            "@type": "Offer",
            "price": p.get("discountedPrice"),
            "priceCurrency": "EUR",
            "availability": "https://schema.org/InStock",
            "url": p.get("canonical_url") or (SITE_URL + product_href(p)),
        },
    }
    if p.get("avgRating"):
        data["aggregateRating"] = {
            "@type": "AggregateRating",
            "ratingValue": p.get("avgRating"),
            "reviewCount": p.get("reviewCount"),
        }
    return data


# ---------------------------------------------------------------------------
# Paginas
# ---------------------------------------------------------------------------

def build_db_js(products):
    payload = {
        "productos": products,
        "nichos": ["monitors"],
        "scoreAxes": SCORE_AXES,
        "updated": date.today().isoformat(),
    }
    js = "(function () {\n  \"use strict\";\n  window.__DB__ = " + json.dumps(payload, ensure_ascii=False, indent=2) + ";\n})();\n"
    with open(os.path.join(ROOT, "lib", "db.js"), "w", encoding="utf-8") as f:
        f.write(js)


def load_curiosidades():
    path = os.path.join(ROOT, "datos", "curiosidades.json")
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def render_curio_widget(c):
    return """
  <div class="curio-widget">
    <span class="curio-label">🔎 Encontrado por curiosidad</span>
    <img src="{img}" alt="{title}" loading="lazy">
    <p class="curio-title">{title}</p>
    <p class="curio-note">{note}</p>
    <p><span class="curio-price">{price}</span>&#9733; {rating}</p>
    <a class="btn btn-ghost btn-sm" href="{url}" target="_blank" rel="sponsored nofollow noopener">Ver en Amazon</a>
  </div>""".format(
        img=esc(c["image"]), title=esc(c["title"]), note=esc(c["note"]),
        price=esc(c["price"]), rating=c.get("avgRating", "—"), url=esc(c["affiliate_url"]),
    )


def render_curio_row():
    items = load_curiosidades()
    if not items:
        return ""
    widgets = "".join(render_curio_widget(c) for c in items)
    return """
<div class="curio-section">
  <span class="curio-section-label">🎲 Cosas curiosas que encontramos por el camino (nada que ver con monitores)</span>
  <div class="curio-row">{widgets}</div>
</div>""".format(widgets=widgets)


def build_index(products):
    featured = [p for p in products if p.get("isFeatured")]
    cards = "".join(render_card(p) for p in featured or products)
    cat_cards = "".join(
        '<a class="cat-entry reveal" href="{0}"><h3>{1}</h3><p>{2}</p></a>'.format(c["slug"], c["title"], c["intro"][:90] + "…")
        for c in CATEGORIES
    )
    curio_row = render_curio_row()
    body = """
<section class="hero">
  <div class="container hero-grid">
    <div>
      <span class="eyebrow">Comparativas independientes de monitores</span>
      <h1 class="reveal is-visible">Encuentra el monitor adecuado por sus datos, no por su marketing.</h1>
      <p class="lede reveal is-visible">Cada monitor en ScreenScope se desglosa en las especificaciones que realmente importan — tipo de panel, tasa de refresco, tiempo de respuesta, color, ergonomía — puntuadas siempre igual, para que puedas comparar de forma justa antes de comprar en Amazon.</p>
      <div class="hero-ctas">
        <a class="btn btn-primary" href="comparador.html">Comparar monitores</a>
        <a class="btn btn-ghost" href="guia-mejor-monitor-gaming-2026.html">Leer la guía de compra</a>
      </div>
    </div>
    <div class="trust-block">
      <div class="trust-item"><h3>Cómo puntuamos</h3><p>Cada especificación se normaliza de 0 a 10 sobre todo el catálogo, así un "8" siempre significa lo mismo.</p></div>
      <div class="trust-item"><h3>Datos reales, sin inventar</h3><p>Si falta un dato se muestra como "—", nunca un número inventado.</p></div>
      <div class="trust-item"><h3>Con afiliados</h3><p>Ganamos una comisión en las compras que cumplen los requisitos en Amazon, sin coste para ti.</p></div>
    </div>
  </div>
</section>

<section class="section container">
  <div class="section-head">
    <span class="eyebrow">Destacados</span>
    <h2>Monitores que merece la pena mirar ahora mismo</h2>
  </div>
  <div class="grid">{cards}</div>
  <div class="section-cta">
    <a class="btn btn-ghost" href="todos-los-monitores.html">Ver más monitores</a>
  </div>
</section>

<section class="section container">
  <div class="section-head">
    <span class="eyebrow">Explora por uso</span>
    <h2>¿Qué estás buscando?</h2>
  </div>
  <div class="grid">{cat_cards}</div>
  {curio_row}
</section>
""".format(cards=cards, cat_cards=cat_cards, curio_row=curio_row)
    website_jsonld = {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": BRAND["name"],
        "url": SITE_URL,
        "description": BRAND["tagline"],
    }
    html_out = page_shell(
        "ScreenScope — Comparador de Monitores Gaming, Ultrawide y para Diseño (2026)",
        "Compara monitores gaming, ultrawide y para diseño con precios reales de Amazon, puntuaciones por especificaciones y ficha técnica completa. Encuentra el mejor monitor para tu presupuesto en 2026.",
        body, active_nav="index.html", canonical="index.html",
        keywords="monitores gaming, monitor ultrawide, monitor para diseño gráfico, comparador de monitores, mejor monitor 2026, monitor barato, ofertas monitores amazon, comparativa de monitores",
        extra_jsonld=jsonld_script(website_jsonld),
    )
    write("index.html", html_out)


def build_category(cat, products):
    in_cat = [p for p in products if p["category"] == cat["key"]]
    cards = "".join(render_card(p) for p in in_cat)
    if not in_cat:
        cards = '<p style="color:var(--text-dim)">Todavía no hay monitores en esta categoría — vuelve pronto.</p>'
    body = """
<section class="section container" data-filterable>
  <div class="section-head">
    <span class="eyebrow">Categoría</span>
    <h1>{title}</h1>
    <p>{intro}</p>
  </div>
  <div class="filters">
    <select data-sort aria-label="Ordenar por">
      <option value="">Ordenar por…</option>
      <option value="price-asc">Precio: de menor a mayor</option>
      <option value="price-desc">Precio: de mayor a menor</option>
      <option value="rating-desc">Valoración: de mayor a menor</option>
    </select>
  </div>
  <div class="grid" data-products-grid>{cards}</div>
</section>
""".format(title=esc(cat["title"]), intro=esc(cat["intro"]), cards=cards)
    breadcrumb = build_jsonld_breadcrumb([("Inicio", "index.html"), (cat["title"], "")])
    item_list = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "url": SITE_URL + product_href(p), "name": p["name"]}
            for i, p in enumerate(in_cat)
        ],
    }
    html_out = page_shell(
        cat.get("seoTitle", "{0} — ScreenScope".format(cat["title"])),
        cat.get("seoDescription", cat["intro"]),
        body, active_nav=cat["slug"], canonical=cat["slug"],
        keywords=cat.get("keywords", ""),
        extra_jsonld=jsonld_script(breadcrumb, item_list),
    )
    write(cat["slug"], html_out)


def build_all_products(products):
    cards = "".join(render_card(p) for p in products)
    body = """
<section class="section container" data-filterable>
  <div class="section-head">
    <span class="eyebrow">Catálogo completo</span>
    <h1>Todos los monitores</h1>
    <p>Los {count} monitores de ScreenScope en un único listado — gaming, diseño y ultrawide juntos. Usa el orden por precio o valoración para encontrar el tuyo más rápido.</p>
  </div>
  <div class="filters">
    <select data-sort aria-label="Ordenar por">
      <option value="">Ordenar por…</option>
      <option value="price-asc">Precio: de menor a mayor</option>
      <option value="price-desc">Precio: de mayor a menor</option>
      <option value="rating-desc">Valoración: de mayor a menor</option>
    </select>
  </div>
  <div class="grid" data-products-grid>{cards}</div>
</section>
""".format(count=len(products), cards=cards)
    item_list = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "url": SITE_URL + product_href(p), "name": p["name"]}
            for i, p in enumerate(products)
        ],
    }
    breadcrumb = build_jsonld_breadcrumb([("Inicio", "index.html"), ("Todos los monitores", "")])
    html_out = page_shell(
        "Todos los Monitores: Catálogo Completo con Precios — ScreenScope",
        "Explora los {0} monitores de ScreenScope en un único listado — gaming, diseño y ultrawide — con precio real de Amazon y puntuaciones por especificación.".format(len(products)),
        body, active_nav="", canonical="todos-los-monitores.html",
        keywords="todos los monitores, catálogo de monitores, comparativa monitores 2026",
        extra_jsonld=jsonld_script(breadcrumb, item_list),
    )
    write("todos-los-monitores.html", html_out)


def build_fichas(products):
    for p in products:
        body = render_ficha(p)
        cat = next((c for c in CATEGORIES if c["key"] == p["category"]), None)
        cat_label = CAT_LABEL.get(p["category"], p["category"])
        size_kw = None
        if p.get("sizeInches"):
            n = p["sizeInches"]
            size_kw = "monitor {0} pulgadas".format(int(n) if n == int(n) else n)
        refresh_kw = None
        if p.get("refreshRateHz"):
            refresh_kw = "monitor {0}hz".format(int(p["refreshRateHz"]))
        keywords = ", ".join(filter(None, [
            p.get("brand"), "monitor {0}".format(cat_label.lower()),
            size_kw, p.get("panelType") and "panel {0}".format(p["panelType"]), refresh_kw,
            "opiniones", "precio", "ficha técnica",
        ]))
        breadcrumb_crumbs = [("Inicio", "index.html")]
        if cat:
            breadcrumb_crumbs.append((cat["title"], cat["slug"]))
        breadcrumb_crumbs.append((p["name"], ""))
        html_out = page_shell(
            "{0}: Análisis, Ficha Técnica, Precio y Opiniones — ScreenScope".format(p["name"]),
            p.get("description", ""),
            body, active_nav="", canonical=product_href(p),
            keywords=keywords,
            image=(p["images"][0] if p.get("images") else ""),
            extra_jsonld=jsonld_script(build_jsonld_breadcrumb(breadcrumb_crumbs)),
        )
        write(product_href(p), html_out)


def build_comparator():
    body = """
<section class="section container">
  <div class="section-head">
    <span class="eyebrow">Lado a lado</span>
    <h1>Comparador de monitores</h1>
    <p>Añade hasta 4 monitores y compara cada especificación, precio y puntuación del editor lado a lado. Tu selección se guarda en este navegador y se refleja en la URL para que puedas compartir una comparación.</p>
  </div>
  <div class="comparator-picker" data-comparator-picker>
    <select aria-label="Añadir un monitor a comparar"></select>
  </div>
  <div data-comparator>
    <div class="compare-empty" data-compare-empty>Todavía no has seleccionado ningún monitor. Usa el desplegable de arriba, o pulsa "Comparar" en cualquier ficha o tarjeta de producto.</div>
    <div class="compare-wrap" data-compare-wrap hidden>
      <div class="compare-cards" data-compare-cards></div>
      <div data-compare-verdict hidden></div>
      <div class="compare-specs" data-compare-specs></div>
    </div>
    <div class="compare-radar" data-compare-radar hidden>
      <h2>Comparativa de puntuaciones</h2>
      <div class="radar-wrap">
        <figure data-radar style="width:min(380px,100%)"></figure>
        <div class="radar-legend" data-radar-legend></div>
      </div>
    </div>
  </div>
</section>
"""
    html_out = page_shell(
        "Comparador de Monitores Online: Compara Especificaciones y Precios — ScreenScope",
        "Compara hasta 4 monitores lado a lado: especificaciones, precio en Amazon y puntuaciones editoriales, gratis y sin registro.",
        body, active_nav="comparador.html", canonical="comparador.html",
        keywords="comparador de monitores, comparar monitores online, comparativa monitores, especificaciones monitor, precio monitor amazon",
    )
    write("comparador.html", html_out)


def build_deals(products):
    deals = [p for p in products if p.get("retailPrice") and p.get("discountedPrice") and p["retailPrice"] > p["discountedPrice"]]
    deals.sort(key=lambda p: (p["retailPrice"] - p["discountedPrice"]) / p["retailPrice"], reverse=True)
    cards = "".join(render_card(p) for p in deals) or '<p style="color:var(--text-dim)">No hay ofertas activas ahora mismo — vuelve pronto.</p>'
    body = """
<section class="section container">
  <div class="section-head">
    <span class="eyebrow">Actualizado el {date}</span>
    <h1>Ofertas actuales</h1>
    <p>Monitores actualmente por debajo de su precio de lista, ordenados por el tamaño del descuento. Los precios son una instantánea — confirma siempre el precio actual en Amazon antes de comprar.</p>
  </div>
  <div class="grid">{cards}</div>
</section>
""".format(date=esc(date.today().isoformat()), cards=cards)
    html_out = page_shell(
        "Ofertas y Descuentos en Monitores Hoy — ScreenScope",
        "Monitores gaming, ultrawide y de diseño actualmente con descuento en Amazon, ordenados por el tamaño de la rebaja.",
        body, active_nav="ofertas.html", canonical="ofertas.html",
        keywords="ofertas monitores, descuentos monitores amazon, monitor barato oferta, chollos monitores",
    )
    write("ofertas.html", html_out)


def build_guide(products):
    gaming = sorted([p for p in products if p["category"] == "Gaming"], key=lambda p: p.get("scoreGaming", 0), reverse=True)
    shortlist_source = gaming or products
    items = ""
    for p in shortlist_source:
        items += """
      <div class="guide-item">
        <img src="{img}" alt="{name}">
        <div>
          <strong><a href="{href}">{name}</a></strong>
          <p class="why">{why}</p>
        </div>
      </div>""".format(img=esc(p["images"][0]), name=esc(p["name"]), href=product_href(p), why=esc(p.get("editorPick", "")))
    body = """
<section class="section container">
  <div class="section-head">
    <span class="eyebrow">Guía de compra</span>
    <h1>El mejor monitor gaming en 2026: cómo elegir de verdad</h1>
  </div>
  <div class="guide-body">
    <p>La mayoría de listas de "mejores monitores" ordenan solo por resolución, que es el eje equivocado para gaming. En juegos rápidos, la tasa de refresco (Hz) y el tiempo de respuesta (ms) influyen más en cómo se siente el juego que un millón de píxeles extra — y la tecnología de sincronización (FreeSync / G-Sync) decide si esa tasa de fotogramas llega sin tearing.</p>
    <h2>Qué importa realmente para gaming</h2>
    <p><strong>Tasa de refresco:</strong> 144Hz es el mínimo práctico para títulos competitivos; 240Hz importa sobre todo cuando ya alcanzas frame rates altos en esports. <strong>Tiempo de respuesta:</strong> por debajo de 5ms GtG se evita el ghosting visible; los paneles OLED lo llevan casi a cero. <strong>Tipo de panel:</strong> el IPS da el mejor color y ángulos de visión por su precio; el VA da más contraste; el OLED da contraste y velocidad a la vez, a precio premium.</p>
    <h2>Nuestra selección</h2>
    <div class="guide-shortlist">{items}</div>
    <h2>Cómo hemos puntuado</h2>
    <p>Cada monitor aquí se puntúa de 0 a 10 en seis ejes — nitidez, fluidez, color/HDR, ergonomía, preparación para gaming y calidad-precio — normalizados frente al resto de monitores de nuestro catálogo. Consulta el desglose completo en <a href="sobre-nosotros.html">cómo puntuamos</a>, o abre el <a href="comparador.html">comparador</a> para comparar cualquier par lado a lado.</p>
  </div>
</section>
""".format(items=items)
    html_out = page_shell(
        "Mejor Monitor Gaming 2026: Guía de Compra Basada en Especificaciones — ScreenScope",
        "Cómo elegir un monitor gaming por tasa de refresco, tiempo de respuesta y tecnología de sincronización, con una selección puntuada.",
        body, active_nav="guia-mejor-monitor-gaming-2026.html", canonical="guia-mejor-monitor-gaming-2026.html",
        keywords="mejor monitor gaming 2026, guía monitor gaming, cómo elegir monitor gaming, monitor 144hz vs 240hz, tiempo de respuesta monitor, freesync vs gsync",
    )
    write("guia-mejor-monitor-gaming-2026.html", html_out)


def build_legal_pages():
    about_body = """
<section class="section container">
  <div class="legal-body">
    <span class="eyebrow">Sobre ScreenScope</span>
    <h1 style="color:var(--text)">Cómo puntuamos los monitores</h1>
    <p>ScreenScope compara monitores por las especificaciones que determinan cómo se sienten realmente al usarlos, no solo por el número que aparece en la caja. Cada monitor entra en la misma base de datos con los mismos campos — tipo de panel, tasa de refresco, tiempo de respuesta, brillo, nivel de HDR, ergonomía — para que las comparaciones sean justas.</p>
    <h2>Las puntuaciones del editor</h2>
    <p>Nitidez, Fluidez, Color/HDR, Ergonomía, Gaming y Calidad-precio se puntúan cada una de 0 a 10. No son cifras del fabricante: las calculamos a partir de las especificaciones, normalizadas según el rango de monitores de nuestro catálogo, así que una puntuación solo tiene sentido en relación con los demás monitores listados aquí. Se recalculan cada vez que cambia el catálogo.</p>
    <h2>Precios</h2>
    <p>Los precios mostrados son una instantánea capturada en una fecha concreta, visible en cada ficha de producto. Los precios de Amazon cambian con frecuencia — confirma siempre el precio actual antes de comprar.</p>
    <h2>Independencia</h2>
    <p>No aceptamos pagos de fabricantes para influir en las clasificaciones o puntuaciones. Nuestros ingresos provienen del Programa de Afiliados de Amazon, indicado en cada página.</p>
  </div>
</section>
"""
    write("sobre-nosotros.html", page_shell("Cómo Puntuamos los Monitores — ScreenScope", "Cómo funcionan la puntuación editorial y los precios de ScreenScope.",
                                             about_body, active_nav="", canonical="sobre-nosotros.html"))

    disclosure_body = """
<section class="section container">
  <div class="legal-body">
    <span class="eyebrow">Legal</span>
    <h1 style="color:var(--text)">Aviso de Afiliados</h1>
    <p>ScreenScope participa en el Programa de Afiliados de Amazon EU, un programa de publicidad para afiliados diseñado para ofrecer a los sitios web un medio de obtener comisiones publicitando y enlazando a Amazon.es y otros sitios de Amazon en la Unión Europea.</p>
    <p>Como afiliados de Amazon, obtenemos ingresos por las compras que cumplen los requisitos aplicables. Esto significa que si haces clic en uno de nuestros enlaces de producto y compras algo en Amazon, podemos recibir una pequeña comisión — sin coste adicional para ti.</p>
    <p>Esto no influye en los productos que decidimos destacar ni en cómo los puntuamos. Amazon, el logotipo de Amazon y los logotipos relacionados son marcas de Amazon.com, Inc. o sus filiales.</p>
  </div>
</section>
"""
    write("aviso-afiliados.html", page_shell("Aviso de Afiliados — ScreenScope", "Aviso de afiliados de ScreenScope sobre el Programa de Afiliados de Amazon.",
                                              disclosure_body, active_nav="", canonical="aviso-afiliados.html"))

    privacy_body = """
<section class="section container">
  <div class="legal-body">
    <span class="eyebrow">Legal</span>
    <h1 style="color:var(--text)">Política de Privacidad</h1>
    <p>Esta web no requiere crear una cuenta. La única información que recogemos son analíticas de visitas mediante Google Analytics, y solo si das tu consentimiento en el aviso de cookies.</p>
    <h2>Cookies</h2>
    <p>Tu selección en el comparador se guarda localmente en tu navegador (localStorage), no en un servidor, y nunca se comparte.</p>
    <p>Si aceptas el aviso de cookies, activamos <strong>Google Analytics</strong> para saber cuántas visitas recibe la web, qué páginas se ven más y desde qué país, con la IP anonimizada. Estos datos son agregados y no identifican a ninguna persona. Si rechazas el aviso, o no respondes, Google Analytics no se activa. Puedes cambiar tu decisión en cualquier momento borrando los datos de este sitio en la configuración de tu navegador.</p>
    <p>Amazon puede establecer sus propias cookies en cuanto haces clic hacia amazon.es, según la política de privacidad propia de Amazon.</p>
    <h2>Contacto</h2>
    <p>Las preguntas sobre esta política pueden enviarse al propietario de la web.</p>
  </div>
</section>
"""
    write("privacidad.html", page_shell("Política de Privacidad — ScreenScope", "Política de privacidad de ScreenScope.",
                                         privacy_body, active_nav="", canonical="privacidad.html"))


def write(rel_path, content):
    full = os.path.join(ROOT, rel_path)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)
    print("  wrote", rel_path)


def build_sitemap(products):
    today = date.today().isoformat()
    urls = [("index.html", "1.0", "weekly")]
    urls += [(cat["slug"], "0.9", "weekly") for cat in CATEGORIES]
    urls += [
        ("comparador.html", "0.8", "weekly"),
        ("todos-los-monitores.html", "0.8", "weekly"),
        ("ofertas.html", "0.8", "daily"),
        ("guia-mejor-monitor-gaming-2026.html", "0.8", "monthly"),
    ]
    urls += [(product_href(p), "0.7", "weekly") for p in products]
    urls += [(path, "0.3", "yearly") for path in ("sobre-nosotros.html", "aviso-afiliados.html", "privacidad.html")]
    entries = "".join(
        "  <url><loc>{0}{1}</loc><lastmod>{2}</lastmod><changefreq>{3}</changefreq><priority>{4}</priority></url>\n"
        .format(SITE_URL, path, today, freq, prio)
        for path, prio, freq in urls
    )
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
           + entries + "</urlset>\n")
    write("sitemap.xml", xml)


def build_robots():
    txt = "User-agent: *\nAllow: /\n\nSitemap: {0}sitemap.xml\n".format(SITE_URL)
    write("robots.txt", txt)


def cleanup_old_pages():
    """Elimina los HTML generados con los slugs antiguos en inglés."""
    old = ["category-gaming.html", "category-design.html", "category-ultrawide.html",
           "comparator.html", "deals.html", "guide-best-gaming-monitor.html",
           "about.html", "affiliate-disclosure.html", "privacy.html"]
    for name in old:
        path = os.path.join(ROOT, name)
        if os.path.exists(path):
            os.remove(path)
            print("  removed old", name)


def cleanup_stale_fichas(products):
    """Borra fichas monitor-*.html de productos que ya no estan en productos.json."""
    valid = {product_href(p) for p in products}
    for name in os.listdir(ROOT):
        if name.startswith("monitor-") and name.endswith(".html") and name not in valid:
            os.remove(os.path.join(ROOT, name))
            print("  removed stale ficha", name)


def main():
    global DEFAULT_OG_IMAGE
    products = load_products()
    print("Generando ScreenScope ({0} productos)…".format(len(products)))
    cleanup_old_pages()
    cleanup_stale_fichas(products)
    featured = next((p for p in products if p.get("isFeatured") and p.get("images")), None)
    fallback = next((p for p in products if p.get("images")), None)
    chosen = featured or fallback
    DEFAULT_OG_IMAGE = chosen["images"][0] if chosen else ""
    build_db_js(products)
    build_index(products)
    for cat in CATEGORIES:
        build_category(cat, products)
    build_all_products(products)
    build_fichas(products)
    build_comparator()
    build_deals(products)
    build_guide(products)
    build_legal_pages()
    build_sitemap(products)
    build_robots()
    print("\nListo. VER = {0}".format(VER))


if __name__ == "__main__":
    sys.exit(main())
