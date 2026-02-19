"""
VN Manager - Gestionnaire de Visual Novels
Tkinter + VNDB API
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import urllib.request   # pour appeler l'API VNDB (inclus dans Python)
import urllib.error

# ─── Constantes ───────────────────────────────────────────────────────────────

STATUTS = ["Planifié", "En cours", "Terminé", "Abandonné"]
FICHIER_SAUVEGARDE = "ma_liste.json"

COULEURS = {
    "bg":        "#0d0d14",
    "surface":   "#13111f",
    "border":    "#2a2440",
    "violet":    "#7c6af7",
    "text":      "#e8e0f0",
    "muted":     "#8879a8",
    "success":   "#4ecb8d",
    "danger":    "#e06c75",
}

# ─── Fonctions utilitaires ────────────────────────────────────────────────────

def sauvegarder(liste):
    """Écrit la liste dans un fichier JSON."""
    with open(FICHIER_SAUVEGARDE, "w", encoding="utf-8") as f:
        json.dump(liste, f, ensure_ascii=False, indent=2)

def charger():
    """Charge la liste depuis le fichier JSON. Retourne [] si introuvable."""
    try:
        with open(FICHIER_SAUVEGARDE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def rechercher_vndb(titre):
    """
    Envoie une requête POST à l'API VNDB et retourne une liste de résultats.
    Utilise urllib (inclus dans Python, pas besoin de pip).
    """
    url = "https://api.vndb.org/kana/vn"
    payload = {
        "filters": ["search", "=", titre],
        "fields": "id, title, released, rating, length_minutes, description",
        "results": 8,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            reponse = json.loads(resp.read().decode("utf-8"))
            return reponse.get("results", [])
    except urllib.error.URLError:
        return None  # pas de connexion


# ─── Fenêtre de recherche VNDB ────────────────────────────────────────────────

class FenetreRecherche(tk.Toplevel):
    def __init__(self, parent, callback_ajout):
        super().__init__(parent)
        self.title("Rechercher un VN")
        self.geometry("540x480")
        self.configure(bg=COULEURS["bg"])
        self.resizable(False, False)
        self.callback_ajout = callback_ajout
        self.resultats = []

        self._construire_ui()

    def _construire_ui(self):
        # Titre
        tk.Label(self, text="Rechercher sur VNDB",
                 bg=COULEURS["bg"], fg=COULEURS["text"],
                 font=("Georgia", 14, "bold")).pack(pady=(16, 8))

        # Barre de recherche
        frame_search = tk.Frame(self, bg=COULEURS["bg"])
        frame_search.pack(fill="x", padx=20)

        self.champ = tk.Entry(frame_search,
                              bg=COULEURS["surface"], fg=COULEURS["text"],
                              insertbackground=COULEURS["text"],
                              relief="flat", font=("Arial", 11))
        self.champ.pack(side="left", fill="x", expand=True, ipady=6, padx=(0, 8))
        self.champ.bind("<Return>", lambda e: self._chercher())

        tk.Button(frame_search, text="Chercher",
                  bg=COULEURS["violet"], fg="white",
                  relief="flat", cursor="hand2",
                  command=self._chercher).pack(side="right", ipady=6, ipadx=10)

        # Label statut
        self.label_statut = tk.Label(self, text="", bg=COULEURS["bg"],
                                     fg=COULEURS["muted"], font=("Arial", 10))
        self.label_statut.pack(pady=(6, 0))

        # Liste des résultats
        frame_liste = tk.Frame(self, bg=COULEURS["bg"])
        frame_liste.pack(fill="both", expand=True, padx=20, pady=10)

        scrollbar = tk.Scrollbar(frame_liste)
        scrollbar.pack(side="right", fill="y")

        self.listbox = tk.Listbox(
            frame_liste,
            bg=COULEURS["surface"], fg=COULEURS["text"],
            selectbackground=COULEURS["violet"],
            relief="flat", font=("Arial", 11),
            yscrollcommand=scrollbar.set,
            activestyle="none",
        )
        self.listbox.pack(fill="both", expand=True)
        scrollbar.config(command=self.listbox.yview)

        # Bouton ajouter
        tk.Button(self, text="✓  Ajouter à ma liste",
                  bg=COULEURS["success"], fg="white",
                  relief="flat", cursor="hand2",
                  font=("Arial", 11, "bold"),
                  command=self._ajouter).pack(pady=(0, 16), ipadx=16, ipady=6)

    def _chercher(self):
        titre = self.champ.get().strip()
        if not titre:
            return
        self.label_statut.config(text="Recherche en cours...")
        self.update()

        self.resultats = rechercher_vndb(titre)

        if self.resultats is None:
            self.label_statut.config(text="❌ Impossible de contacter VNDB (connexion ?)")
            return

        self.listbox.delete(0, tk.END)
        if not self.resultats:
            self.label_statut.config(text="Aucun résultat.")
            return

        self.label_statut.config(text=f"{len(self.resultats)} résultats trouvés")
        for vn in self.resultats:
            annee = vn.get("released", "")[:4] or "?"
            note = f"★{vn['rating']/10:.1f}" if vn.get("rating") else ""
            duree = f"~{vn['length_minutes']//60}h" if vn.get("length_minutes") else ""
            infos = "  ".join(filter(None, [annee, note, duree]))
            self.listbox.insert(tk.END, f"  {vn['title']}  ({infos})")

    def _ajouter(self):
        selection = self.listbox.curselection()
        if not selection:
            messagebox.showwarning("Sélection", "Sélectionne un VN dans la liste.")
            return
        vn = self.resultats[selection[0]]
        self.callback_ajout(vn)
        self.destroy()


# ─── Fenêtre de détail / édition d'un VN ─────────────────────────────────────

class FenetreDetail(tk.Toplevel):
    def __init__(self, parent, vn, callback_sauvegarde):
        super().__init__(parent)
        self.title(vn["title"])
        self.geometry("480x420")
        self.configure(bg=COULEURS["bg"])
        self.resizable(False, False)
        self.vn = vn
        self.callback_sauvegarde = callback_sauvegarde

        self._construire_ui()

    def _construire_ui(self):
        # Titre
        tk.Label(self, text=self.vn["title"],
                 bg=COULEURS["bg"], fg=COULEURS["text"],
                 font=("Georgia", 13, "bold"),
                 wraplength=440).pack(pady=(16, 4), padx=20)

        # Infos VNDB
        annee = self.vn.get("released", "")[:4] or "?"
        note = f"★ {self.vn['rating']/10:.1f}/10" if self.vn.get("rating") else "Pas de note"
        duree = f"~{self.vn['length_minutes']//60}h" if self.vn.get("length_minutes") else ""
        tk.Label(self, text=f"{annee}  ·  {note}  ·  {duree}",
                 bg=COULEURS["bg"], fg=COULEURS["muted"],
                 font=("Arial", 10)).pack(pady=(0, 12))

        # Séparateur
        tk.Frame(self, bg=COULEURS["border"], height=1).pack(fill="x", padx=20, pady=(0, 12))

        # Statut
        frame_statut = tk.Frame(self, bg=COULEURS["bg"])
        frame_statut.pack(fill="x", padx=20, pady=(0, 10))
        tk.Label(frame_statut, text="Statut :", bg=COULEURS["bg"],
                 fg=COULEURS["text"], font=("Arial", 11)).pack(side="left")
        self.var_statut = tk.StringVar(value=self.vn.get("statut", "Planifié"))
        menu = ttk.Combobox(frame_statut, textvariable=self.var_statut,
                            values=STATUTS, state="readonly", width=14)
        menu.pack(side="left", padx=(10, 0))

        # Note perso
        frame_note = tk.Frame(self, bg=COULEURS["bg"])
        frame_note.pack(fill="x", padx=20, pady=(0, 10))
        tk.Label(frame_note, text="Ma note :", bg=COULEURS["bg"],
                 fg=COULEURS["text"], font=("Arial", 11)).pack(side="left")
        self.var_note = tk.IntVar(value=self.vn.get("ma_note", 0))
        for i in range(1, 6):
            tk.Radiobutton(frame_note, text=f"{'★'*i}", variable=self.var_note,
                           value=i, bg=COULEURS["bg"], fg="#e5a550",
                           selectcolor=COULEURS["bg"],
                           activebackground=COULEURS["bg"]).pack(side="left")

        # Notes perso
        tk.Label(self, text="Mes notes :", bg=COULEURS["bg"],
                 fg=COULEURS["text"], font=("Arial", 11),
                 anchor="w").pack(fill="x", padx=20)
        self.champ_notes = tk.Text(self, height=5,
                                   bg=COULEURS["surface"], fg=COULEURS["text"],
                                   insertbackground=COULEURS["text"],
                                   relief="flat", font=("Arial", 11),
                                   padx=8, pady=6)
        self.champ_notes.pack(fill="x", padx=20, pady=(4, 12))
        self.champ_notes.insert("1.0", self.vn.get("notes", ""))

        # Bouton sauvegarder
        tk.Button(self, text="💾  Sauvegarder",
                  bg=COULEURS["violet"], fg="white",
                  relief="flat", cursor="hand2",
                  font=("Arial", 11, "bold"),
                  command=self._sauvegarder).pack(ipadx=16, ipady=6)

    def _sauvegarder(self):
        self.vn["statut"] = self.var_statut.get()
        self.vn["ma_note"] = self.var_note.get()
        self.vn["notes"] = self.champ_notes.get("1.0", tk.END).strip()
        self.callback_sauvegarde()
        self.destroy()


# ─── Fenêtre principale ───────────────────────────────────────────────────────

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("VN Manager")
        self.geometry("680x560")
        self.configure(bg=COULEURS["bg"])
        self.resizable(True, True)

        # Charger les données
        self.liste = charger()

        self._construire_ui()
        self._rafraichir_liste()

    def _construire_ui(self):
        # ── En-tête ──
        header = tk.Frame(self, bg=COULEURS["bg"])
        header.pack(fill="x", padx=20, pady=(16, 8))

        tk.Label(header, text="VN Manager",
                 bg=COULEURS["bg"], fg=COULEURS["violet"],
                 font=("Georgia", 22, "bold")).pack(side="left")

        tk.Button(header, text="+ Ajouter un VN",
                  bg=COULEURS["violet"], fg="white",
                  relief="flat", cursor="hand2",
                  font=("Arial", 11, "bold"),
                  command=self._ouvrir_recherche).pack(side="right", ipadx=12, ipady=6)

        # ── Stats ──
        self.frame_stats = tk.Frame(self, bg=COULEURS["bg"])
        self.frame_stats.pack(fill="x", padx=20, pady=(0, 10))

        # ── Filtres ──
        frame_filtres = tk.Frame(self, bg=COULEURS["bg"])
        frame_filtres.pack(fill="x", padx=20, pady=(0, 8))

        tk.Label(frame_filtres, text="Filtrer :",
                 bg=COULEURS["bg"], fg=COULEURS["muted"],
                 font=("Arial", 10)).pack(side="left")

        self.var_filtre = tk.StringVar(value="Tous")
        for statut in ["Tous"] + STATUTS:
            tk.Radiobutton(
                frame_filtres, text=statut,
                variable=self.var_filtre, value=statut,
                bg=COULEURS["bg"], fg=COULEURS["text"],
                selectcolor=COULEURS["bg"],
                activebackground=COULEURS["bg"],
                command=self._rafraichir_liste,
            ).pack(side="left", padx=4)

        # ── Liste principale ──
        frame_liste = tk.Frame(self, bg=COULEURS["bg"])
        frame_liste.pack(fill="both", expand=True, padx=20, pady=(0, 16))

        scrollbar = tk.Scrollbar(frame_liste)
        scrollbar.pack(side="right", fill="y")

        self.listbox = tk.Listbox(
            frame_liste,
            bg=COULEURS["surface"], fg=COULEURS["text"],
            selectbackground=COULEURS["violet"],
            relief="flat", font=("Arial", 12),
            yscrollcommand=scrollbar.set,
            activestyle="none",
            cursor="hand2",
        )
        self.listbox.pack(fill="both", expand=True)
        scrollbar.config(command=self.listbox.yview)
        self.listbox.bind("<Double-Button-1>", self._ouvrir_detail)

        # ── Barre du bas ──
        frame_bas = tk.Frame(self, bg=COULEURS["bg"])
        frame_bas.pack(fill="x", padx=20, pady=(0, 12))

        tk.Button(frame_bas, text="✏️  Modifier",
                  bg=COULEURS["surface"], fg=COULEURS["text"],
                  relief="flat", cursor="hand2",
                  command=self._ouvrir_detail).pack(side="left", ipadx=10, ipady=4)

        tk.Button(frame_bas, text="🗑  Supprimer",
                  bg=COULEURS["danger"], fg="white",
                  relief="flat", cursor="hand2",
                  command=self._supprimer).pack(side="left", padx=8, ipadx=10, ipady=4)

        self.label_aide = tk.Label(frame_bas,
                                   text="Double-clic pour modifier",
                                   bg=COULEURS["bg"], fg=COULEURS["muted"],
                                   font=("Arial", 9))
        self.label_aide.pack(side="right")

    def _rafraichir_liste(self):
        """Recharge l'affichage de la liste selon le filtre actif."""
        self.listbox.delete(0, tk.END)
        filtre = self.var_filtre.get()

        self.liste_affichee = [
            vn for vn in self.liste
            if filtre == "Tous" or vn.get("statut", "Planifié") == filtre
        ]

        for vn in self.liste_affichee:
            etoiles = "★" * vn.get("ma_note", 0)
            statut = vn.get("statut", "Planifié")
            annee = vn.get("released", "")[:4] or "?"
            ligne = f"  {vn['title']}  —  {statut}  {etoiles}  ({annee})"
            self.listbox.insert(tk.END, ligne)

        self._rafraichir_stats()

    def _rafraichir_stats(self):
        """Met à jour les compteurs en haut."""
        for widget in self.frame_stats.winfo_children():
            widget.destroy()

        total = len(self.liste)
        termines = sum(1 for v in self.liste if v.get("statut") == "Terminé")
        en_cours = sum(1 for v in self.liste if v.get("statut") == "En cours")
        heures = sum(v.get("length_minutes", 0) for v in self.liste) // 60

        for label, valeur in [
            ("Total", total),
            ("Terminés", termines),
            ("En cours", en_cours),
            ("Heures estimées", f"{heures}h"),
        ]:
            frame = tk.Frame(self.frame_stats, bg=COULEURS["surface"],
                             padx=14, pady=8)
            frame.pack(side="left", padx=(0, 8))
            tk.Label(frame, text=str(valeur),
                     bg=COULEURS["surface"], fg=COULEURS["violet"],
                     font=("Georgia", 16, "bold")).pack()
            tk.Label(frame, text=label,
                     bg=COULEURS["surface"], fg=COULEURS["muted"],
                     font=("Arial", 9)).pack()

    def _ouvrir_recherche(self):
        FenetreRecherche(self, self._ajouter_vn)

    def _ajouter_vn(self, vn):
        """Appelé par FenetreRecherche quand l'utilisateur choisit un VN."""
        # Éviter les doublons
        if any(v["id"] == vn["id"] for v in self.liste):
            messagebox.showinfo("Déjà dans la liste", f"'{vn['title']}' est déjà dans ta liste.")
            return
        vn["statut"] = "Planifié"
        vn["ma_note"] = 0
        vn["notes"] = ""
        self.liste.append(vn)
        sauvegarder(self.liste)
        self._rafraichir_liste()

    def _ouvrir_detail(self, event=None):
        selection = self.listbox.curselection()
        if not selection:
            return
        vn = self.liste_affichee[selection[0]]
        FenetreDetail(self, vn, self._apres_modification)

    def _apres_modification(self):
        sauvegarder(self.liste)
        self._rafraichir_liste()

    def _supprimer(self):
        selection = self.listbox.curselection()
        if not selection:
            return
        vn = self.liste_affichee[selection[0]]
        confirmer = messagebox.askyesno(
            "Supprimer", f"Supprimer '{vn['title']}' de ta liste ?"
        )
        if confirmer:
            self.liste.remove(vn)
            sauvegarder(self.liste)
            self._rafraichir_liste()


# ─── Lancement ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = App()
    app.mainloop()