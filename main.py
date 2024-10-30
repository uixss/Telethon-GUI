import asyncio
import os
import pickle
import customtkinter as ctk
from tkinter import ttk, Toplevel
from PIL import Image, ImageTk
import ctypes  
from telethon import TelegramClient, functions, types, errors
from session import create_session, save_session, load_sessions, save_all_sessions, get_entity_data
import base64
import io

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

root = ctk.CTk()
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
window_width = int(screen_width * 0.25)
window_height = int(screen_height * 0.48)
root.geometry(f"{window_width}x{window_height}")
root.title("𝐒𝐇𝐈𝐓 𝐔𝐍𝐃𝐄𝐑 💀")
root.configure(bg="#262626")
root.resizable(False, False)
root.overrideredirect(True)
root.wm_attributes('-alpha', 0.92)
root.grid_columnconfigure(0, weight=3) 
root.grid_columnconfigure(1, weight=1)  
icon_path = os.path.abspath("undermain.ico")

def create_generic_popup(title, width=250, height=400, labels=[], button_text="Aceptar", button_command=None):
    popup = ctk.CTkToplevel(root)
    popup.title(title)
    if os.path.exists(icon_path):
        popup.iconbitmap(icon_path)
    else:
        print("El icono undermain.ico no se encontró.")

    popup.geometry(f"{width}x{height}")
    popup.configure(bg="#262626")
    popup.resizable(False, False)
    popup.wm_attributes('-alpha', 0.95)

    input_entries = {}
    for label_text in labels:
        label = ctk.CTkLabel(popup, text=label_text, text_color="lightgray")
        label.pack(pady=10)
        entry = ctk.CTkEntry(popup)
        entry.pack(pady=5)
        input_entries[label_text] = entry

    if button_command:
        button = ctk.CTkButton(popup, text=button_text, command=lambda: button_command(input_entries),
                               fg_color="#3A3A4D", hover_color="#6C6C8A")
        button.pack(pady=10)
    else:
        button = ctk.CTkButton(popup, text=button_text, command=popup.destroy,
                               fg_color="#3A3A4D", hover_color="#6C6C8A")
        button.pack(pady=10)

    return popup


def start_move(event):
    root.x = event.x
    root.y = event.y

def stop_move(event):
    root.x = None
    root.y = None

def on_motion(event):
    deltax = event.x - root.x
    deltay = event.y - root.y
    x = root.winfo_x() + deltax
    y = root.winfo_y() + deltay
    root.geometry(f"+{x}+{y}")

root.bind("<ButtonPress-1>", start_move)
root.bind("<ButtonRelease-1>", stop_move)
root.bind("<B1-Motion>", on_motion)

def update_sessions_list():
    active_sessions = load_sessions()
    for item in tree.get_children():
        tree.delete(item)
    for session in active_sessions:
        _, _, phone = session
        masked_phone = f"{phone[:3]}{'*' * (len(phone) - 3)}"
        tree.insert("", "end", values=(masked_phone,))


def delete_selected_session():
    selected_item = tree.selection()
    if not selected_item:
        create_generic_popup("Advertencia", labels=["Seleccione una sesión para eliminar."])
        return
    item = tree.item(selected_item)
    session_data = item['values']
    updated_sessions = [s for s in load_sessions() if f"{s[2][:3]}{'*' * (len(s[2]) - 3)}" != session_data[0]]
    save_all_sessions(updated_sessions)
    update_sessions_list()
    create_generic_popup("Eliminado", labels=["La sesión ha sido eliminada y los cambios se han guardado."])


def authenticate():
    api_id = api_id_entry.get()
    api_hash = api_hash_entry.get()
    phone_number = phone_entry.get()
    if api_id and api_hash and phone_number:
        asyncio.run(create_session(api_id, api_hash, phone_number))
        update_sessions_list()
    else:
        create_generic_popup("Advertencia", labels=["Por favor complete todos los campos antes de autenticar."])


async def check_entity():
    entity_input = entity_input_entry.get()
    api_id, api_hash, phone = load_sessions()[0]
    client = TelegramClient(f'sessions/{phone}', api_id, api_hash)
    await client.connect()

    if await client.is_user_authorized():
        try:
            entity = await client.get_entity(entity_input)
            if isinstance(entity, types.Channel) or isinstance(entity, types.Chat):
                full_chat = await client(functions.channels.GetFullChannelRequest(channel=entity))
                ban_status = "banned" if getattr(full_chat.full_chat, 'banned_rights', None) else "active"
                
                console_text.delete("1.0", ctk.END)
                console_text.insert(ctk.END, f"❌ {entity_input} has been {ban_status}.\n"
                                         f"\n• Chat ID: {entity.id}\n"
                                         f"• Chat Name: {full_chat.chats[0].title}\n"
                                         f"• Chat Members: {full_chat.full_chat.participants_count}\n")
            elif isinstance(entity, types.User):
                user_info = await client(functions.users.GetFullUserRequest(entity))
                user = user_info.users[0]
                
                console_text.delete("1.0", ctk.END)
                console_text.insert(ctk.END, f"❌ {entity_input} \n"
                                         f"\n• ID: {user.id}\n"
                                         f"• Name: {user.first_name} {user.last_name or ''}\n"
                                         f"• Username: @{user.username or 'N/A'}\n")
        except errors.UserNotParticipantError:
            console_text.delete("1.0", ctk.END)
            console_text.insert(ctk.END, f"User {phone} is not a participant in {entity_input}.\n")
        except Exception as e:
            console_text.delete("1.0", ctk.END)
            console_text.insert(ctk.END, f"Error retrieving entity: {str(e)}\n")
    else:
        console_text.delete("1.0", ctk.END)
        console_text.insert(ctk.END, f"Not authorized for initial session: {phone}\n")
    await client.disconnect()


def run_check_entity():
    console_text.delete("1.0", "end") 
    asyncio.run(check_entity())


top_panel = ctk.CTkFrame(root, height=40, fg_color="#121212")
top_panel.grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 0), sticky="ew")
top_panel.grid_columnconfigure((0, 1, 2), weight=1)

main_frame = ctk.CTkFrame(root, corner_radius=5, fg_color="#262626")
main_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
main_frame.grid_columnconfigure(1, weight=1)

index_frame = ctk.CTkFrame(root, corner_radius=5, fg_color="#262626")
index_frame.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")

buttons = [
    ("About", "Luxury Shield version 1.0\nDeveloped by [Your Company]."),
    ("Support", "For support, please contact support@example.com."),
   
]

for i, (text, content) in enumerate(buttons):
    button = ctk.CTkButton(
        top_panel, text=text, fg_color="#121212", hover_color="#3A3A4D",
        width=225, command=lambda t=text, c=content: create_generic_popup(t, labels=[content])
    )
    button.grid(row=0, column=i, padx=5, pady=5)

labels = ["API ID", "API Hash", "Phone number"]
entries = []
for i, label_text in enumerate(labels):
    label = ctk.CTkLabel(main_frame, text=label_text, text_color="lightgray", bg_color="#262626")
    label.grid(row=i, column=0, padx=5, pady=5, sticky="w")
    entry = ctk.CTkEntry(main_frame, fg_color="#262626")
    entry.grid(row=i, column=1, padx=5, pady=5, sticky="ew")
    entries.append(entry)
api_id_entry, api_hash_entry, phone_entry = entries

authenticate_button = ctk.CTkButton(main_frame, text="AUTH", command=authenticate, fg_color="#3A3A4D", hover_color="#6C6C8A")
authenticate_button.grid(row=3, column=1, pady=10, sticky="ew")

deauthenticate_button = ctk.CTkButton(main_frame, text="DELETE", command=delete_selected_session, fg_color="#3A3A4D", hover_color="#6C6C8A")
deauthenticate_button.grid(row=3, column=0, pady=10, padx=5, sticky="w")

style = ttk.Style()
style.configure("Custom.Treeview", background="#262626", fieldbackground="#262626", foreground="white", rowheight=30, font=("Arial", 12))
tree = ttk.Treeview(main_frame, columns=("Phone",), selectmode='browse', style="Custom.Treeview", height=3)
tree["show"] = "tree"
tree.column("Phone", anchor="center", stretch=True, width=100)
tree.grid(row=5, column=0, columnspan=2, padx=3, pady=3, sticky="nsew")

update_sessions_list()

entity_input_label = ctk.CTkLabel(main_frame, text="CHECK @user, link or ID", text_color="lightgray", bg_color="#262626")
entity_input_label.grid(row=7, column=0, padx=5, pady=5, sticky="w")
entity_input_entry = ctk.CTkEntry(main_frame, fg_color="#262626")
entity_input_entry.grid(row=7, column=1, padx=5, pady=5, sticky="ew")

console_frame = ctk.CTkFrame(main_frame, fg_color="#262626", corner_radius=5)
console_frame.grid(row=9, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
console_text = ctk.CTkTextbox(console_frame, wrap="word", height=100)
console_text.pack(expand=True, fill="both", padx=5, pady=5)

get_entity_button = ctk.CTkButton(main_frame, text="CHECK", command=run_check_entity, fg_color="#3A3A4D", hover_color="#6C6C8A")
get_entity_button.grid(row=8, column=0, columnspan=2, pady=10, sticky="ew")

logo_path = "undermain.png"
if os.path.exists(logo_path):
    logo_image = Image.open(logo_path).resize((100, 100), Image.LANCZOS)
    logo_image_tk = ImageTk.PhotoImage(logo_image)
    canvas = ctk.CTkCanvas(index_frame, width=125, height=125, bg="#262626", highlightthickness=0)
    canvas.create_image(55, 55, image=logo_image_tk)
    canvas.pack(pady=(10, 10))

buttons = [
    ("Send Message", lambda: create_generic_popup("Send Message", labels=["Username or ID", "Message", "Number of Sessions", "Messages per Session"], button_text="Send Message", button_command=lambda entries: asyncio.run(send_messages_popup(entries)))),
    ("Get INFO", lambda: print("Get INFO clicked")),
    ("MASSACRE REPORT", lambda: print("MASSACRE REPORT clicked"))
]

for text, command in buttons:
    button = ctk.CTkButton(index_frame, text=text, command=command, fg_color="#3A3A4D", hover_color="#6C6C8A", height=25)
    button.pack(pady=5, padx=5, fill="x")


root.mainloop()
