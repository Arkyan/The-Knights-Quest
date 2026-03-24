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
#                     DELARATION DE LA FENETRE
#                     AVEC LA TAILLE, LE TITRE
#                     ET L'ICONE
##############################################################################
fenetre = Tk()
fenetre.geometry("1920x1080")
fenetre.title("The Knight's Quest")
fenetre.iconbitmap(os.path.join(BASE_DIR, "assets/icon/chateau.ico"))

##############################################################################  
#                     CRÉATION DE LA FENÊTRE
#                     GRACE A CANVAS
##############################################################################
canvas = Canvas(fenetre, width=1920, height=1080, bg="white")
canvas.pack()

def quit_button_event(): #définiton de la fonction quit_button_event qui sert a fermer le programme
   exit()

##############################################################################
#                     DELARATION DES IMAGES
##############################################################################
background_img_normal_src = ImageTk.PhotoImage(Image.open(os.path.join(BASE_DIR, 'assets/background/background.png')))
background_img_blur_src = ImageTk.PhotoImage(Image.open(os.path.join(BASE_DIR, 'assets/background/background_blur.jpg')))
personnage_avant_src = ImageTk.PhotoImage(Image.open(os.path.join(BASE_DIR, 'assets/personnages/marche_avant.png')))
personnage_arriere_src = ImageTk.PhotoImage(Image.open(os.path.join(BASE_DIR, 'assets/personnages/marche_arrière.png')))
personnage_gauche_src = ImageTk.PhotoImage(Image.open(os.path.join(BASE_DIR, 'assets/personnages/marche_gauche.png')))
personnage_droite_src = ImageTk.PhotoImage(Image.open(os.path.join(BASE_DIR, 'assets/personnages/marche_droite.png')))
play_button_src = ImageTk.PhotoImage(Image.open(os.path.join(BASE_DIR, "assets/buttons/start_button.png")))
quit_button_src = ImageTk.PhotoImage(Image.open(os.path.join(BASE_DIR, "assets/buttons/quit_button.png")))
resume_button_src = ImageTk.PhotoImage(Image.open(os.path.join(BASE_DIR, "assets/buttons/resume_button.png")))
menu_principal_button_src = ImageTk.PhotoImage(Image.open(os.path.join(BASE_DIR, "assets/buttons/menu_principal_button.png")))

def play_button_event(variable) :
   global personnage
   canvas.delete(background_img_blur)
   canvas.delete(play_button)
   canvas.delete(quit_button)

   background_img_normal = canvas.create_image(0, 0, anchor=NW, image=background_img_normal_src)
   personnage = canvas.create_image(960, 540, anchor=NW, image=personnage_avant_src)
   canvas.move(background_img_normal, -2760, -4240)

   f = open(os.path.join(BASE_DIR, 'data.json'))
   data = json.load(f)

   
   rectangles = []

   
   for i in data['collisions']:
      rect = canvas.create_rectangle(i["x1"], i["y1"], i["x2"], i["y2"], fill=i["color"], outline=i["color"])
      rectangles.append(rect)
      
   f.close()

   coord_carres = []
   for i in data['collisions']:
      coord_carres.append([i["x1"], i["y1"], i["x2"], i["y2"], i["id"]])

   collision_info = {c['id']: c for c in data['collisions']}
   quete_by_collision = {q['id_collision']: q for q in data['quetes'] if q.get('id_collision')}
   dialogue_en_cours = [False]
   dialogue_last_zone = [None]

   def afficher_dialogue(lignes):
      dialogue_en_cours[0] = True
      fenetre.unbind("<Left>")
      fenetre.unbind("<Right>")
      fenetre.unbind("<Up>")
      fenetre.unbind("<Down>")

      index = [0]
      boite = canvas.create_rectangle(200, 850, 1720, 1000, fill="black", outline="white", width=3)
      texte = canvas.create_text(960, 925, text=lignes[0], fill="white", font=('Helvetica 16'), width=1400)
      indicateur = canvas.create_text(1700, 990, text="▶", fill="white", font=('Helvetica 12'))

      def next_ligne(e=None):
         index[0] += 1
         if index[0] >= len(lignes):
            canvas.delete(boite)
            canvas.delete(texte)
            canvas.delete(indicateur)
            dialogue_en_cours[0] = False
            fenetre.unbind("<space>")
            fenetre.bind("<Left>", deplacer_gauche)
            fenetre.bind("<Right>", deplacer_droite)
            fenetre.bind("<Up>", deplacer_haut)
            fenetre.bind("<Down>", deplacer_bas)
            fenetre.bind("<Escape>", menu_echap)
         else:
            canvas.itemconfig(texte, text=lignes[index[0]])

      fenetre.bind("<space>", next_ligne)
      canvas.tag_bind(boite, "<Button-1>", next_ligne)
      canvas.tag_bind(texte, "<Button-1>", next_ligne)
      canvas.tag_bind(indicateur, "<Button-1>", next_ligne)

   def check_zone_dialogue(coords_perso):
      if dialogue_en_cours[0]:
         return
      for coord_carre in coord_carres:
         carre_id = coord_carre[4]
         if (coords_perso[0] < coord_carre[2] and coords_perso[2] > coord_carre[0] and
               coords_perso[3] > coord_carre[1] and coords_perso[1] < coord_carre[3]):
            if collision_info.get(carre_id, {}).get('color') == 'green' and carre_id in quete_by_collision:
               if dialogue_last_zone[0] != carre_id:
                  dialogue_last_zone[0] = carre_id
                  afficher_dialogue(quete_by_collision[carre_id]['dialogue'])
               return
      dialogue_last_zone[0] = None

   def detect_collision(canvas, mover, data, x, y, coord_carre_move):

      new_coord_carre_move = [coord_carre_move[0] + x, coord_carre_move[1] + y, coord_carre_move[2] + x, coord_carre_move[3] + y]
      can_move = True
      for i, coord_carre in enumerate(coord_carres):
         if collision_info.get(coord_carre[4], {}).get('color') == 'green':
            continue
         if new_coord_carre_move[0] < coord_carre[2] and new_coord_carre_move[2] > coord_carre[0] and new_coord_carre_move[3] > coord_carre[1] and new_coord_carre_move[1] < coord_carre[3]:
            can_move = False
            break
      if can_move:
         x_perso = x/5
         y_perso = y/5
         canvas.move(mover, x_perso, y_perso)
         canvas.move(background_img_normal, -x, -y)
         for i, rect in enumerate(rectangles):
            canvas.move(rect, -x, -y)
            coord_carres[i] = [coord_carres[i][0]-x, coord_carres[i][1]-y, coord_carres[i][2]-x, coord_carres[i][3]-y, coord_carres[i][4]]
         check_zone_dialogue(new_coord_carre_move)

   def deplacer_droite(e):
      canvas.itemconfig(personnage, image=personnage_droite_src)
      canvas.update()
      coords_perso = canvas.bbox(personnage)
      detect_collision(canvas, personnage, data, 10, 0, coords_perso)

   def deplacer_gauche(e):
      canvas.itemconfig(personnage, image=personnage_gauche_src)
      canvas.update()
      coords_perso = canvas.bbox(personnage)
      detect_collision(canvas, personnage, data, -10, 0, coords_perso)

   def deplacer_bas(e):
      canvas.itemconfig(personnage, image=personnage_arriere_src)
      canvas.update()
      coords_perso = canvas.bbox(personnage)
      detect_collision(canvas, personnage, data, 0, 10, coords_perso)

   def deplacer_haut(e):
      canvas.itemconfig(personnage, image=personnage_avant_src)
      canvas.update()
      coords_perso = canvas.bbox(personnage)
      detect_collision(canvas, personnage, data, 0, -10, coords_perso)

   def menu_echap(e) :
      fenetre.unbind("<Left>")
      fenetre.unbind("<Right>")
      fenetre.unbind("<Up>")
      fenetre.unbind("<Down>")
      fenetre.unbind("<Escape>")
      background_img_blur = canvas.create_image(0, 0, anchor=NW, image=background_img_blur_src)
      canvas.move(background_img_blur, -980, -1980)

      resume_button = canvas.create_image(150, 750, anchor=NW, image = resume_button_src)

      menu_principal_button = canvas.create_image(1270, 750, anchor=NW, image = menu_principal_button_src)

      canvas.tag_bind(resume_button, "<Button-1>", lambda event : quit_escape_menu())
      canvas.tag_bind(menu_principal_button, "<Button-1>", lambda event : menu_principal())

      def quit_escape_menu() :
         canvas.delete(background_img_blur)
         canvas.delete(resume_button)
         canvas.delete(menu_principal_button)
         fenetre.bind("<Left>", deplacer_gauche)
         fenetre.bind("<Right>", deplacer_droite)
         fenetre.bind("<Up>", deplacer_haut)
         fenetre.bind("<Down>", deplacer_bas)
         fenetre.bind("<Escape>", menu_echap)
         

      def menu_principal() :
         canvas.delete(personnage)
         canvas.delete(background_img_normal)
         background_img_blur = canvas.create_image(0, 0, anchor=NW, image=background_img_blur_src)
         canvas.move(background_img_blur, -980, -1980)

         play_button = canvas.create_image(150, 750, anchor=NW, image = play_button_src)

         quit_button = canvas.create_image(1270, 750, anchor=NW, image = quit_button_src)

         canvas.tag_bind(quit_button, "<Button-1>", lambda event : quit_button_event())
         canvas.tag_bind(play_button, "<Button-1>", lambda event : play_button_event(canvas))
         fenetre.unbind("<Left>")
         fenetre.unbind("<Right>")
         fenetre.unbind("<Up>")
         fenetre.unbind("<Down>")
         fenetre.unbind("<Escape>")

         playtime = canvas.create_text(960, 975, text="Temps de jeu : ", fill="white", font=('Helvetica 15 bold'))
         f = open(os.path.join(BASE_DIR, 'data.json'))
         data = json.load(f)
         canvas.itemconfig(playtime, text="Temps de jeu : " + str(data["playtime"]) + " min")


   fenetre.bind("<Left>", deplacer_gauche)
   fenetre.bind("<Right>", deplacer_droite)
   fenetre.bind("<Up>", deplacer_haut)
   fenetre.bind("<Down>", deplacer_bas)
   fenetre.bind("<Escape>", menu_echap)

background_img_blur = canvas.create_image(0, 0, anchor=NW, image=background_img_blur_src)
canvas.move(background_img_blur, -980, -1980)

play_button = canvas.create_image(150, 750, anchor=NW, image = play_button_src)

quit_button = canvas.create_image(1270, 750, anchor=NW, image = quit_button_src)

playtime = canvas.create_text(960, 975, text="Temps de jeu : ", fill="white", font=('Helvetica 15 bold'))
f = open(os.path.join(BASE_DIR, 'data.json'))
data = json.load(f)
canvas.itemconfig(playtime, text="Temps de jeu : " + str(data["playtime"]) + " min")

canvas.tag_bind(quit_button, "<Button-1>", lambda event : quit_button_event())
canvas.tag_bind(play_button, "<Button-1>", lambda event : play_button_event(canvas))

def task():
   with open(os.path.join(BASE_DIR, 'data.json'), 'r+') as f:
      data = json.load(f)
      data['playtime'] = data['playtime'] + 1
      canvas.itemconfig(playtime, text="Temps de jeu : " + str(data["playtime"]) + " min")
      f.seek(0)
      json.dump(data, f, indent=4)
      f.truncate()
   fenetre.after(60000, task)

fenetre.after(60000, task)


fenetre.mainloop()