##############################################################################
#   generate_assets.py — Génère les PNGs de l'interface depuis PIL
#   Exécuter UNE FOIS avant de lancer le jeu :  python generate_assets.py
##############################################################################
import os, math
from PIL import Image, ImageDraw, ImageFilter

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UI_DIR   = os.path.join(BASE_DIR, 'assets', 'ui')
os.makedirs(UI_DIR, exist_ok=True)

def save(img, name):
    path = os.path.join(UI_DIR, name)
    img.save(path)
    print(f"  OK  {name}")

# ── Utilitaires ─────────────────────────────────────────────────────────────
def heart_points(cx, cy, size):
    """Retourne la liste de points (polygon) pour un cœur centré."""
    pts = []
    for i in range(360):
        t = math.radians(i)
        x = 16 * math.sin(t) ** 3
        y = -(13*math.cos(t) - 5*math.cos(2*t) - 2*math.cos(3*t) - math.cos(4*t))
        pts.append((cx + x * size / 36, cy + y * size / 36))
    return pts

def radial_gradient(img, cx, cy, r, color_inner, color_outer):
    """Applique un dégradé radial simple sur une image RGBA existante."""
    px = img.load()
    w, h = img.size
    ri, gi, bi = color_inner
    ro, go, bo = color_outer
    for y in range(h):
        for x in range(w):
            d = math.hypot(x - cx, y - cy) / r
            d = min(d, 1.0)
            r_ = int(ri + (ro - ri) * d)
            g_ = int(gi + (go - gi) * d)
            b_ = int(bi + (bo - bi) * d)
            if px[x, y][3] > 0:
                px[x, y] = (r_, g_, b_, px[x, y][3])

# ── Cœur plein ──────────────────────────────────────────────────────────────
def make_heart_full(size=38):
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    d   = ImageDraw.Draw(img)
    cx, cy = size // 2, size // 2 + 2
    pts = heart_points(cx, cy, size * 0.85)
    d.polygon(pts, fill=(200, 20, 40, 255), outline=(100, 0, 15, 255))
    radial_gradient(img, cx - size//6, cy - size//5,
                    size * 0.55, (255, 120, 145), (180, 0, 30))
    # Reflet blanc
    hl = heart_points(cx - size//8, cy - size//5, size * 0.38)
    tmp = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(tmp).polygon(hl, fill=(255, 255, 255, 60))
    img = Image.alpha_composite(img, tmp)
    return img.filter(ImageFilter.SMOOTH)

# ── Cœur vide ───────────────────────────────────────────────────────────────
def make_heart_empty(size=38):
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    d   = ImageDraw.Draw(img)
    cx, cy = size // 2, size // 2 + 2
    pts = heart_points(cx, cy, size * 0.85)
    d.polygon(pts, fill=(30, 28, 50, 210), outline=(80, 75, 110, 220))
    return img

# ── Pièce d'or ──────────────────────────────────────────────────────────────
def make_coin(size=28):
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    d   = ImageDraw.Draw(img)
    cx = cy = size // 2
    # Ombre portée
    d.ellipse([cx-cx+2, cy-cy+3, cx+cx-1, cy+cy+2], fill=(80, 40, 0, 120))
    # Corps
    d.ellipse([1, 1, size-2, size-2], fill=(200, 140, 0, 255), outline=(140, 80, 0, 255))
    radial_gradient(img, cx - size//5, cy - size//5, size * 0.55,
                    (255, 230, 100), (170, 100, 0))
    # Cercle intérieur
    d.ellipse([size//4, size//4, size-size//4, size-size//4],
              fill=None, outline=(200, 150, 10, 140), width=1)
    # Lettre G
    d.text((cx - 3, cy - 5), "G", fill=(120, 70, 0, 200))
    # Reflet
    d.ellipse([size//5, size//5, size//2, size//2 - 1],
              fill=(255, 255, 200, 45))
    return img.filter(ImageFilter.SMOOTH)

# ── Épée (fragment) ─────────────────────────────────────────────────────────
def make_sword(w=72, h=22):
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d   = ImageDraw.Draw(img)
    cy  = h // 2
    # Lame
    d.polygon([(7, cy-2), (w-4, cy-1), (w, cy), (w-4, cy+1), (7, cy+2)],
              fill=(180, 210, 235, 255), outline=(100, 130, 160, 200))
    d.line([(9, cy), (w-6, cy)], fill=(240, 250, 255, 160), width=1)
    # Garde
    d.rectangle([4, cy-7, 9, cy+7], fill=(170, 160, 110, 255), outline=(110, 100, 60, 255))
    # Manche
    d.rectangle([0, cy-3, 6, cy+3], fill=(110, 70, 30, 255), outline=(60, 35, 10, 255))
    # Pommeau
    d.ellipse([0, cy-4, 6, cy+4], fill=(200, 160, 40, 255), outline=(130, 90, 10, 255))
    return img.filter(ImageFilter.SMOOTH)

# ── Bouclier ────────────────────────────────────────────────────────────────
def make_shield(w=30, h=38):
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d   = ImageDraw.Draw(img)
    pts = [(w//2, 2), (w-2, 6), (w-2, h*6//10), (w//2, h-2), (2, h*6//10), (2, 6)]
    # Ombre
    shadow = [(x+2, y+2) for x, y in pts]
    d.polygon(shadow, fill=(0, 0, 0, 80))
    # Corps
    d.polygon(pts, fill=(50, 80, 160, 255), outline=(180, 150, 40, 255), width=2)
    # Croix
    cx, cy = w//2, h//2 - 2
    d.rectangle([cx-2, 7, cx+2, h-10], fill=(200, 170, 40, 220))
    d.rectangle([6, cy-2, w-6, cy+2],  fill=(200, 170, 40, 220))
    # Reflet
    d.polygon([(w//2, 4), (w-4, 8), (w-4, h//3), (w//2, h//3 - 2)],
              fill=(255, 255, 255, 25))
    return img.filter(ImageFilter.SMOOTH)

# ── Parchemin ────────────────────────────────────────────────────────────────
def make_scroll(w=30, h=38):
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d   = ImageDraw.Draw(img)
    roll_h = 5
    # Corps
    d.rectangle([2, roll_h, w-2, h-roll_h], fill=(235, 210, 155, 255), outline=(150, 110, 55, 200))
    # Rouleaux haut et bas
    for cy in [roll_h, h-roll_h]:
        d.ellipse([1, cy-roll_h, w-1, cy+roll_h],
                  fill=(210, 175, 115, 255), outline=(140, 100, 45, 200))
        d.ellipse([3, cy-roll_h+2, w-3, cy+roll_h-2], fill=(230, 195, 135, 200))
    # Lignes de texte
    for ly in range(12, h-12, 5):
        w2 = w - 6 if ly == h-12 else w-4
        d.line([(4, ly), (w2, ly)], fill=(120, 80, 30, 100), width=1)
    return img.filter(ImageFilter.SMOOTH)

# ── Potion ───────────────────────────────────────────────────────────────────
def make_potion(w=22, h=36):
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d   = ImageDraw.Draw(img)
    cx  = w // 2
    # Bouchon
    d.rectangle([cx-3, 0, cx+3, 4], fill=(130, 85, 35, 255), outline=(70, 40, 10, 255))
    # Goulot
    d.rectangle([cx-4, 4, cx+4, 10], fill=(140, 180, 210, 180), outline=(80, 120, 160, 200))
    # Corps (liquide)
    body = [4, 11, w-4, h-3]
    d.ellipse(body, fill=(200, 30, 60, 230), outline=(120, 10, 30, 220))
    radial_gradient(img, cx - 3, 18, 9, (255, 100, 130), (160, 0, 30))
    # Verre overlay
    d.ellipse(body, fill=(200, 230, 255, 30))
    # Surface liquide
    d.ellipse([6, 12, w-6, 17], fill=(255, 160, 180, 60))
    # Reflet
    d.line([(6, 18), (7, 26)], fill=(255, 255, 255, 100), width=2)
    d.ellipse([w-8, 20, w-5, 24], fill=(255, 255, 255, 70))
    return img.filter(ImageFilter.SMOOTH)

# ── Boussole ──────────────────────────────────────────────────────────────────
def make_compass(size=42):
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    d   = ImageDraw.Draw(img)
    cx = cy = size // 2
    r  = size // 2 - 2
    # Cadran
    d.ellipse([2, 2, size-2, size-2], fill=(15, 14, 30, 240), outline=(192, 160, 96, 255), width=2)
    # Points cardinaux (tirets)
    for angle, length in [(0, 5), (90, 4), (180, 4), (270, 4)]:
        a = math.radians(angle - 90)
        x0 = cx + (r-1) * math.cos(a)
        y0 = cy + (r-1) * math.sin(a)
        x1 = cx + (r - length) * math.cos(a)
        y1 = cy + (r - length) * math.sin(a)
        d.line([(x0, y0), (x1, y1)], fill=(192, 160, 96, 255), width=2)
    # Aiguille Nord (rouge)
    d.polygon([(cx, cy - r + 8), (cx+3, cy), (cx, cy-4), (cx-3, cy)],
              fill=(200, 30, 50, 255), outline=(120, 0, 20, 200))
    # Aiguille Sud (blanche)
    d.polygon([(cx, cy + r - 8), (cx+3, cy), (cx, cy+4), (cx-3, cy)],
              fill=(220, 220, 230, 240), outline=(140, 140, 160, 200))
    # Pivot central
    d.ellipse([cx-3, cy-3, cx+3, cy+3], fill=(192, 160, 96, 255), outline=(120, 90, 20, 255))
    return img.filter(ImageFilter.SMOOTH)

# ── Génération ───────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print("\n[*] Generation des assets PNG...\n")
    save(make_heart_full(38),   'heart_full.png')
    save(make_heart_empty(38),  'heart_empty.png')
    save(make_coin(28),         'coin.png')
    save(make_sword(72, 22),    'sword.png')
    save(make_shield(30, 38),   'shield.png')
    save(make_scroll(30, 38),   'scroll.png')
    save(make_potion(22, 36),   'potion.png')
    save(make_compass(42),      'compass.png')
    print("\n[OK] Tous les assets ont ete crees dans assets/ui/\n")
