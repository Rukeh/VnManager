from PIL import Image
import tkinter 
import customtkinter 
import os



#Path getter
base_dir = os.path.dirname(os.path.abspath(__file__))
logo_path = os.path.join(base_dir, 'logo.png')

#App init
app = customtkinter.CTk()
app.geometry("1280x720")
app.title("Vn Manager")

#Frame building
frame1 = customtkinter.CTkFrame(master=app, width =800, height = 30, border_width=2, corner_radius=15, fg_color="#303030")
frame2 = customtkinter.CTkFrame(master=app, width = 230, border_width = 2, corner_radius = 8)
frame3 = customtkinter.CTkFrame(master=app, border_width = 2, corner_radius = 8 )

#logo_fetch
logo_image = customtkinter.CTkImage(light_image=Image.open(logo_path), size = (30,30))
logo = customtkinter.CTkLabel(master = app, image= logo_image, text="placeholder")
logo.place(x=90,y=5)

#Frame packs
frame1.pack(pady=3, fill='x', padx=(245,5))
frame2.pack(side = "left", fill="y", padx=5, pady=(5,5))
frame3.pack(side = "right", fill='both', pady=(5,5), padx=(5,5), expand = True)

#Window start 
app.mainloop()