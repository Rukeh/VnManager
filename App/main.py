from PIL import Image
from io import BytesIO
import requests
import tkinter 
import customtkinter 
import os
import sys
import json

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
    def search_vn_button():
        research = entry.get().strip()
        if not research:
            return
        api_data = search_vns(research)

        for widget in search_frame_results.winfo_children():
            widget.destroy()

        for vn in api_data :
            year = (vn.get("released") or '?')[:4]

            vn_card = customtkinter.CTkFrame(search_frame_results)
            vn_card.pack(fill='x')

            img_url = vn['image']['url']
            if img_url:
                image_ctk = image_loader_url(img_url, size=(150,200))
                if image_ctk:
                    card_image = customtkinter.CTkLabel(vn_card, image=image_ctk, text="")
                    card_image.image = image_ctk
                    card_image.pack(side='left', padx=(8,0), pady=8)

            customtkinter.CTkLabel(vn_card, text=vn['title'] + " " + year, font=("Arial", 30, 'bold'), anchor='w').pack(side='top', fill='x', padx=30)
            customtkinter.CTkLabel(vn_card, text=vn['description'], font = ('Arial', 18, 'bold'), anchor='w').pack(fill='x', padx = 50)

    do_search_button = customtkinter.CTkButton(master = search_frame, command=search_vn_button, text= 'Search')
    do_search_button.pack(side = 'right')
    search_frame_results = customtkinter.CTkScrollableFrame(search_window)
    search_frame_results.pack(fill='both', expand=True)

def image_loader_url(url, size=(150,200)):
    try:
        img_response = requests.get(url)
        img = Image.open(BytesIO(img_response.content))
        return customtkinter.CTkImage(img, size=size)
    except:
        return None

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
