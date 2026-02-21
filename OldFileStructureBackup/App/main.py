from PIL import Image
from io import BytesIO
import requests
import tkinter 
import customtkinter 
import os
import sys
import json
import re
import threading

#Path getter
base_dir = os.path.dirname(os.path.abspath(__file__))
logo_path = os.path.join(base_dir, 'logo.png')
sys.path.append(os.path.join(base_dir, "..", "API_Requests"))
from VnDB_API_Requests import search_vns #import the search function that enables the search of vns using vndb kana api

#Save getter 
save_file = os.path.join(base_dir, '..', "Save/data.json")

#Functions 
def data_load():
    """
    Tries to load existing data in ../Save 
    If nothing is there returns a basic template
    """
    try: 
        with open(save_file, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        return {'categories': ["Not finished", "Finished", "Planned"]}

def save_data(data):
    """
    Saves the data in a json file in ../Save
    """
    with open(save_file, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent = 2)

def add_category():
    """
    Adds a category nothing more -_-
    Usable via a button
    """
    category_name = category_entry.get().strip()
    if not category_name:
        return
    data["categories"].append(category_name)
    save_data(data)
    category_entry.delete(0, "end")
    refresh_categories()

def refresh_categories():
    """
    Refreshes the categories displayed on the left panel in the main window
    """
    for widget in categories_frame.winfo_children():
        widget.destroy()
    for category in data["categories"]:
        button = customtkinter.CTkButton(
            master=categories_frame,
            text=category,
            anchor="w",
            fg_color="transparent",
            hover_color="#3a3a3a",
        )
        button.pack(fill="x", padx=8, pady=2)

def search_window_for_button():
    """
    This function is called when the Search a VN button is clicked on
    Opens a search window where the user can search for Visual novels using VnDB API (///and add them to the current category(Feature not already implemented)) 
    """
    search_window = customtkinter.CTkToplevel(app)
    search_window.title('Search a Visual Novel from VnDB database...')
    search_window.geometry("600x450")
    search_frame = customtkinter.CTkFrame(search_window)
    search_frame.pack(fill="x", padx=10, pady=10)
    entry = customtkinter.CTkEntry(search_frame, placeholder_text="Search a VN...")
    entry.pack(side="left", fill="x", expand=True, padx=(10, 8), pady=10)
    last_results = []

    view_mode = tkinter.StringVar(value="list")
    
    def search_vn_button():
        research = entry.get().strip()
        if not research:
            return
        api_data = search_vns(research)
        last_results.clear()
        last_results.extend(api_data)
        render_results(api_data)
    
    def toggle_view():
        if view_mode.get() == "list":
            view_mode.set("grid")
            toggle_button.configure(text="☰ List")
        else:
            view_mode.set("list")
            toggle_button.configure(text="⊞ Grid")
        if last_results:
                render_results(last_results)

    def render_results(api_data):
        for widget in search_frame_results.winfo_children():
            widget.destroy()

        if view_mode.get() == "list":
            for vn in api_data:
                year = (vn["released"] or "?")[:4]
                vn_card = customtkinter.CTkFrame(search_frame_results)
                vn_card.pack(fill="x", pady=4, padx=4)

                img_url = (vn['image']['url'] or {})
                card_image = customtkinter.CTkLabel(vn_card, text="", width=150, height=200)
                card_image.pack(side="left", padx=(8, 0), pady=8)
                if img_url:
                    def load_img(label=card_image, url=img_url):
                        img = image_loader_url(url, size=(150, 200))
                        if img:
                            label.configure(image=img)
                            label.image = img
                    threading.Thread(target=load_img, daemon=True).start()

                text_frame = customtkinter.CTkFrame(vn_card, fg_color="transparent")
                text_frame.pack(side="left", fill="both", expand=True, padx=10, pady=8)
                customtkinter.CTkLabel(text_frame, text=f"{vn['title']} ({year})", font=("Arial", 20, "bold"), anchor="w", wraplength=350).pack(fill="x", pady=(4, 4))
                customtkinter.CTkLabel(text_frame, text=clean_description(vn.get("description")), font=("Arial", 13), anchor="w", wraplength=350, justify="left").pack(fill="x")

        else:
            columns = 10
            for index, vn in enumerate(api_data):
                year = (vn.get("released") or "?")[:4]
                row = index // columns
                col = index % columns

                vn_card = customtkinter.CTkFrame(search_frame_results)
                vn_card.grid(row=row, column=col, padx=8, pady=8, sticky="n")

                img_url = (vn['image']['url'] or {})
                card_image = customtkinter.CTkLabel(vn_card, text="", width=150, height=200)
                card_image.pack(pady=(8, 4), padx=8)
                if img_url:
                    def load_img(label=card_image, url=img_url):
                        img = image_loader_url(url, size=(130, 180))
                        if img:
                            label.configure(image=img)
                            label.image = img
                    threading.Thread(target=load_img, daemon=True).start()

                customtkinter.CTkLabel(vn_card, text=vn["title"], font=("Arial", 12, "bold"), wraplength=130, justify="center").pack(padx=6)
                customtkinter.CTkLabel(vn_card, text=year, font=("Arial", 11), text_color="gray").pack(pady=(0, 8))

    toggle_button = customtkinter.CTkButton(search_frame, text="⊞ Grid", width=80, command=toggle_view)
    toggle_button.pack(side="right", padx=(0, 8))

    do_search_button = customtkinter.CTkButton(search_frame, text="Search", command=search_vn_button)
    do_search_button.pack(side="right")

    search_frame_results = customtkinter.CTkScrollableFrame(search_window)
    search_frame_results.pack(fill="both", expand=True)

    entry.bind("<Return>", lambda e: search_vn_button())

def image_loader_url(url, size=(150,200)):
    """
    Tries to load an image from an url 
    -url = url of an image 
    -size = size of the returned image (argument 1 : width, argument 2 : height) default 150x200
    """
    try:
        img_response = requests.get(url, timeout=5)
        img = Image.open(BytesIO(img_response.content))
        return customtkinter.CTkImage(img, size=size)
    except:
        return None
        
def clean_description(text):
    if not text:
        return "No description available."
    text = re.sub(r'\[url=[^\]]*\](.*?)\[/url\]', r'\1', text, flags=re.DOTALL)    #Hopefully removes hyperlink markers
    text = re.sub(r'\[/?[a-zA-Z][^\]]*\]', '', text)                               #(Created for the descriptions of novels may work elsewere)
    text = text.strip()
    if len(text) > 300:
        text = text[:300].rsplit(' ', 1)[0] + '...'
    return text

#App init
app = customtkinter.CTk()
app.geometry("1280x720")
app.title("VnManager")

#Frame building
search_frame = customtkinter.CTkFrame(master=app, width =800, height = 30, border_width=2, corner_radius=15, fg_color="#303030")
categories_frame = customtkinter.CTkFrame(master=app, width = 230, border_width = 2, corner_radius = 8)
frame3 = customtkinter.CTkFrame(master=app, border_width = 2, corner_radius = 8, fg_color="#1c1d1f")

#logo_fetch
logo_image = customtkinter.CTkImage(light_image=Image.open(logo_path), size = (30,30))
logo = customtkinter.CTkLabel(master = app, image= logo_image, text="placeholder")
logo.place(x=90,y=5)

#Buttons
category_entry = customtkinter.CTkEntry(categories_frame, placeholder_text="New category...")
category_entry.pack(padx=8, pady=(10, 4), fill="x")
category_add_button = customtkinter.CTkButton(categories_frame, text="+ Add", width=60, command=add_category)
category_add_button.pack(padx=8, pady=(0, 8), fill="x")
search_button = customtkinter.CTkButton(frame3, text = 'Search VN', command=search_window_for_button)
search_button.pack(pady=5, fill='x', padx=(5,5))

#Frame packs
search_frame.pack(pady=3, fill='x', padx=(245,5))
categories_frame.pack(side = "left", fill="y", padx=5, pady=(5,5))
frame3.pack(side = "right", fill='both', pady=(5,5), padx=(5,5), expand = True)

#Scroll
categories_frame = customtkinter.CTkScrollableFrame(categories_frame)
categories_frame.pack(fill="both", expand=True, padx=4, pady=4)

#Window start 
data = data_load()
refresh_categories()
app.mainloop()
