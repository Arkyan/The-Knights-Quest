##############################################################################
#                     IMPORTATION DES BIBLIOTHÈQUES
##############################################################################
from tkinter import *
from PIL import Image, ImageTk
from time import *
import json, os, ctypes, random, math

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except:
    pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

##############################################################################
#                     CONSTANTES GLOBALES
##############################################################################
MAX_HP       = 5
MINIMAP_SIZE = 200   # taille en pixels de la mini-carte

##############################################################################
#                     DECLARATION DE LA FENETRE
##############################################################################
fenetre = Tk()
fenetre.geometry("1920x1080")
fenetre.title("The Knight's Quest")
fenetre.iconbitmap(os.path.join(BASE_DIR, "assets/icon/chateau.ico"))

##############################################################################
#                     CRÉATION DU CANVAS
##############################################################################
canvas = Canvas(fenetre, width=1920, height=1080, bg="black")
canvas.pack()

def quit_button_event():
    exit()

##############################################################################
#                     CHARGEMENT DES IMAGES
##############################################################################
# Background — conservé en PIL pour générer la mini-carte
_bg_pil = Image.open(os.path.join(BASE_DIR, 'assets/background/background.png'))
BG_W, BG_H = _bg_pil.size

background_img_normal_src = ImageTk.PhotoImage(_bg_pil)
background_img_blur_src   = ImageTk.PhotoImage(
    Image.open(os.path.join(BASE_DIR, 'assets/background/background_blur.jpg')))

# Mini-carte (fond reduit)
_mini_pil      = _bg_pil.resize((MINIMAP_SIZE, MINIMAP_SIZE), Image.LANCZOS)
bg_minimap_src = ImageTk.PhotoImage(_mini_pil)

# Sprites du personnage
personnage_avant_src      = ImageTk.PhotoImage(Image.open(os.path.join(BASE_DIR, 'assets/personnages/marche_avant.png')))
personnage_arriere_src    = ImageTk.PhotoImage(Image.open(os.path.join(BASE_DIR, 'assets/personnages/marche_arri\u00e8re.png')))
personnage_gauche_src     = ImageTk.PhotoImage(Image.open(os.path.join(BASE_DIR, 'assets/personnages/marche_gauche.png')))
personnage_droite_src     = ImageTk.PhotoImage(Image.open(os.path.join(BASE_DIR, 'assets/personnages/marche_droite.png')))

# Boutons
play_button_src           = ImageTk.PhotoImage(Image.open(os.path.join(BASE_DIR, "assets/buttons/start_button.png")))
quit_button_src           = ImageTk.PhotoImage(Image.open(os.path.join(BASE_DIR, "assets/buttons/quit_button.png")))
resume_button_src         = ImageTk.PhotoImage(Image.open(os.path.join(BASE_DIR, "assets/buttons/resume_button.png")))
menu_principal_button_src = ImageTk.PhotoImage(Image.open(os.path.join(BASE_DIR, "assets/buttons/menu_principal_button.png")))

# Assets UI (generes par generate_assets.py — chargement silencieux si absents)
def _load_ui(name, size=None):
    p = os.path.join(BASE_DIR, 'assets', 'ui', name)
    if not os.path.exists(p):
        return None
    img = Image.open(p)
    if size:
        img = img.resize(size, Image.LANCZOS)
    return ImageTk.PhotoImage(img)

heart_full_src  = _load_ui('heart_full.png',  (36, 36))
heart_empty_src = _load_ui('heart_empty.png', (36, 36))
coin_src        = _load_ui('coin.png',         (24, 24))
compass_src     = _load_ui('compass.png',      (36, 36))
scroll_src      = _load_ui('scroll.png',       (20, 26))
potion_src      = _load_ui('potion.png',       (16, 26))
UI_OK = all(x is not None for x in [heart_full_src, heart_empty_src, coin_src])

##############################################################################
#                     ETAT GLOBAL DU MENU
##############################################################################
_menu_actif = [False]
_menu_stars  = []   # tuples (canvas_id, speed_y, drift_x)

##############################################################################
#                     FONCTION PRINCIPALE DU JEU
##############################################################################
def play_button_event(variable):
    global personnage
    _menu_actif[0] = False
    canvas.delete("all")

    background_img_normal = canvas.create_image(0, 0, anchor=NW, image=background_img_normal_src)
    personnage = canvas.create_image(960, 540, anchor=NW, image=personnage_avant_src)
    canvas.move(background_img_normal, -2760, -4240)

    with open(os.path.join(BASE_DIR, 'data.json'), encoding='utf-8') as f:
        data = json.load(f)

    collision_info     = {c['id']: c for c in data['collisions']}
    quete_by_collision = {q['id_collision']: q for q in data['quetes'] if q.get('id_collision')}
    quetes_completees  = set(data.get('quetes_completees', []))

    dialogue_en_cours  = [False]
    dialogue_last_zone = [None]

    # ── Zones de collision (invisibles) + indicateurs "!" ────────────────────
    rectangles      = []
    indicateurs_npc = {}

    for i in data['collisions']:
        rect = canvas.create_rectangle(i["x1"], i["y1"], i["x2"], i["y2"],
                                        fill="", outline="", tags='collision')
        rectangles.append(rect)
        if i["color"] == "green":
            quete = quete_by_collision.get(i["id"])
            if quete and i["id"] not in quetes_completees:
                cx = (i["x1"] + i["x2"]) // 2
                cy = i["y1"] - 25
                ind = canvas.create_text(cx, cy, text="!", fill="#FFD700",
                                          font=('Helvetica 26 bold'), tags='indicator')
                indicateurs_npc[i["id"]] = ind

    coord_carres = [[i["x1"], i["y1"], i["x2"], i["y2"], i["id"]] for i in data['collisions']]

    # ── Debug ─────────────────────────────────────────────────────────────────
    debug_mode   = [False]
    debug_labels = [None] * len(rectangles)

    debug_bg         = canvas.create_rectangle(5, 5, 460, 125, fill="#000000",
                                               outline="#555555", state='hidden')
    debug_coords     = canvas.create_text(10, 10, anchor=NW, text="", fill="#00ff00",
                                          font=('Courier 11 bold'), state='hidden')
    debug_perso_rect = canvas.create_rectangle(0, 0, 0, 0, outline="cyan",
                                               width=2, dash=(4, 4), state='hidden')

    def mettre_a_jour_debug():
        if not debug_mode[0]:
            return
        coords = canvas.bbox(personnage)
        if coords:
            cx = (coords[0] + coords[2]) // 2
            cy = (coords[1] + coords[3]) // 2
            w  = coords[2] - coords[0]
            h  = coords[3] - coords[1]
            bg_pos = canvas.coords(background_img_normal)
            data_x = int(cx - bg_pos[0] - 2760)
            data_y = int(cy - bg_pos[1] - 4240)
            canvas.itemconfig(debug_coords,
                text=f"[F3] DEBUG\n"
                     f"canvas:    x={cx}  y={cy}\n"
                     f"data.json: x={data_x}  y={data_y}\n"
                     f"perso bbox: {w}x{h} px")
            canvas.coords(debug_perso_rect, coords[0], coords[1], coords[2], coords[3])
        canvas.lift(debug_bg)
        canvas.lift(debug_coords)
        canvas.lift(debug_perso_rect)

    def toggle_debug(e=None):
        debug_mode[0] = not debug_mode[0]
        if debug_mode[0]:
            bg_pos = canvas.coords(background_img_normal)
            for i, rect in enumerate(rectangles):
                cid   = coord_carres[i][4]
                color = collision_info.get(cid, {}).get('color', 'white')
                if color == 'red':
                    outline = "red"
                elif color == 'green':
                    outline = "#00ff00"
                else:
                    outline = "#ff8800"  # zones piege = orange
                canvas.itemconfig(rect, fill="", outline=outline, width=2)
                x1 = int(coord_carres[i][0] - bg_pos[0] - 2760)
                y1 = int(coord_carres[i][1] - bg_pos[1] - 4240)
                x2 = int(coord_carres[i][2] - bg_pos[0] - 2760)
                y2 = int(coord_carres[i][3] - bg_pos[1] - 4240)
                cx1, cy1 = coord_carres[i][0], coord_carres[i][1]
                cx2, cy2 = coord_carres[i][2], coord_carres[i][3]
                rx  = (cx1 + cx2) // 2
                ry  = (cy1 + cy2) // 2
                items = [
                    canvas.create_text(cx1, cy1, text=f"x1={x1}\ny1={y1}", fill=outline, font=('Courier 7'), anchor=NW),
                    canvas.create_text(cx2, cy1, text=f"x2={x2}\ny1={y1}", fill=outline, font=('Courier 7'), anchor=NE),
                    canvas.create_text(cx1, cy2, text=f"x1={x1}\ny2={y2}", fill=outline, font=('Courier 7'), anchor=SW),
                    canvas.create_text(cx2, cy2, text=f"x2={x2}\ny2={y2}", fill=outline, font=('Courier 7'), anchor=SE),
                    canvas.create_text(rx,  ry,  text=f"id={cid}",          fill=outline, font=('Courier 9 bold'), anchor=CENTER),
                ]
                debug_labels[i] = items
            canvas.itemconfig(debug_bg,         state='normal')
            canvas.itemconfig(debug_coords,     state='normal')
            canvas.itemconfig(debug_perso_rect, state='normal')
            mettre_a_jour_debug()
        else:
            for i, rect in enumerate(rectangles):
                canvas.itemconfig(rect, fill="", outline="")
            for i, lbls in enumerate(debug_labels):
                if lbls:
                    for lbl in lbls:
                        canvas.delete(lbl)
                    debug_labels[i] = None
            canvas.itemconfig(debug_bg,         state='hidden')
            canvas.itemconfig(debug_coords,     state='hidden')
            canvas.itemconfig(debug_perso_rect, state='hidden')

    # ── Animation "!" clignotant ──────────────────────────────────────────
    def animer_indicateurs():
        for ind in indicateurs_npc.values():
            c = canvas.itemcget(ind, "fill")
            canvas.itemconfig(ind, fill="#FFD700" if c == "#cc9900" else "#cc9900")
        fenetre.after(600, animer_indicateurs)

    animer_indicateurs()

    # ── HUD : etat ──────────────────────────────────────────────────────────
    hp              = [MAX_HP]
    gold            = [0]
    damage_cooldown = [0]

    # ── Mini-carte ───────────────────────────────────────────────────────────
    MM_X = 1920 - MINIMAP_SIZE - 15
    MM_Y = 15
    mm_bg    = canvas.create_image(MM_X, MM_Y, anchor=NW, image=bg_minimap_src, tags='minimap')
    mm_frame = canvas.create_rectangle(MM_X-2, MM_Y-2,
                                        MM_X+MINIMAP_SIZE+2, MM_Y+MINIMAP_SIZE+2,
                                        outline='#c0a060', width=2, fill='', tags='minimap')
    mm_dot   = canvas.create_oval(0, 0, 10, 10, fill='#ff3344', outline='white',
                                   width=1, tags='minimap')
    canvas.create_text(MM_X + MINIMAP_SIZE//2, MM_Y - 14,
                        text='Carte', fill='#c0a060',
                        font=('Helvetica 10 bold'), tags='minimap')
    if compass_src:
        canvas.create_image(MM_X + MINIMAP_SIZE - 2, MM_Y + MINIMAP_SIZE - 2,
                             anchor=SE, image=compass_src, tags='minimap')

    # ── Coeurs (barre de vie) ────────────────────────────────────────────────
    HUD_X, HUD_Y = 12, 12
    canvas.create_rectangle(HUD_X-2, HUD_Y-2,
                             HUD_X + MAX_HP*42 + 2, HUD_Y + 48,
                             fill='#1a1a2e', outline='#c0a060', width=2, tags='hud')
    hearts = []
    for i in range(MAX_HP):
        x = HUD_X + i * 42 + 3
        if UI_OK:
            h = canvas.create_image(x, HUD_Y + 5, anchor=NW, image=heart_full_src, tags='hud')
        else:
            h = canvas.create_text(x + 16, HUD_Y + 24, text='♥', fill='#cc2233',
                                    font=('Helvetica 26 bold'), tags='hud')
        hearts.append(h)

    # ── Or ───────────────────────────────────────────────────────────────────
    gold_y = HUD_Y + 56
    canvas.create_rectangle(HUD_X-2, gold_y-2, HUD_X + 170, gold_y + 30,
                             fill='#1a1a2e', outline='#c0a060', width=1, tags='hud')
    if coin_src:
        canvas.create_image(HUD_X + 2, gold_y + 1, anchor=NW, image=coin_src, tags='hud')
        gold_text = canvas.create_text(HUD_X + 34, gold_y + 14, anchor=W,
                                        text="0  pieces", fill='#FFD700',
                                        font=('Helvetica 12 bold'), tags='hud')
    else:
        gold_text = canvas.create_text(HUD_X + 10, gold_y + 14, anchor=W,
                                        text="0  pieces", fill='#FFD700',
                                        font=('Helvetica 12 bold'), tags='hud')

    # ── Fonctions HUD ─────────────────────────────────────────────────────────
    def lift_hud():
        canvas.tag_raise('minimap')
        canvas.tag_raise('hud')
        canvas.tag_raise('notification')

    def update_hud():
        for i, h in enumerate(hearts):
            if UI_OK:
                canvas.itemconfig(h, image=(heart_full_src if i < hp[0] else heart_empty_src))
            else:
                canvas.itemconfig(h, fill=('#cc2233' if i < hp[0] else '#333350'))
        canvas.itemconfig(gold_text, text=f"{gold[0]}  pieces")
        lift_hud()

    def update_minimap():
        bg_pos = canvas.coords(background_img_normal)
        bbox   = canvas.bbox(personnage)
        if not bbox:
            return
        cx = (bbox[0] + bbox[2]) / 2
        cy = (bbox[1] + bbox[3]) / 2
        wx = cx - bg_pos[0]
        wy = cy - bg_pos[1]
        dx = MM_X + int(wx / BG_W * MINIMAP_SIZE)
        dy = MM_Y + int(wy / BG_H * MINIMAP_SIZE)
        dx = max(MM_X + 5, min(MM_X + MINIMAP_SIZE - 5, dx))
        dy = max(MM_Y + 5, min(MM_Y + MINIMAP_SIZE - 5, dy))
        canvas.coords(mm_dot, dx - 5, dy - 5, dx + 5, dy + 5)
        canvas.tag_raise('minimap')

    update_minimap()

    # ── Notifications toast ───────────────────────────────────────────────────
    _notif_items = []
    _notif_job   = [None]

    def show_notification(text, color='#90ee90', duration=3000):
        for item in _notif_items:
            canvas.delete(item)
        _notif_items.clear()
        if _notif_job[0]:
            fenetre.after_cancel(_notif_job[0])
        bg  = canvas.create_rectangle(560, 8, 1360, 52,
                                       fill='#1a1a2e', outline='#c0a060', width=2, tags='notification')
        txt = canvas.create_text(960, 30, text=text, fill=color,
                                  font=('Helvetica 14 bold'), tags='notification')
        _notif_items.extend([bg, txt])
        canvas.tag_raise('notification')
        def _hide():
            for item in _notif_items:
                canvas.delete(item)
            _notif_items.clear()
        _notif_job[0] = fenetre.after(duration, _hide)

    # ── Degats et zones pieges ────────────────────────────────────────────────
    def prendre_degats(montant=1):
        if damage_cooldown[0] > 0:
            return
        hp[0] = max(0, hp[0] - montant)
        damage_cooldown[0] = 90
        update_hud()
        show_notification(f"  -{montant} PV  ", '#ff4455', 1500)
        flash = canvas.create_rectangle(0, 0, 1920, 1080, fill='#ff0000',
                                         stipple='gray25', tags='flash')
        fenetre.after(130, lambda: canvas.delete(flash))
        if hp[0] <= 0:
            fenetre.after(350, afficher_game_over)

    def tick_cooldown():
        if damage_cooldown[0] > 0:
            damage_cooldown[0] -= 1
        fenetre.after(16, tick_cooldown)

    tick_cooldown()

    # ── Victoire / Game Over ──────────────────────────────────────────────────
    def check_victory():
        with open(os.path.join(BASE_DIR, 'data.json'), encoding='utf-8') as f:
            d = json.load(f)
        actives    = {q['id'] for q in d['quetes'] if q.get('id_collision')}
        completees = set(d.get('quetes_completees', []))
        if actives and actives.issubset(completees):
            fenetre.after(900, afficher_victoire)

    def _unbind_all():
        for key in ('<Left>', '<Right>', '<Up>', '<Down>',
                    '<Escape>', '<Tab>', '<F1>', '<F2>', '<F3>', '<Return>'):
            fenetre.unbind(key)

    def afficher_victoire():
        _unbind_all()
        with open(os.path.join(BASE_DIR, 'data.json'), encoding='utf-8') as f:
            d = json.load(f)

        overlay = canvas.create_rectangle(0, 0, 1920, 1080, fill='#000000', stipple='gray50')
        items   = [overlay]
        items.append(canvas.create_text(964, 294, text='VICTOIRE',
                                         fill='#6a4a00', font=('Helvetica 70 bold')))
        items.append(canvas.create_text(960, 290, text='VICTOIRE',
                                         fill='#FFD700', font=('Helvetica 70 bold')))
        items.append(canvas.create_text(960, 400,
                                         text="Tu as accompli toutes les quetes du royaume !",
                                         fill='white', font=('Helvetica 20')))
        items.append(canvas.create_text(960, 460,
                                         text=f"Or amasse : {gold[0]} pieces",
                                         fill='#FFD700', font=('Helvetica 18')))
        items.append(canvas.create_text(960, 515,
                                         text=f"Temps de jeu : {d['playtime']} min",
                                         fill='#aaaaaa', font=('Helvetica 15')))
        items.append(canvas.create_line(560, 555, 1360, 555, fill='#c0a060', width=1))

        # Etoiles filantes
        stars_v = []
        for _ in range(70):
            x = random.randint(0, 1920)
            y = random.randint(0, 530)
            r = random.randint(1, 4)
            s = canvas.create_oval(x-r, y-r, x+r, y+r,
                                    fill=random.choice(['#FFD700', 'white', '#ffa0c0']),
                                    outline='')
            stars_v.append((s, random.uniform(0.6, 2.2)))
            items.append(s)

        def animate_stars():
            if not items:
                return
            for s, sp in stars_v:
                try:
                    canvas.move(s, 0, sp)
                    c = canvas.coords(s)
                    if c and c[1] > 580:
                        x = random.randint(0, 1920)
                        canvas.coords(s, x-2, -6, x+2, -2)
                except:
                    pass
            fenetre.after(28, animate_stars)

        animate_stars()

        btn = canvas.create_text(960, 640,
                                  text='[ Entree  —  Menu Principal ]',
                                  fill='#c0a060', font=('Helvetica 18 bold'))
        items.append(btn)

        def retour(e=None):
            items.clear()
            fenetre.unbind('<Return>')
            canvas.delete('all')
            afficher_menu_principal()

        canvas.tag_bind(btn, '<Button-1>', retour)
        fenetre.bind('<Return>', retour)

    def afficher_game_over():
        _unbind_all()
        overlay = canvas.create_rectangle(0, 0, 1920, 1080, fill='#0d0000', stipple='gray25')
        items   = [overlay]
        items.append(canvas.create_text(960, 360, text='GAME  OVER',
                                         fill='#cc2233', font=('Helvetica 72 bold')))
        items.append(canvas.create_text(960, 460,
                                         text="Le chevalier est tombe au combat...",
                                         fill='#888888', font=('Helvetica 20')))
        items.append(canvas.create_text(960, 520,
                                         text=f"Or amasse : {gold[0]} pieces",
                                         fill='#666666', font=('Helvetica 15')))
        items.append(canvas.create_line(560, 560, 1360, 560, fill='#441111', width=1))

        btn_r = canvas.create_text(760, 640, text='[ Recommencer ]',
                                    fill='#c0a060', font=('Helvetica 18 bold'))
        btn_m = canvas.create_text(1160, 640, text='[ Menu Principal ]',
                                    fill='#c0a060', font=('Helvetica 18 bold'))
        items += [btn_r, btn_m]

        def recommencer(e=None):
            items.clear()
            fenetre.unbind('<Return>')
            canvas.delete('all')
            play_button_event(canvas)

        def retour(e=None):
            items.clear()
            fenetre.unbind('<Return>')
            canvas.delete('all')
            afficher_menu_principal()

        canvas.tag_bind(btn_r, '<Button-1>', recommencer)
        canvas.tag_bind(btn_m, '<Button-1>', retour)
        fenetre.bind('<Return>', recommencer)

    # ── Sauvegarde d'une quete completee ─────────────────────────────────────
    def sauvegarder_quete_complete(quete_id, zone_id):
        with open(os.path.join(BASE_DIR, 'data.json'), 'r+', encoding='utf-8') as f:
            d = json.load(f)
            completees = d.get('quetes_completees', [])
            if quete_id not in completees:
                completees.append(quete_id)
            d['quetes_completees'] = completees
            f.seek(0)
            json.dump(d, f, indent=4, ensure_ascii=False)
            f.truncate()

        quete_info = next((q for q in data['quetes'] if q['id'] == quete_id), None)
        reward = quete_info.get('reward_gold', 10) if quete_info else 10
        gold[0] += reward
        update_hud()

        titre = quete_info.get('title', f'Quete {quete_id}') if quete_info else f'Quete {quete_id}'
        show_notification(f"  Quete accomplie : {titre}  +{reward} pieces  ", '#90ee90')

        quetes_completees.add(zone_id)
        if zone_id in indicateurs_npc:
            canvas.delete(indicateurs_npc[zone_id])
            del indicateurs_npc[zone_id]

        check_victory()

    # ── Affichage du dialogue ─────────────────────────────────────────────────
    def afficher_dialogue(lignes, speaker="", quete_id=None, zone_id=None):
        dialogue_en_cours[0] = True
        fenetre.unbind("<Left>"); fenetre.unbind("<Right>")
        fenetre.unbind("<Up>");   fenetre.unbind("<Down>")
        fenetre.unbind("<Tab>")

        index          = [0]
        items_dialogue = []

        boite = canvas.create_rectangle(200, 840, 1720, 1020,
                                         fill="#1a1a2e", outline="#c0a060", width=3)
        items_dialogue.append(boite)

        if speaker:
            nom_boite = canvas.create_rectangle(200, 800, 440, 845,
                                                 fill="#1a1a2e", outline="#c0a060", width=2)
            nom_texte = canvas.create_text(320, 822, text=speaker,
                                            fill="#FFD700", font=('Helvetica 14 bold'))
            items_dialogue += [nom_boite, nom_texte]
            if scroll_src:
                icn = canvas.create_image(448, 822, anchor=W, image=scroll_src)
                items_dialogue.append(icn)

        texte      = canvas.create_text(960, 925, text=lignes[0],
                                         fill="white", font=('Helvetica 16'), width=1400)
        indicateur = canvas.create_text(1690, 1008, text="> Espace / Clic",
                                         fill="#c0a060", font=('Helvetica 11'))
        compteur   = canvas.create_text(215, 1008, text=f"1 / {len(lignes)}",
                                         fill="#888888", font=('Helvetica 11'))
        items_dialogue += [texte, indicateur, compteur]

        def next_ligne(e=None):
            index[0] += 1
            if index[0] >= len(lignes):
                for item in items_dialogue:
                    canvas.delete(item)
                dialogue_en_cours[0] = False
                fenetre.unbind("<space>")
                if quete_id is not None:
                    sauvegarder_quete_complete(quete_id, zone_id)
                fenetre.bind("<Left>",   deplacer_gauche)
                fenetre.bind("<Right>",  deplacer_droite)
                fenetre.bind("<Up>",     deplacer_haut)
                fenetre.bind("<Down>",   deplacer_bas)
                fenetre.bind("<Escape>", menu_echap)
                fenetre.bind("<Tab>",    afficher_journal)
                fenetre.bind("<F1>",     afficher_aide)
                lift_hud()
            else:
                canvas.itemconfig(texte, text=lignes[index[0]])
                canvas.itemconfig(compteur, text=f"{index[0]+1} / {len(lignes)}")

        fenetre.bind("<space>", next_ligne)
        for item in [boite, texte, indicateur]:
            canvas.tag_bind(item, "<Button-1>", next_ligne)

    # ── Journal de quetes (Tab) ───────────────────────────────────────────────
    def afficher_journal(e=None):
        with open(os.path.join(BASE_DIR, 'data.json'), encoding='utf-8') as f:
            d = json.load(f)
        completees    = set(d.get('quetes_completees', []))
        nb_total      = sum(1 for q in d['quetes'] if q.get('id_collision'))
        nb_completees = len(completees & {q['id'] for q in d['quetes'] if q.get('id_collision')})

        items_journal = []
        overlay   = canvas.create_rectangle(380, 60, 1540, 880,
                                             fill="#1a1a2e", outline="#c0a060", width=3)
        titre     = canvas.create_text(960, 115, text="Journal de Quetes",
                                        fill="#FFD700", font=('Helvetica 24 bold'))
        prog_txt  = canvas.create_text(960, 158,
                                        text=f"Progression : {nb_completees} / {nb_total}  quetes actives",
                                        fill="#aaaaaa", font=('Helvetica 13'))
        sep       = canvas.create_line(430, 178, 1510, 178, fill="#c0a060", width=1)
        items_journal += [overlay, titre, prog_txt, sep]

        # Barre de progression
        bar_w    = 900
        bar_x    = 960 - bar_w // 2
        bar_bg   = canvas.create_rectangle(bar_x, 188, bar_x + bar_w, 206,
                                            fill='#2a2a3e', outline='#555566')
        prog_px  = int(bar_w * nb_completees / max(nb_total, 1))
        bar_fill = canvas.create_rectangle(bar_x, 188, bar_x + prog_px, 206,
                                            fill='#c0a060', outline='')
        items_journal += [bar_bg, bar_fill]

        y = 232
        for q in d['quetes']:
            termine  = q['id'] in completees
            has_coll = bool(q.get('id_collision'))
            if not has_coll:
                statut = "?"
                couleur = "#666688"
            elif termine:
                statut = "v"
                couleur = "#90ee90"
            else:
                statut = "o"
                couleur = "white"
            nom    = q.get('title', f"Quete {q['id']}")
            desc   = q.get('description', '')
            reward = q.get('reward_gold')

            t1 = canvas.create_text(400, y, text=f"[{statut}]  {nom}",
                                     fill=couleur, font=('Helvetica 15 bold'), anchor=W)
            items_journal.append(t1)
            line2 = desc
            if reward:
                line2 += f"  ({reward} pieces)"
            if line2:
                t2 = canvas.create_text(418, y + 28, text=line2,
                                         fill="#888899", font=('Helvetica 12'), anchor=W)
                items_journal.append(t2)
                y += 82
            else:
                y += 56

        sep2      = canvas.create_line(430, y + 10, 1510, y + 10, fill="#555566", width=1)
        gold_txt  = canvas.create_text(960, y + 32, text=f"Or total : {gold[0]} pieces",
                                        fill="#FFD700", font=('Helvetica 13'))
        fermer_txt = canvas.create_text(960, y + 60, text="[ Tab ]  Fermer",
                                         fill="#c0a060", font=('Helvetica 13'))
        items_journal += [sep2, gold_txt, fermer_txt]

        def fermer_journal(e=None):
            for item in items_journal:
                canvas.delete(item)
            fenetre.unbind("<Tab>")
            fenetre.bind("<Tab>", afficher_journal)

        fenetre.unbind("<Tab>")
        fenetre.bind("<Tab>", fermer_journal)
        canvas.tag_bind(overlay, "<Button-1>", fermer_journal)

    # ── Aide (F1) ─────────────────────────────────────────────────────────────
    def afficher_aide(e=None):
        items_aide = []
        bg    = canvas.create_rectangle(580, 180, 1340, 760,
                                         fill='#1a1a2e', outline='#c0a060', width=3)
        titre = canvas.create_text(960, 225, text='Controles',
                                    fill='#FFD700', font=('Helvetica 22 bold'))
        sep   = canvas.create_line(620, 248, 1300, 248, fill='#c0a060', width=1)
        items_aide += [bg, titre, sep]

        controles = [
            ('Fleches',       'Deplacer le chevalier'),
            ('Espace / Clic', 'Avancer dans le dialogue'),
            ('Tab',           'Journal de quetes'),
            ('Echap',         'Menu pause'),
            ('F1',            'Cette aide'),
            ('F2',            'Outil de dessin de collisions'),
            ('F3',            'Mode debug (zones visibles)'),
        ]
        y = 278
        for key, desc in controles:
            kb = canvas.create_rectangle(605, y-16, 760, y+16,
                                          fill='#262640', outline='#555577', width=1)
            kt = canvas.create_text(683, y, text=key, fill='#c0a060',
                                     font=('Helvetica 13 bold'))
            dt = canvas.create_text(785, y, text=desc, fill='white',
                                     font=('Helvetica 13'), anchor=W)
            items_aide += [kb, kt, dt]
            y += 48

        fermer_txt = canvas.create_text(960, 730, text='[ F1 ]  Fermer',
                                         fill='#c0a060', font=('Helvetica 13'))
        items_aide.append(fermer_txt)

        def fermer_aide(e2=None):
            for item in items_aide:
                canvas.delete(item)
            fenetre.unbind('<F1>')
            fenetre.bind('<F1>', afficher_aide)

        fenetre.unbind('<F1>')
        fenetre.bind('<F1>', fermer_aide)
        canvas.tag_bind(bg, '<Button-1>', fermer_aide)

    # ── Outil de dessin de collisions (F2) ────────────────────────────────────
    draw_mode      = [False]
    draw_start     = [None]
    draw_preview   = [None]
    draw_indicator = [None]
    draw_panel     = []

    def on_draw_press(e):
        draw_start[0] = (e.x, e.y)
        for item in draw_panel:
            canvas.delete(item)
        draw_panel.clear()
        if draw_preview[0]:
            canvas.delete(draw_preview[0])
        draw_preview[0] = canvas.create_rectangle(e.x, e.y, e.x, e.y,
                                                   outline="yellow", width=2, dash=(4, 4))

    def on_draw_drag(e):
        if not draw_start[0] or not draw_preview[0]:
            return
        x0, y0 = draw_start[0]
        canvas.coords(draw_preview[0], x0, y0, e.x, e.y)

    def on_draw_release(e):
        if not draw_start[0]:
            return
        x0, y0 = draw_start[0]
        draw_start[0] = None
        rx1, ry1 = min(x0, e.x), min(y0, e.y)
        rx2, ry2 = max(x0, e.x), max(y0, e.y)
        if rx2 - rx1 < 5 or ry2 - ry1 < 5:
            return
        bg_pos = canvas.coords(background_img_normal)
        djx1 = int(rx1 - bg_pos[0] - 2760)
        djy1 = int(ry1 - bg_pos[1] - 4240)
        djx2 = int(rx2 - bg_pos[0] - 2760)
        djy2 = int(ry2 - bg_pos[1] - 4240)
        px, py = 960, 500
        items = [
            canvas.create_rectangle(px-390, py-90, px+390, py+100,
                                     fill="#1a1a2e", outline="#c0a060", width=2),
            canvas.create_text(px, py-58, fill="white", font=('Courier 13 bold'),
                                text=f"x1={djx1}  y1={djy1}  ->  x2={djx2}  y2={djy2}"),
            canvas.create_text(px, py-25, text="Sauvegarder comme :",
                                fill="#aaaaaa", font=('Helvetica 12')),
            # Rouge
            canvas.create_rectangle(px-340, py+5, px-20,  py+70,
                                     fill="#5a0000", outline="red", width=2),
            canvas.create_text(px-180, py+37, text="[R]  Mur (rouge)",
                                fill="white", font=('Helvetica 13 bold')),
            # Vert
            canvas.create_rectangle(px+20,  py+5, px+340, py+70,
                                     fill="#004000", outline="#00ff00", width=2),
            canvas.create_text(px+180, py+37, text="[G]  PNJ (vert)",
                                fill="white", font=('Helvetica 13 bold')),
            # Orange
            canvas.create_rectangle(px-160, py-80, px+160, py-10,
                                     fill="#3a2a00", outline="#ff8800", width=2),
            canvas.create_text(px, py-45, text="[O]  Piege (orange)",
                                fill="white", font=('Helvetica 13 bold')),
        ]
        draw_panel.extend(items)

        def sauvegarder(color):
            fenetre.unbind("r"); fenetre.unbind("g"); fenetre.unbind("o")
            for item in draw_panel:
                canvas.delete(item)
            draw_panel.clear()
            if draw_preview[0]:
                canvas.delete(draw_preview[0])
                draw_preview[0] = None
            with open(os.path.join(BASE_DIR, 'data.json'), 'r+', encoding='utf-8') as f:
                d = json.load(f)
                new_id = max((c['id'] for c in d['collisions']), default=0) + 1
                d['collisions'].append({"id": new_id, "x1": djx1, "y1": djy1,
                                        "x2": djx2, "y2": djy2, "color": color})
                f.seek(0)
                json.dump(d, f, indent=4, ensure_ascii=False)
                f.truncate()
            rect = canvas.create_rectangle(rx1, ry1, rx2, ry2, fill="", outline="")
            rectangles.append(rect)
            coord_carres.append([rx1, ry1, rx2, ry2, new_id])
            collision_info[new_id] = {"id": new_id, "x1": djx1, "y1": djy1,
                                      "x2": djx2, "y2": djy2, "color": color}
            debug_labels.append(None)

        fenetre.bind("r", lambda e: sauvegarder("red"))
        fenetre.bind("g", lambda e: sauvegarder("green"))
        fenetre.bind("o", lambda e: sauvegarder("orange"))
        canvas.tag_bind(items[3], "<Button-1>", lambda e: sauvegarder("red"))
        canvas.tag_bind(items[4], "<Button-1>", lambda e: sauvegarder("red"))
        canvas.tag_bind(items[5], "<Button-1>", lambda e: sauvegarder("green"))
        canvas.tag_bind(items[6], "<Button-1>", lambda e: sauvegarder("green"))
        canvas.tag_bind(items[7], "<Button-1>", lambda e: sauvegarder("orange"))
        canvas.tag_bind(items[8], "<Button-1>", lambda e: sauvegarder("orange"))

    def toggle_draw(e=None):
        draw_mode[0] = not draw_mode[0]
        if draw_mode[0]:
            draw_indicator[0] = canvas.create_text(960, 28,
                text="MODE DESSIN  |  Glisser pour tracer  |  F2 pour quitter",
                fill="yellow", font=('Helvetica 12 bold'))
            canvas.bind("<ButtonPress-1>",   on_draw_press)
            canvas.bind("<B1-Motion>",       on_draw_drag)
            canvas.bind("<ButtonRelease-1>", on_draw_release)
        else:
            canvas.unbind("<ButtonPress-1>")
            canvas.unbind("<B1-Motion>")
            canvas.unbind("<ButtonRelease-1>")
            fenetre.unbind("r"); fenetre.unbind("g"); fenetre.unbind("o")
            if draw_indicator[0]:
                canvas.delete(draw_indicator[0])
                draw_indicator[0] = None
            if draw_preview[0]:
                canvas.delete(draw_preview[0])
                draw_preview[0] = None
            for item in draw_panel:
                canvas.delete(item)
            draw_panel.clear()

    # ── Detection des zones de dialogue ───────────────────────────────────────
    def check_zone_dialogue(coords_perso):
        if dialogue_en_cours[0]:
            return
        for coord_carre in coord_carres:
            carre_id = coord_carre[4]
            if (coords_perso[0] < coord_carre[2] and coords_perso[2] > coord_carre[0] and
                    coords_perso[3] > coord_carre[1] and coords_perso[1] < coord_carre[3]):
                if collision_info.get(carre_id, {}).get('color') == 'green' and carre_id in quete_by_collision:
                    if carre_id in quetes_completees:
                        return
                    if dialogue_last_zone[0] != carre_id:
                        dialogue_last_zone[0] = carre_id
                        quete = quete_by_collision[carre_id]
                        afficher_dialogue(
                            quete['dialogue'],
                            speaker=quete.get('speaker', ''),
                            quete_id=quete['id'],
                            zone_id=carre_id
                        )
                    return
        dialogue_last_zone[0] = None

    # ── Detection des collisions + zones pieges ───────────────────────────────
    def detect_collision(canvas, mover, data, x, y, coord_carre_move):
        new_coords = [coord_carre_move[0]+x, coord_carre_move[1]+y,
                      coord_carre_move[2]+x, coord_carre_move[3]+y]
        can_move = True
        on_trap  = False

        for coord_carre in coord_carres:
            color = collision_info.get(coord_carre[4], {}).get('color', 'red')
            if color in ('green', 'orange'):
                if color == 'orange':
                    if (new_coords[0] < coord_carre[2] and new_coords[2] > coord_carre[0] and
                            new_coords[3] > coord_carre[1] and new_coords[1] < coord_carre[3]):
                        on_trap = True
                continue
            if (new_coords[0] < coord_carre[2] and new_coords[2] > coord_carre[0] and
                    new_coords[3] > coord_carre[1] and new_coords[1] < coord_carre[3]):
                can_move = False
                break

        if can_move:
            canvas.move(mover, x/5, y/5)
            canvas.move(background_img_normal, -x, -y)
            for i, rect in enumerate(rectangles):
                canvas.move(rect, -x, -y)
                coord_carres[i] = [coord_carres[i][0]-x, coord_carres[i][1]-y,
                                   coord_carres[i][2]-x, coord_carres[i][3]-y, coord_carres[i][4]]
            for ind in indicateurs_npc.values():
                canvas.move(ind, -x, -y)
            for lbls in debug_labels:
                if lbls:
                    for lbl in lbls:
                        canvas.move(lbl, -x, -y)
            if on_trap:
                prendre_degats()
            update_minimap()
            mettre_a_jour_debug()
            check_zone_dialogue(new_coords)
            lift_hud()

    # ── Fonctions de deplacement ──────────────────────────────────────────────
    def deplacer_droite(e):
        canvas.itemconfig(personnage, image=personnage_droite_src)
        canvas.update()
        detect_collision(canvas, personnage, data, 10, 0, canvas.bbox(personnage))

    def deplacer_gauche(e):
        canvas.itemconfig(personnage, image=personnage_gauche_src)
        canvas.update()
        detect_collision(canvas, personnage, data, -10, 0, canvas.bbox(personnage))

    def deplacer_bas(e):
        canvas.itemconfig(personnage, image=personnage_arriere_src)
        canvas.update()
        detect_collision(canvas, personnage, data, 0, 10, canvas.bbox(personnage))

    def deplacer_haut(e):
        canvas.itemconfig(personnage, image=personnage_avant_src)
        canvas.update()
        detect_collision(canvas, personnage, data, 0, -10, canvas.bbox(personnage))

    # ── Menu pause (Echap) ────────────────────────────────────────────────────
    def menu_echap(e):
        fenetre.unbind("<Left>"); fenetre.unbind("<Right>")
        fenetre.unbind("<Up>");   fenetre.unbind("<Down>")
        fenetre.unbind("<Escape>"); fenetre.unbind("<Tab>")

        bg_blur = canvas.create_image(0, 0, anchor=NW, image=background_img_blur_src)
        canvas.move(bg_blur, -980, -1980)

        pause_titre = canvas.create_text(960, 580, text="Pause",
                                          fill='#FFD700', font=('Helvetica 40 bold'))
        pause_info  = canvas.create_text(960, 640,
                                          text=f"PV : {hp[0]} / {MAX_HP}   |   Or : {gold[0]} pieces",
                                          fill='#aaaaaa', font=('Helvetica 16'))

        resume_btn         = canvas.create_image(150,  750, anchor=NW, image=resume_button_src)
        menu_principal_btn = canvas.create_image(1270, 750, anchor=NW, image=menu_principal_button_src)

        def reprendre(e=None):
            canvas.delete(bg_blur)
            canvas.delete(resume_btn)
            canvas.delete(menu_principal_btn)
            canvas.delete(pause_titre)
            canvas.delete(pause_info)
            fenetre.bind("<Left>",   deplacer_gauche)
            fenetre.bind("<Right>",  deplacer_droite)
            fenetre.bind("<Up>",     deplacer_haut)
            fenetre.bind("<Down>",   deplacer_bas)
            fenetre.bind("<Escape>", menu_echap)
            fenetre.bind("<Tab>",    afficher_journal)
            fenetre.bind("<F1>",     afficher_aide)
            fenetre.bind("<F3>",     toggle_debug)
            fenetre.bind("<F2>",     toggle_draw)
            lift_hud()

        def retour_menu(e=None):
            canvas.delete("all")
            fenetre.unbind("<Left>"); fenetre.unbind("<Right>")
            fenetre.unbind("<Up>");   fenetre.unbind("<Down>")
            fenetre.unbind("<Escape>"); fenetre.unbind("<Tab>")
            afficher_menu_principal()

        canvas.tag_bind(resume_btn,         "<Button-1>", reprendre)
        canvas.tag_bind(menu_principal_btn, "<Button-1>", retour_menu)
        fenetre.bind("<Escape>", reprendre)

    # ── Bindings de depart ────────────────────────────────────────────────────
    fenetre.bind("<Left>",   deplacer_gauche)
    fenetre.bind("<Right>",  deplacer_droite)
    fenetre.bind("<Up>",     deplacer_haut)
    fenetre.bind("<Down>",   deplacer_bas)
    fenetre.bind("<Escape>", menu_echap)
    fenetre.bind("<Tab>",    afficher_journal)
    fenetre.bind("<F1>",     afficher_aide)
    fenetre.bind("<F3>",     toggle_debug)
    fenetre.bind("<F2>",     toggle_draw)

    show_notification("  Utilisez les fleches pour explorer  —  F1 pour l'aide  ",
                      '#c0a060', 4500)
    lift_hud()


##############################################################################
#                     MENU PRINCIPAL
##############################################################################
def afficher_menu_principal():
    global background_img_blur, play_button, quit_button, playtime
    _menu_actif[0] = True

    background_img_blur = canvas.create_image(0, 0, anchor=NW, image=background_img_blur_src)
    canvas.move(background_img_blur, -980, -1980)

    # Titre avec ombre portee
    canvas.create_text(964, 186, text="The Knight's Quest",
                        fill='#6a4a10', font=('Helvetica 52 bold'))
    canvas.create_text(960, 182, text="The Knight's Quest",
                        fill='#FFD700', font=('Helvetica 52 bold'))
    canvas.create_text(960, 248, text="Une aventure medievale",
                        fill='#c0a060', font=('Helvetica 18'))

    play_button = canvas.create_image(150,  750, anchor=NW, image=play_button_src)
    quit_button = canvas.create_image(1270, 750, anchor=NW, image=quit_button_src)
    playtime    = canvas.create_text(960, 975, text="Temps de jeu : ",
                                      fill="white", font=('Helvetica 15 bold'))

    with open(os.path.join(BASE_DIR, 'data.json'), encoding='utf-8') as f:
        data = json.load(f)
    completees = set(data.get('quetes_completees', []))
    actives    = sum(1 for q in data['quetes'] if q.get('id_collision'))
    canvas.itemconfig(playtime,
        text=f"Temps de jeu : {data['playtime']} min   |   "
             f"Quetes : {len(completees)} / {actives}")

    # Etoiles animees en fond
    _menu_stars.clear()
    for _ in range(55):
        x  = random.randint(0, 1920)
        y  = random.randint(0, 1080)
        r  = random.randint(1, 3)
        st = 'gray50' if random.random() > 0.5 else ''
        s  = canvas.create_oval(x-r, y-r, x+r, y+r, fill='white', outline='', stipple=st)
        _menu_stars.append((s, random.uniform(0.12, 0.5), random.uniform(-0.12, 0.12)))

    def animer_stars():
        if not _menu_actif[0]:
            return
        for s, sp, dr in _menu_stars:
            try:
                canvas.move(s, dr, sp)
                c = canvas.coords(s)
                if c and c[1] > 1095:
                    x  = random.randint(0, 1920)
                    sz = random.randint(1, 3)
                    canvas.coords(s, x-sz, -sz, x+sz, sz)
            except:
                pass
        fenetre.after(28, animer_stars)

    animer_stars()

    canvas.tag_bind(quit_button, "<Button-1>", lambda event: quit_button_event())
    canvas.tag_bind(play_button, "<Button-1>", lambda event: play_button_event(canvas))


##############################################################################
#                     COMPTEUR DE TEMPS DE JEU
##############################################################################
def task():
    with open(os.path.join(BASE_DIR, 'data.json'), 'r+', encoding='utf-8') as f:
        data = json.load(f)
        data['playtime'] = data['playtime'] + 1
        try:
            canvas.itemconfig(playtime, text=f"Temps de jeu : {data['playtime']} min")
        except:
            pass
        f.seek(0)
        json.dump(data, f, indent=4, ensure_ascii=False)
        f.truncate()
    fenetre.after(60000, task)


afficher_menu_principal()
fenetre.after(60000, task)
fenetre.mainloop()
