##############################################################################
#                     IMPORTATION DES BIBLIOTHÈQUES
#                     NÉCESSAIRES AU PROGRAMME
##############################################################################
from tkinter import *
from PIL import Image, ImageTk
from time import *
import json
import os
import ctypes

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except:
    pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

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
background_img_normal_src = ImageTk.PhotoImage(Image.open(os.path.join(BASE_DIR, 'assets/background/background.png')))
background_img_blur_src   = ImageTk.PhotoImage(Image.open(os.path.join(BASE_DIR, 'assets/background/background_blur.jpg')))
personnage_avant_src      = ImageTk.PhotoImage(Image.open(os.path.join(BASE_DIR, 'assets/personnages/marche_avant.png')))
personnage_arriere_src    = ImageTk.PhotoImage(Image.open(os.path.join(BASE_DIR, 'assets/personnages/marche_arrière.png')))
personnage_gauche_src     = ImageTk.PhotoImage(Image.open(os.path.join(BASE_DIR, 'assets/personnages/marche_gauche.png')))
personnage_droite_src     = ImageTk.PhotoImage(Image.open(os.path.join(BASE_DIR, 'assets/personnages/marche_droite.png')))
play_button_src           = ImageTk.PhotoImage(Image.open(os.path.join(BASE_DIR, "assets/buttons/start_button.png")))
quit_button_src           = ImageTk.PhotoImage(Image.open(os.path.join(BASE_DIR, "assets/buttons/quit_button.png")))
resume_button_src         = ImageTk.PhotoImage(Image.open(os.path.join(BASE_DIR, "assets/buttons/resume_button.png")))
menu_principal_button_src = ImageTk.PhotoImage(Image.open(os.path.join(BASE_DIR, "assets/buttons/menu_principal_button.png")))

##############################################################################
#                     FONCTION PRINCIPALE DU JEU
##############################################################################
def play_button_event(variable):
    global personnage
    canvas.delete("all")

    background_img_normal = canvas.create_image(0, 0, anchor=NW, image=background_img_normal_src)
    personnage = canvas.create_image(960, 540, anchor=NW, image=personnage_avant_src)
    canvas.move(background_img_normal, -2760, -4240)

    with open(os.path.join(BASE_DIR, 'data.json'), encoding='utf-8') as f:
        data = json.load(f)

    collision_info     = {c['id']: c for c in data['collisions']}
    quete_by_collision = {q['id_collision']: q for q in data['quetes'] if q.get('id_collision')}
    quetes_completees  = set(data.get('quetes_completees', []))

    dialogue_en_cours = [False]
    dialogue_last_zone = [None]


    # --- Création des zones de collision (invisibles) et indicateurs "!" ---
    rectangles = []
    indicateurs_npc = {}

    for i in data['collisions']:
        rect = canvas.create_rectangle(i["x1"], i["y1"], i["x2"], i["y2"], fill="", outline="")
        rectangles.append(rect)
        if i["color"] == "green":
            quete = quete_by_collision.get(i["id"])
            if quete and i["id"] not in quetes_completees:
                cx = (i["x1"] + i["x2"]) // 2
                cy = i["y1"] - 25
                ind = canvas.create_text(cx, cy, text="!", fill="#FFD700", font=('Helvetica 26 bold'))
                indicateurs_npc[i["id"]] = ind

    coord_carres = [[i["x1"], i["y1"], i["x2"], i["y2"], i["id"]] for i in data['collisions']]

    # --- Debug ---
    debug_mode   = [False]
    debug_labels = [None] * len(rectangles)

    debug_bg      = canvas.create_rectangle(5, 5, 460, 125, fill="#000000", outline="#555555", state='hidden')
    debug_coords  = canvas.create_text(10, 10, anchor=NW, text="", fill="#00ff00",
                                       font=('Courier 11 bold'), state='hidden')
    debug_perso_rect = canvas.create_rectangle(0, 0, 0, 0, outline="cyan", width=2,
                                               dash=(4, 4), state='hidden')

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
                cid = coord_carres[i][4]
                color = collision_info.get(cid, {}).get('color', 'white')
                outline = "red" if color == "red" else "#00ff00"
                canvas.itemconfig(rect, fill="", outline=outline, width=2)
                # Coords data.json
                x1 = int(coord_carres[i][0] - bg_pos[0] - 2760)
                y1 = int(coord_carres[i][1] - bg_pos[1] - 4240)
                x2 = int(coord_carres[i][2] - bg_pos[0] - 2760)
                y2 = int(coord_carres[i][3] - bg_pos[1] - 4240)
                cx1 = coord_carres[i][0]  # canvas courant
                cy1 = coord_carres[i][1]
                cx2 = coord_carres[i][2]
                cy2 = coord_carres[i][3]
                rx  = (cx1 + cx2) // 2
                ry  = (cy1 + cy2) // 2
                items = [
                    canvas.create_text(cx1, cy1, text=f"x1={x1}\ny1={y1}", fill=outline, font=('Courier 7'), anchor=NW),
                    canvas.create_text(cx2, cy1, text=f"x2={x2}\ny1={y1}", fill=outline, font=('Courier 7'), anchor=NE),
                    canvas.create_text(cx1, cy2, text=f"x1={x1}\ny2={y2}", fill=outline, font=('Courier 7'), anchor=SW),
                    canvas.create_text(cx2, cy2, text=f"x2={x2}\ny2={y2}", fill=outline, font=('Courier 7'), anchor=SE),
                    canvas.create_text(rx,  ry,  text=f"id={cid}",         fill=outline, font=('Courier 9 bold'), anchor=CENTER),
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

    # --- Animation du "!" (clignotement) ---
    def animer_indicateurs():
        for ind in indicateurs_npc.values():
            couleur_actuel = canvas.itemcget(ind, "fill")
            canvas.itemconfig(ind, fill="#FFD700" if couleur_actuel == "#cc9900" else "#cc9900")
        fenetre.after(600, animer_indicateurs)

    animer_indicateurs()

    # --- Sauvegarde d'une quête complétée ---
    def sauvegarder_quete_complete(quete_id, zone_id):
        with open(os.path.join(BASE_DIR, 'data.json'), 'r+', encoding='utf-8') as f:
            d = json.load(f)
            completees = d.get('quetes_completees', [])
            if quete_id not in completees:
                completees.append(quete_id)
            d['quetes_completees'] = completees
            f.seek(0)
            json.dump(d, f, indent=4)
            f.truncate()
        quetes_completees.add(zone_id)
        if zone_id in indicateurs_npc:
            canvas.delete(indicateurs_npc[zone_id])
            del indicateurs_npc[zone_id]

    # --- Affichage du dialogue ---
    def afficher_dialogue(lignes, speaker="", quete_id=None, zone_id=None):
        dialogue_en_cours[0] = True
        fenetre.unbind("<Left>")
        fenetre.unbind("<Right>")
        fenetre.unbind("<Up>")
        fenetre.unbind("<Down>")
        fenetre.unbind("<Tab>")

        index = [0]
        items_dialogue = []

        boite = canvas.create_rectangle(200, 840, 1720, 1020, fill="#1a1a2e", outline="#c0a060", width=3)
        items_dialogue.append(boite)

        if speaker:
            nom_boite = canvas.create_rectangle(200, 800, 440, 845, fill="#1a1a2e", outline="#c0a060", width=2)
            nom_texte = canvas.create_text(320, 822, text=speaker, fill="#FFD700", font=('Helvetica 14 bold'))
            items_dialogue += [nom_boite, nom_texte]

        texte = canvas.create_text(960, 925, text=lignes[0], fill="white", font=('Helvetica 16'), width=1400)
        indicateur = canvas.create_text(1690, 1008, text="▶  Espace / Clic", fill="#c0a060", font=('Helvetica 11'))
        items_dialogue += [texte, indicateur]

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
            else:
                canvas.itemconfig(texte, text=lignes[index[0]])

        fenetre.bind("<space>", next_ligne)
        for item in [boite, texte, indicateur]:
            canvas.tag_bind(item, "<Button-1>", next_ligne)

    # --- Journal de quêtes ---
    def afficher_journal(e=None):
        with open(os.path.join(BASE_DIR, 'data.json'), encoding='utf-8') as f:
            d = json.load(f)
        completees = set(d.get('quetes_completees', []))

        items_journal = []
        overlay = canvas.create_rectangle(400, 80, 1520, 820, fill="#1a1a2e", outline="#c0a060", width=3)
        titre   = canvas.create_text(960, 130, text="Journal de Quêtes", fill="#FFD700", font=('Helvetica 24 bold'))
        items_journal += [overlay, titre]

        nb_completees = len(completees)
        nb_total = len(d['quetes'])
        progression = canvas.create_text(960, 170, text=f"Progression : {nb_completees} / {nb_total}", fill="#aaaaaa", font=('Helvetica 13'))
        items_journal.append(progression)

        separateur = canvas.create_line(450, 190, 1470, 190, fill="#c0a060", width=1)
        items_journal.append(separateur)

        y = 230
        for q in d['quetes']:
            termine = q['id'] in completees
            statut  = "✓" if termine else "○"
            couleur = "#90ee90" if termine else "white"
            nom     = q.get('title', f"Quête {q['id']}")
            desc    = q.get('description', '')

            t1 = canvas.create_text(460, y, text=f"{statut}  {nom}", fill=couleur, font=('Helvetica 15 bold'), anchor=W)
            items_journal.append(t1)
            if desc:
                t2 = canvas.create_text(480, y + 28, text=desc, fill="#aaaaaa", font=('Helvetica 12'), anchor=W)
                items_journal.append(t2)
                y += 80
            else:
                y += 55

        fermer_txt = canvas.create_text(960, 790, text="[ Tab ]  Fermer", fill="#c0a060", font=('Helvetica 13'))
        items_journal.append(fermer_txt)

        def fermer_journal(e=None):
            for item in items_journal:
                canvas.delete(item)
            fenetre.unbind("<Tab>")
            fenetre.bind("<Tab>", afficher_journal)

        fenetre.unbind("<Tab>")
        fenetre.bind("<Tab>", fermer_journal)
        canvas.tag_bind(overlay, "<Button-1>", fermer_journal)

    # --- Outil de dessin de collisions (F2) ---
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
            canvas.create_rectangle(px-370, py-80, px+370, py+90, fill="#1a1a2e", outline="#c0a060", width=2),
            canvas.create_text(px, py-50, text=f"x1={djx1}  y1={djy1}  →  x2={djx2}  y2={djy2}",
                fill="white", font=('Courier 13 bold')),
            canvas.create_text(px, py-15, text="Sauvegarder comme :", fill="#aaaaaa", font=('Helvetica 12')),
            canvas.create_rectangle(px-320, py+15, px-20, py+65, fill="#5a0000", outline="red", width=2),
            canvas.create_text(px-170, py+40, text="[R]  Mur (rouge)", fill="white", font=('Helvetica 13 bold')),
            canvas.create_rectangle(px+20,  py+15, px+320, py+65, fill="#004000", outline="#00ff00", width=2),
            canvas.create_text(px+170, py+40, text="[G]  PNJ (vert)",  fill="white", font=('Helvetica 13 bold')),
        ]
        draw_panel.extend(items)

        def sauvegarder(color):
            fenetre.unbind("r")
            fenetre.unbind("g")
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
        canvas.tag_bind(items[3], "<Button-1>", lambda e: sauvegarder("red"))
        canvas.tag_bind(items[4], "<Button-1>", lambda e: sauvegarder("red"))
        canvas.tag_bind(items[5], "<Button-1>", lambda e: sauvegarder("green"))
        canvas.tag_bind(items[6], "<Button-1>", lambda e: sauvegarder("green"))

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
            fenetre.unbind("r")
            fenetre.unbind("g")
            if draw_indicator[0]:
                canvas.delete(draw_indicator[0])
                draw_indicator[0] = None
            if draw_preview[0]:
                canvas.delete(draw_preview[0])
                draw_preview[0] = None
            for item in draw_panel:
                canvas.delete(item)
            draw_panel.clear()

    # --- Détection des zones de dialogue ---
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

    # --- Détection des collisions et déplacement ---
    def detect_collision(canvas, mover, data, x, y, coord_carre_move):
        new_coords = [coord_carre_move[0]+x, coord_carre_move[1]+y, coord_carre_move[2]+x, coord_carre_move[3]+y]
        can_move = True
        for coord_carre in coord_carres:
            if collision_info.get(coord_carre[4], {}).get('color') == 'green':
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
            mettre_a_jour_debug()
            check_zone_dialogue(new_coords)

    # --- Fonctions de déplacement ---
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

    # --- Menu pause (Echap) ---
    def menu_echap(e):
        fenetre.unbind("<Left>")
        fenetre.unbind("<Right>")
        fenetre.unbind("<Up>")
        fenetre.unbind("<Down>")
        fenetre.unbind("<Escape>")
        fenetre.unbind("<Tab>")

        bg_blur = canvas.create_image(0, 0, anchor=NW, image=background_img_blur_src)
        canvas.move(bg_blur, -980, -1980)
        resume_btn       = canvas.create_image(150,  750, anchor=NW, image=resume_button_src)
        menu_principal_btn = canvas.create_image(1270, 750, anchor=NW, image=menu_principal_button_src)

        canvas.tag_bind(resume_btn,        "<Button-1>", lambda e: reprendre())
        canvas.tag_bind(menu_principal_btn, "<Button-1>", lambda e: retour_menu())

        def reprendre():
            canvas.delete(bg_blur)
            canvas.delete(resume_btn)
            canvas.delete(menu_principal_btn)
            fenetre.bind("<Left>",   deplacer_gauche)
            fenetre.bind("<Right>",  deplacer_droite)
            fenetre.bind("<Up>",     deplacer_haut)
            fenetre.bind("<Down>",   deplacer_bas)
            fenetre.bind("<Escape>", menu_echap)
            fenetre.bind("<Tab>",    afficher_journal)
            fenetre.bind("<F3>",     toggle_debug)
            fenetre.bind("<F2>",     toggle_draw)

        def retour_menu():
            canvas.delete("all")
            fenetre.unbind("<Left>")
            fenetre.unbind("<Right>")
            fenetre.unbind("<Up>")
            fenetre.unbind("<Down>")
            fenetre.unbind("<Escape>")
            fenetre.unbind("<Tab>")
            afficher_menu_principal()

    fenetre.bind("<Left>",   deplacer_gauche)
    fenetre.bind("<Right>",  deplacer_droite)
    fenetre.bind("<Up>",     deplacer_haut)
    fenetre.bind("<Down>",   deplacer_bas)
    fenetre.bind("<Escape>", menu_echap)
    fenetre.bind("<Tab>",    afficher_journal)
    fenetre.bind("<F3>",     toggle_debug)
    fenetre.bind("<F2>",     toggle_draw)


##############################################################################
#                     MENU PRINCIPAL
##############################################################################
def afficher_menu_principal():
    global background_img_blur, play_button, quit_button, playtime

    background_img_blur = canvas.create_image(0, 0, anchor=NW, image=background_img_blur_src)
    canvas.move(background_img_blur, -980, -1980)

    play_button  = canvas.create_image(150,  750, anchor=NW, image=play_button_src)
    quit_button  = canvas.create_image(1270, 750, anchor=NW, image=quit_button_src)

    playtime = canvas.create_text(960, 975, text="Temps de jeu : ", fill="white", font=('Helvetica 15 bold'))
    with open(os.path.join(BASE_DIR, 'data.json'), encoding='utf-8') as f:
        data = json.load(f)
    canvas.itemconfig(playtime, text="Temps de jeu : " + str(data["playtime"]) + " min")

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
            canvas.itemconfig(playtime, text="Temps de jeu : " + str(data["playtime"]) + " min")
        except:
            pass
        f.seek(0)
        json.dump(data, f, indent=4, ensure_ascii=False)
        f.truncate()
    fenetre.after(60000, task)


afficher_menu_principal()
fenetre.after(60000, task)
fenetre.mainloop()
