#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gerador da Identidade Visual NEXUS AI (cérebro cibernético).
Produz SVGs vetoriais autorais em assets/ e um guia em brand/guide.html.
"""
import os, math, datetime

OUT = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(OUT, "assets")
BRAND = os.path.join(OUT, "brand")
os.makedirs(ASSETS, exist_ok=True)
os.makedirs(BRAND, exist_ok=True)

FONT = "'Orbitron','Exo 2','Bank Gothic','Eurostile','Arial Narrow',sans-serif"

# ----------------------------------------------------------------------------
# Geometria do contorno do cérebro (vista superior, simétrico em x=120)
# ----------------------------------------------------------------------------
RIGHT = [
    (120, 26), (138, 28), (152, 34), (166, 36), (182, 50), (194, 68),
    (198, 90), (196, 112), (188, 132), (190, 150), (176, 168),
    (150, 180), (126, 186), (120, 188),
]

def mirror_pts(pts):
    return [(240 - x, y) for (x, y) in pts]

loop = RIGHT + mirror_pts(RIGHT[::-1][1:-1])

def catmull_closed(points):
    n = len(points)
    d = "M %.1f %.1f " % points[0]
    for i in range(n):
        p0 = points[(i - 1) % n]; p1 = points[i]
        p2 = points[(i + 1) % n]; p3 = points[(i + 2) % n]
        b1 = (p1[0] + (p2[0] - p0[0]) / 6.0, p1[1] + (p2[1] - p0[1]) / 6.0)
        b2 = (p2[0] - (p3[0] - p1[0]) / 6.0, p2[1] - (p3[1] - p1[1]) / 6.0)
        d += "C %.1f %.1f %.1f %.1f %.1f %.1f " % (b1[0], b1[1], b2[0], b2[1], p2[0], p2[1])
    return d + "Z"

BRAIN_D = catmull_closed(loop)

# Sulcos (curvas internas) — pares espelhados
SULCI = [
    "M150 52 C 170 74, 172 104, 154 134",
    "M168 60 C 186 86, 184 120, 166 146",
    "M134 70 C 120 92, 120 120, 136 150",
    "M112 60 C 96 86, 98 120, 116 146",
]

# Traços de circuito (com nós) — gerados dentro do cérebro
def circuit_traces():
    s = []
    # horizontais
    for y in (66, 92, 118, 144):
        s.append("M70 %d L176 %d" % (y, y))
    # verticais/ramos
    s.append("M120 40 L120 170")
    s.append("M120 92 L150 92")
    s.append("M120 118 L96 118")
    s.append("M90 66 L90 144")
    s.append("M150 66 L150 144")
    return s

TRACE_PATHS = circuit_traces()
NODES = [(120, 40), (120, 92), (120, 118), (120, 170), (150, 92), (96, 118),
         (90, 66), (90, 144), (150, 66), (150, 144), (70, 66), (176, 144),
         (70, 118), (176, 92)]

def hex_points(cx, cy, r, rot=0):
    pts = []
    for i in range(6):
        a = math.radians(60 * i - 90 + rot)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return " ".join("%.1f,%.1f" % p for p in pts)

# ----------------------------------------------------------------------------
# Defs por modo de cor
# ----------------------------------------------------------------------------
def defs_color():
    return """
  <defs>
    <linearGradient id="brainFill" x1="0" y1="0" x2="0.4" y2="1">
      <stop offset="0%" stop-color="#13283b"/>
      <stop offset="55%" stop-color="#0c1827"/>
      <stop offset="100%" stop-color="#08111c"/>
    </linearGradient>
    <linearGradient id="metal" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#cfe8f5"/>
      <stop offset="35%" stop-color="#5b7c8e"/>
      <stop offset="60%" stop-color="#9fb9c6"/>
      <stop offset="100%" stop-color="#3a4d59"/>
    </linearGradient>
    <radialGradient id="coreGlow" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#f2feff"/>
      <stop offset="30%" stop-color="#7df9ff"/>
      <stop offset="70%" stop-color="#00aef0"/>
      <stop offset="100%" stop-color="#063a55" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="trace" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#0a7cff"/>
      <stop offset="50%" stop-color="#00aef0"/>
      <stop offset="100%" stop-color="#2dd4ff"/>
    </linearGradient>
    <radialGradient id="spark" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#ffffff"/>
      <stop offset="40%" stop-color="#aef6ff"/>
      <stop offset="100%" stop-color="#00aef0" stop-opacity="0"/>
    </radialGradient>
    <filter id="glow" x="-60%" y="-60%" width="220%" height="220%">
      <feGaussianBlur stdDeviation="6" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <filter id="soft" x="-80%" y="-80%" width="260%" height="260%">
      <feGaussianBlur stdDeviation="2.2"/>
    </filter>
    <clipPath id="brainClip"><path d="__BRAIN__"/></clipPath>
  </defs>""".replace("__BRAIN__", BRAIN_D)

def palette(mode):
    if mode == "color":
        return dict(brain="url(#brainFill)", edge="#2dd4ff", edgew=2.6,
                    sulci="#1d4a63", fissure="#37e0ff", trace="url(#trace)",
                    node="#aef6ff", core="url(#coreGlow)", bolt="url(#metal)",
                    boltedge="#0a2230", spark="url(#spark)", glow=True,
                    text="#eaf6ff", tag="#2dd4ff", sign="#7e8ba3")
    if mode == "mono":
        c = "#00aef0"
        return dict(brain=c, edge=c, edgew=2.4, sulci=c, fissure=c, trace=c,
                    node=c, core=c, bolt=c, boltedge=c, spark=c, glow=False,
                    text=c, tag=c, sign=c)
    # negative
    c = "#ffffff"
    return dict(brain=c, edge=c, edgew=2.4, sulci=c, fissure=c, trace=c,
                node=c, core=c, bolt=c, boltedge=c, spark=c, glow=False,
                text=c, tag=c, sign=c)

# ----------------------------------------------------------------------------
# Símbolo do cérebro
# ----------------------------------------------------------------------------
def brain_symbol(mode="color", detail="full"):
    p = palette(mode)
    glow = p["glow"]
    g = ['<g>']
    # corpo do cérebro
    g.append('<path d="%s" fill="%s" stroke="%s" stroke-width="%s" stroke-linejoin="round"/>'
             % (BRAIN_D, p["brain"], p["edge"], p["edgew"]))
    clip = ' clip-path="url(#brainClip)"' if mode == "color" else ''
    inner = ['<g%s>' % clip]
    # sulcos
    for s in SULCI:
        inner.append('<path d="%s" fill="none" stroke="%s" stroke-width="1.6" stroke-linecap="round" opacity="0.85"/>' % (s, p["sulci"]))
    # fissura central
    inner.append('<path d="M120 30 C 113 64, 127 96, 120 122 S 113 158, 120 186" fill="none" stroke="%s" stroke-width="2.2" stroke-linecap="round"/>' % p["fissure"])
    # circuitos
    for t in TRACE_PATHS:
        inner.append('<path d="%s" fill="none" stroke="%s" stroke-width="1.5" opacity="0.9" stroke-linecap="round"/>' % (t, p["trace"]))
    for (nx, ny) in NODES:
        inner.append('<circle cx="%d" cy="%d" r="2.6" fill="%s"/>' % (nx, ny, p["node"]))
    inner.append('</g>')
    g += inner
    # núcleo luminoso
    core_op = ' filter="url(#glow)"' if glow else ''
    g.append('<ellipse cx="120" cy="108" rx="30" ry="34" fill="%s" opacity="0.95"%s/>' % (p["core"], core_op))
    g.append('<ellipse cx="120" cy="108" rx="13" ry="15" fill="%s" opacity="0.95"/>' % (p["core"] if mode=="color" else p["core"]))
    # parafusos de fixação (topo)
    for bx in (82, 158):
        g.append('<polygon points="%s" fill="%s" stroke="%s" stroke-width="1.2"/>' % (hex_points(bx, 56, 7), p["bolt"], p["boltedge"]))
        g.append('<line x1="%d" y1="52" x2="%d" y2="60" stroke="%s" stroke-width="1.4"/>' % (bx, bx, p["boltedge"]))
    # engrenagem discreta (base)
    gear = []
    gc = (120, 178); gr = 11
    for i in range(10):
        a = math.radians(36 * i)
        gear.append((gc[0] + gr * math.cos(a), gc[1] + gr * math.sin(a)))
    gpts = " ".join("%.1f,%.1f" % q for q in gear)
    g.append('<polygon points="%s" fill="none" stroke="%s" stroke-width="1.3" opacity="0.8"/>' % (gpts, p["bolt"]))
    g.append('<circle cx="120" cy="178" r="5" fill="none" stroke="%s" stroke-width="1.3" opacity="0.8"/>' % p["bolt"])

    # ---- FALHA CONTROLADA À DIREITA (evolução) ----
    if detail == "full":
        fx, fy = 198, 112
        # rachadura tecnológica
        g.append('<path d="M196 92 L206 104 L200 112 L210 124 L202 134" fill="none" stroke="%s" stroke-width="1.4" opacity="0.9" stroke-linejoin="round"/>' % p["edge"])
        # parafusos saindo
        for (sx, sy) in [(208, 98), (214, 120)]:
            g.append('<polygon points="%s" fill="%s" stroke="%s" stroke-width="1" opacity="0.95"/>' % (hex_points(sx, sy, 5), p["bolt"], p["boltedge"]))
            g.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="1"/>' % (sx-3, sy, sx+3, sy, p["boltedge"]))
        # fragmentos geométricos se desprendendo
        frags = ["202,96 210,100 206,108 199,105", "212,126 220,124 218,132 211,133", "206,140 213,138 211,146 204,147"]
        for fr in frags:
            g.append('<polygon points="%s" fill="%s" stroke="%s" stroke-width="0.8" opacity="0.92"/>' % (fr, p["bolt"], p["boltedge"]))
        # faíscas elétricas azuis
        for (spx, spy) in [(204, 106), (211, 122)]:
            g.append('<circle cx="%d" cy="%d" r="9" fill="%s"%s/>' % (spx, spy, p["spark"], ' filter="url(#soft)"' if glow else ''))
            g.append('<path d="M%d %d l3 -5 l-2 4 l3 -3" fill="none" stroke="%s" stroke-width="1.4" stroke-linecap="round"/>' % (spx-1, spy+2, p["node"]))
    g.append('</g>')
    return "\n".join(g)

# ----------------------------------------------------------------------------
# Composições (lockups)
# ----------------------------------------------------------------------------
def text_block(p, cx, y_name, y_tag, y_sign, fs_name=54, fs_tag=13, fs_sign=12):
    out = []
    out.append('<text x="%d" y="%d" text-anchor="middle" font-family=%s font-size="%d" font-weight="800" letter-spacing="8" fill="%s">NEXUS AI</text>'
               % (cx, y_name, qt(FONT), fs_name, p["text"]))
    out.append('<text x="%d" y="%d" text-anchor="middle" font-family=%s font-size="%d" font-weight="600" letter-spacing="4" fill="%s">INTELIGÊNCIA • AUTOMAÇÃO • INOVAÇÃO</text>'
               % (cx, y_tag, qt(FONT), fs_tag, p["tag"]))
    out.append('<text x="%d" y="%d" text-anchor="middle" font-family=%s font-size="%d" font-weight="500" letter-spacing="1" fill="%s">Designed &amp; Developed by Pedrog1906g</text>'
               % (cx, y_sign, qt(FONT), fs_sign, p["sign"]))
    return out

def qt(s):
    return '"' + s + '"'

STYLE = ("<style>@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&amp;family=Exo+2:wght@600;800&amp;display=swap');</style>")

# 1) Logo vertical (hero)
def logo_vertical(mode):
    p = palette(mode)
    sym = brain_symbol(mode, "full")
    W, H = 360, 520
    s = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" role="img" aria-label="NEXUS AI">' % (W, H, W, H)]
    if mode == "color":
        s.append(defs_color())
    s.append(STYLE)
    # símbolo escalado para ~220 de largura, centralizado no topo
    s.append('<g transform="translate(60,18) scale(1.0)">%s</g>' % sym)
    s += text_block(p, W/2, 330, 366, 470, fs_name=54, fs_tag=13, fs_sign=12)
    s.append('</svg>')
    return "\n".join(s)

# 2) Logo horizontal
def logo_horizontal(mode):
    p = palette(mode)
    sym = brain_symbol(mode, "full")
    W, H = 600, 220
    s = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" role="img" aria-label="NEXUS AI">' % (W, H, W, H)]
    if mode == "color":
        s.append(defs_color())
    s.append(STYLE)
    s.append('<g transform="translate(20,30)">%s</g>' % sym)
    s += text_block(p, 410, 110, 142, 188, fs_name=52, fs_tag=13, fs_sign=12)
    s.append('</svg>')
    return "\n".join(s)

# 3) Símbolo apenas
def logo_symbol(mode, detail="full"):
    p = palette(mode)
    sym = brain_symbol(mode, detail)
    s = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 240" width="240" height="240" role="img" aria-label="NEXUS AI Symbol">' ]
    if mode == "color":
        s.append(defs_color())
    s.append(sym)
    s.append('</svg>')
    return "\n".join(s)

# 4) Wordmark apenas
def logo_wordmark(mode):
    p = palette(mode)
    W, H = 460, 150
    s = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" role="img" aria-label="NEXUS AI">' % (W, H, W, H)]
    s.append(STYLE)
    s += text_block(p, W/2, 70, 102, 138, fs_name=58, fs_tag=13, fs_sign=12)
    s.append('</svg>')
    return "\n".join(s)

# 5) Ícone / favicon (tile arredondado)
def icon_tile(mode, rounded=True, size=512):
    p = palette(mode)
    sym = brain_symbol(mode, "full")
    rx = 96 if rounded else 0
    s = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" role="img" aria-label="NEXUS AI">' % (size, size, size, size)]
    if mode == "color":
        s.append('<defs><radialGradient id="bgTile" cx="50%" cy="38%" r="75%">'
                 '<stop offset="0%" stop-color="#0c2233"/><stop offset="60%" stop-color="#06121d"/>'
                 '<stop offset="100%" stop-color="#020910"/></radialGradient>'
                 + defs_color().split("<defs>")[1].split("</defs>")[0] + '</defs>')
        s.append('<rect x="0" y="0" width="512" height="512" rx="%d" fill="url(#bgTile)"/>' % rx)
    else:
        s.append('<rect x="0" y="0" width="512" height="512" rx="%d" fill="#020910"/>' % rx)
    # símbolo central ~ 300px
    s.append('<g transform="translate(136,128) scale(1.5)">%s</g>' % sym)
    s.append('</svg>')
    return "\n".join(s)

# 6) Favicon minimalista (legível em 16px)
def favicon():
    s = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64" role="img" aria-label="NEXUS AI">']
    s.append('<defs><radialGradient id="fg" cx="50%" cy="45%" r="55%">'
             '<stop offset="0%" stop-color="#f2feff"/><stop offset="45%" stop-color="#2dd4ff"/>'
             '<stop offset="100%" stop-color="#0077b6"/></radialGradient></defs>')
    s.append('<circle cx="32" cy="32" r="30" fill="#020910"/>')
    s.append('<path d="%s" fill="#0c1827" stroke="#2dd4ff" stroke-width="2.2"/>' % shrink(BRAIN_D, 64))
    s.append('<ellipse cx="32" cy="33" rx="9" ry="10" fill="url(#fg)"/>')
    s.append('<path d="M32 8 C 30 20, 34 30, 32 38 S 30 52, 32 56" fill="none" stroke="#37e0ff" stroke-width="1.4"/>')
    s.append('</svg>')
    return "\n".join(s)

def shrink(d, target):
    # escala grosseira do path do cérebro (240 -> 64) centralizado
    import re
    nums = re.findall(r'-?\d+\.?\d*', d)
    # abordagem simples: reescala todos os números pares como x,y
    toks = re.findall(r'[MLCZmlcz]|-?\d+\.?\d*', d)
    out = []
    i = 0
    scale = target/240.0
    while i < len(toks):
        t = toks[i]
        if t in ('M','L','C','Z','m','l','c','z'):
            out.append(t); i += 1
        else:
            x = float(toks[i]); y = float(toks[i+1])
            out.append("%.1f" % (x*scale))
            out.append("%.1f" % (y*scale + 2))
            i += 2
    return " ".join(out)

# 7) Avatares (GitHub / Discord / X) — quadrado 512
def avatar(mode):
    return icon_tile(mode, rounded=True, size=512)

# 8) Banner corporativo
def banner():
    p = palette("color")
    sym = brain_symbol("color", "full")
    W, H = 1500, 500
    s = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" role="img" aria-label="NEXUS AI Banner">' % (W, H, W, H)]
    s.append('<defs>'
             '<linearGradient id="bBg" x1="0" y1="0" x2="1" y2="1">'
             '<stop offset="0%" stop-color="#020910"/><stop offset="55%" stop-color="#061826"/>'
             '<stop offset="100%" stop-color="#01060d"/></linearGradient>'
             '<radialGradient id="bGlow" cx="32%" cy="50%" r="55%">'
             '<stop offset="0%" stop-color="#0a3a55" stop-opacity="0.9"/>'
             '<stop offset="100%" stop-color="#0a3a55" stop-opacity="0"/></radialGradient>'
             + defs_color().split("<defs>")[1].split("</defs>")[0] + '</defs>')
    s.append('<rect width="%d" height="%d" fill="url(#bBg)"/>' % (W, H))
    # linhas de circuito discretas de fundo
    s.append('<g stroke="#0e3550" stroke-width="1" opacity="0.5">')
    for y in range(40, 500, 56):
        s.append('<line x1="0" y1="%d" x2="1500" y2="%d"/>' % (y, y))
    for x in range(60, 1500, 90):
        s.append('<line x1="%d" y1="0" x2="%d" y2="500"/>' % (x, x))
    s.append('</g>')
    s.append('<rect width="%d" height="%d" fill="url(#bGlow)"/>' % (W, H))
    # logo à esquerda
    s.append('<g transform="translate(250,150)">%s</g>' % sym)
    # texto à direita
    s.append('<text x="640" y="235" font-family=%s font-size="92" font-weight="900" letter-spacing="10" fill="#eaf6ff">NEXUS AI</text>' % qt(FONT))
    s.append('<text x="642" y="285" font-family=%s font-size="22" font-weight="600" letter-spacing="6" fill="#2dd4ff">INTELIGÊNCIA • AUTOMAÇÃO • INOVAÇÃO</text>' % qt(FONT))
    s.append('<text x="642" y="400" font-family=%s font-size="18" font-weight="500" letter-spacing="2" fill="#7e8ba3">Designed &amp; Developed by Pedrog1906g</text>' % qt(FONT))
    s.append('<line x1="642" y1="330" x2="1380" y2="330" stroke="#12384f" stroke-width="2"/>')
    # barra de profundidade/HUD
    s.append('<g stroke="#00aef0" stroke-width="2" opacity="0.7" fill="none">'
             '<path d="M642 350 H1380"/><circle cx="642" cy="350" r="4" fill="#00aef0"/>'
             '<path d="M1380 350 l-14 -7 v14 z" fill="#00aef0"/></g>')
    s.append('</svg>')
    return "\n".join(s)

# ----------------------------------------------------------------------------
# Escrita dos arquivos
# ----------------------------------------------------------------------------
files = {
    "logo.svg": logo_vertical("color"),
    "logo-horizontal.svg": logo_horizontal("color"),
    "logo-symbol.svg": logo_symbol("color", "full"),
    "logo-wordmark.svg": logo_wordmark("color"),
    "logo-mono.svg": logo_vertical("mono"),
    "logo-negative.svg": logo_vertical("negative"),
    "icon.svg": icon_tile("color", True, 512),
    "favicon.svg": favicon(),
    "avatar-github.svg": avatar("color"),
    "avatar-discord.svg": avatar("color"),
    "avatar-x.svg": avatar("color"),
    "banner.svg": banner(),
}
for name, content in files.items():
    with open(os.path.join(ASSETS, name), "w", encoding="utf-8") as f:
        f.write(content)
    print("gerado:", name, len(content), "bytes")

# ----------------------------------------------------------------------------
# Guia de marca (HTML com SVGs embutidos)
# ----------------------------------------------------------------------------
def embed(name):
    with open(os.path.join(ASSETS, name), encoding="utf-8") as f:
        return f.read()

swatches = [
    ("#0B0F14", "Preto profundo"),
    ("#00AEEF", "Azul elétrico"),
    ("#2DD4FF", "Azul ciano"),
    ("#E6F1FF", "Branco metálico"),
    ("#3A4D59", "Cinza grafite"),
    ("#FF5252", "Vermelho (alertas)"),
]

def tile(svg, bg, label):
    return ('<div class="tile" style="background:%s"><div class="art">%s</div>'
            '<div class="cap">%s</div></div>' % (bg, svg, label))

guide = """<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>NEXUS AI — Identidade Visual</title>
<style>
  :root{--bg:#05070d;--panel:#0c111c;--cyan:#00aeef;--txt:#e6f1ff;--dim:#7e8ba3;}
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--txt);
       font-family:'Segoe UI',system-ui,sans-serif;line-height:1.5}
  header{padding:48px 24px;text-align:center;
         background:radial-gradient(60% 80% at 50% 0%,#0a3a55 0%,#05070d 70%)}
  header h1{margin:0;font-size:30px;letter-spacing:6px;font-weight:800}
  header p{color:var(--cyan);letter-spacing:3px;margin:6px 0 0;font-size:13px}
  section{max-width:1100px;margin:0 auto;padding:36px 20px}
  h2{font-size:18px;letter-spacing:3px;color:var(--cyan);border-left:3px solid var(--cyan);
     padding-left:12px;margin:0 0 18px;text-transform:uppercase}
  .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:16px}
  .tile{border:1px solid #16263a;border-radius:14px;padding:16px;text-align:center;overflow:hidden}
  .art{height:180px;display:flex;align-items:center;justify-content:center}
  .art svg{max-width:100%;max-height:170px}
  .cap{margin-top:10px;font-size:12px;color:var(--dim);letter-spacing:1px}
  .sw{display:flex;flex-wrap:wrap;gap:12px}
  .sw div{width:140px}
  .sw .c{height:64px;border-radius:10px;border:1px solid #1c2c40}
  .sw small{display:block;margin-top:6px;font-size:11px;color:var(--dim)}
  .row{display:flex;gap:16px;flex-wrap:wrap}
  .card{background:var(--panel);border:1px solid #16263a;border-radius:14px;padding:18px;flex:1;min-width:260px}
  .card h3{margin:0 0 8px;font-size:14px;letter-spacing:1px;color:var(--cyan)}
  .card ul{margin:0;padding-left:18px;color:#c4d2e2;font-size:13px}
  .sig{text-align:center;padding:30px;color:var(--dim);letter-spacing:2px;font-size:13px}
  code{background:#0a1622;padding:2px 6px;border-radius:5px;color:#7df9ff;font-size:12px}
</style></head>
<body>
<header>
  <h1>NEXUS AI</h1>
  <p>INTELIGÊNCIA • AUTOMAÇÃO • INOVAÇÃO</p>
</header>

<section>
  <h2>Símbolo — Cérebro Cibernético</h2>
  <div class="grid">
    @@SYM@@
  </div>
</section>

<section>
  <h2>Variações da Logomarca</h2>
  <div class="grid">
    @@VAR@@
  </div>
</section>

<section>
  <h2>Paleta de Cores</h2>
  <div class="sw">@@SW@@</div>
</section>

<section>
  <h2>Tipografia</h2>
  <div class="card">
    <h3>Família sugerida</h3>
    <ul>
      <li>Orbitron / Exo 2 / Bank Gothic / Eurostile (títulos e marca)</li>
      <li>Geométrica, limpa, premium — evitar fontes chamativas</li>
      <li>NEXUS AI em caixa alta com tracking amplo</li>
    </ul>
  </div>
</section>

<section>
  <h2>Uso e Aplicações</h2>
  <div class="row">
    <div class="card"><h3>Fundos</h3><ul>
      <li>Preto profundo #0B0F14</li><li>Branco (versão negativa)</li>
      <li>Escala de cinza</li><li>Splash screen / favicon / app</li>
    </ul></div>
    <div class="card"><h3>Faça</h3><ul>
      <li>Mantenha a área de respiro (padding)</li>
      <li>Use a versão negativa em fundos escuros</li>
      <li>Respeite a simetria e o núcleo luminoso</li>
    </ul></div>
    <div class="card"><h3>Não faça</h3><ul>
      <li>Não use vermelho como cor principal</li>
      <li>Não distorça o símbolo</li>
      <li>Não remova a assinatura de crédito</li>
      <li>Não exagere em neon/brilho</li>
    </ul></div>
  </div>
</section>

<section>
  <h2>Banner Corporativo</h2>
  <div class="tile" style="background:#020910">@@BAN@@<div class="cap">banner.svg — 1500×500</div></div>
</section>

<div class="sig">Designed &amp; Developed by Pedrog1906g</div>
</body></html>
"""
sym_tiles = (tile(embed("logo-symbol.svg"), "#020910", "Símbolo (cor)") +
             tile(embed("logo-symbol.svg"), "#ffffff", "Símbolo (sobre branco)") +
             tile(embed("favicon.svg"), "#020910", "Favicon 64×64"))
var_tiles = (tile(embed("logo.svg"), "#020910", "Vertical (cor)") +
             tile(embed("logo-horizontal.svg"), "#020910", "Horizontal (cor)") +
             tile(embed("logo-wordmark.svg"), "#020910", "Somente tipografia") +
             tile(embed("logo-mono.svg"), "#020910", "Monocromática") +
             tile(embed("logo-negative.svg"), "#020910", "Negativa (branco)") +
             tile(embed("icon.svg"), "#020910", "Ícone / App"))
sw_html = "".join('<div><div class="c" style="background:%s"></div><small>%s<br/>%s</small></div>' % (c, c, n) for c, n in swatches)
banner_html = embed("banner.svg")
guide = guide.replace("@@SYM@@", sym_tiles).replace("@@VAR@@", var_tiles).replace("@@SW@@", sw_html).replace("@@BAN@@", banner_html)

with open(os.path.join(BRAND, "guide.html"), "w", encoding="utf-8") as f:
    f.write(guide)
print("gerado: brand/guide.html", len(guide), "bytes")

# BRAND.md
brand_md = """# NEXUS AI — Identidade Visual

Marca de tecnologia (IA, engenharia de software, automação, inovação e segurança).
Símbolo principal: **cérebro cibernético** com falha controlada à direita (evolução).

## Conceito
- Núcleo de inteligência, processamento e consciência artificial.
- Circuitos, engrenagens discretas, placas, metal escovado, núcleo luminoso.
- Falha à direita: poucos parafusos saindo, fragmentos geométricos, rachaduras sutis e faíscas azuis — evolução, não destruição.

## Arquivos (`assets/`)
| Arquivo | Uso |
|---|---|
| `logo.svg` | Logo vertical (herói): símbolo + NEXUS AI + tagline + assinatura |
| `logo-horizontal.svg` | Lockup horizontal (símbolo + texto) |
| `logo-symbol.svg` | Somente símbolo |
| `logo-wordmark.svg` | Somente tipografia |
| `logo-mono.svg` | Monocromática |
| `logo-negative.svg` | Negativa (branco, p/ fundo escuro) |
| `icon.svg` | Ícone de aplicativo / tile arredondado |
| `favicon.svg` | Favicon 64×64 (legível em pequeno) |
| `avatar-github.svg` / `avatar-discord.svg` / `avatar-x.svg` | Avatares de rede (1:1) |
| `banner.svg` | Banner corporativo 1500×500 |

## Paleta
- Preto profundo `#0B0F14` · Azul elétrico `#00AEEF` · Azul ciano `#2DD4FF`
- Branco metálico `#E6F1FF` · Cinza grafite `#3A4D59`
- Vermelho `#FF5252` **apenas para alertas**.

## Tipografia
Orbitron / Exo 2 / Bank Gothic / Eurostile — geométrica, limpa, premium.
`NEXUS AI` em caixa alta com tracking amplo.

## Assinatura oficial
**Designed & Developed by Pedrog1906g**

## Guia visual
Abra `brand/guide.html` para ver todas as variações, paleta e regras de uso.
"""
with open(os.path.join(OUT, "BRAND.md"), "w", encoding="utf-8") as f:
    f.write(brand_md)
print("gerado: BRAND.md")
print("PRONTO.")
