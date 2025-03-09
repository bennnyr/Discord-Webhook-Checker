import customtkinter as ctk
import os
import time
import subprocess
import sys
import threading
import json
import colorsys

def load_previous_inputs():
    try:
        with open('previous_inputs.json', 'r') as f:
            data = json.load(f)
            token_entry.insert(0, data.get("token", ""))
            channel_id_entry.insert(0, data.get("channel_id", ""))
            alert_channel_id_entry.insert(0, data.get("alert_channel_id", ""))
            wait_time_entry.insert(0, data.get("wait_time", ""))
            mumu_path_entry.insert(0, data.get("mumu_path", ""))
    except FileNotFoundError:
        pass  # if theres no previous file, skip

def save_inputs():
    data = {
        "token": token_entry.get(),
        "channel_id": channel_id_entry.get(),
        "alert_channel_id": alert_channel_id_entry.get(),
        "wait_time": wait_time_entry.get(),
        "mumu_path": mumu_path_entry.get()
    }
    with open('previous_inputs.json', 'w') as f:
        json.dump(data, f)

def generate_mumu_restart_script(mumu_path):
    # makes mumurestart.py in the path user gives
    restart_script = f'''import os
import time
import subprocess

# Step 1: close mumuplayer
os.system("taskkill /F /IM MumuPlayer.exe")  # change if the process name is different

# Step 2: wait a few seconds to ensure its closed
time.sleep(5)

# Step 3: reopen mumuplayer
mumu_path = r"{mumu_path}"  # this will be replaced by the users input
subprocess.Popen(mumu_path)

# Step 4: wait for mumuplayer to fully load
time.sleep(20)  # adjust based on loading time

'''
    with open("mumurestart.py", "w", encoding="utf-8") as f:
        f.write(restart_script)
    print("mumurestart.py has been generated!")

def start_bot():
    token = token_entry.get()
    channel_id = channel_id_entry.get()
    alert_channel_id = alert_channel_id_entry.get()
    wait_time = wait_time_entry.get()
    mumu_path = mumu_path_entry.get()

    # save inputs for future use
    save_inputs()

    # hide the input fields and button
    for widget in root.winfo_children():
        widget.pack_forget()

    # create a text widget for console output
    console_text = ctk.CTkTextbox(root, width=380, height=300)
    console_text.pack(pady=20)

    # create a button to start MumuPlayer below the console
    def start_mumuplayer():
        try:
            print("Starting MumuPlayer...")
            subprocess.Popen(mumu_path)  # start MumuPlayer with the provided path
        except Exception as e:
            console_text.insert(ctk.END, f"Error starting MumuPlayer: {str(e)}\n")
            console_text.see(ctk.END)

    mumu_button = ctk.CTkButton(root, text="Start MumuPlayer", command=start_mumuplayer)
    mumu_button.pack(pady=10)

    def redirect_output():
        sys.stdout = sys.stderr = ConsoleRedirector(console_text)

    redirect_output()

    # ensure mumu_path uses raw string or double backslashes
    mumu_path = mumu_path.replace("\\", "\\\\")  # Escape the backslashes

    # generate mumurestart.py with user input
    generate_mumu_restart_script(mumu_path)

    bot_code = f'''import discord
import asyncio
import datetime
import subprocess
from discord.ext import tasks

TOKEN = "{token}"
CHANNEL_ID = {channel_id}
ALERT_CHANNEL_ID = {alert_channel_id}

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True

client = discord.Client(intents=intents)

last_webhook_time = None

@client.event
async def on_ready():
    print(f'Logged in as {{client.user}}')
    alert_channel = client.get_channel(ALERT_CHANNEL_ID)
    if alert_channel:
        await alert_channel.send("Bot online!")  # send message when bot is online
    print("Successfully Launched Bot")  # message after successfully launching the bot
    check_webhook_task.start()

@client.event
async def on_message(message):
    global last_webhook_time
    if message.webhook_id:
        last_webhook_time = datetime.datetime.utcnow()

@tasks.loop(seconds=60)
async def check_webhook_task():
    global last_webhook_time
    if last_webhook_time:
        elapsed_time = (datetime.datetime.utcnow() - last_webhook_time).total_seconds()
        if elapsed_time > {wait_time}:  # user-defined wait time
            alert_channel = client.get_channel(ALERT_CHANNEL_ID)
            if alert_channel:
                await alert_channel.send("⚠️ Game has crashed, Restarting MumuPlayer.|| <@796819163129577493>|| ")

                # after the alert message is sent open the command prompt and run mumurestart.py
                print("Running mumurestart.py...")
                subprocess.Popen(['cmd', '/c', 'start', 'python', 'mumurestart.py'])
                time.sleep(30)  # wait for 30 seconds before closing the command prompt
                os.system("taskkill /F /IM cmd.exe")  # close the command prompt

                last_webhook_time = datetime.datetime.utcnow()

client.run(TOKEN)
'''

    with open("bot_script.py", "w", encoding="utf-8") as f:
        f.write(bot_code)

    def run_bot():
        console_text.insert(ctk.END, f"Logging in as {token}\n")  # logging in message
        try:
            process = subprocess.Popen(["python", "bot_script.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            while True:
                output = process.stdout.readline()
                if output == b'' and process.poll() is not None:
                    break
                if output:
                    console_text.insert(ctk.END, f"Output: {output.decode()}\n")
                    console_text.see(ctk.END)
            # capture stderr for errors
            error_output = process.stderr.read().decode()
            if error_output:
                console_text.insert(ctk.END, f"Error: {error_output}\n")
                console_text.see(ctk.END)
        except Exception as e:
            console_text.insert(ctk.END, f"Failed to run bot script\n")
            console_text.see(ctk.END)

    threading.Thread(target=run_bot).start()

class ConsoleRedirector:
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, text):
        self.text_widget.insert(ctk.END, text)
        self.text_widget.see(ctk.END)

    def flush(self):
        pass  # UI setup
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")
root = ctk.CTk()
root.title("Discord Bot Setup")
root.geometry("400x400")

# UI components (define all components here)
ctk.CTkLabel(root, text="Enter Bot Token:").pack()
token_entry = ctk.CTkEntry(root, width=300)
token_entry.pack()

ctk.CTkLabel(root, text="Enter Channel ID:").pack()
channel_id_entry = ctk.CTkEntry(root, width=300)
channel_id_entry.pack()

ctk.CTkLabel(root, text="Enter Alert Channel ID:").pack()
alert_channel_id_entry = ctk.CTkEntry(root, width=300)
alert_channel_id_entry.pack()

ctk.CTkLabel(root, text="Enter Wait Time (seconds):").pack()
wait_time_entry = ctk.CTkEntry(root, width=300)
wait_time_entry.pack()

ctk.CTkLabel(root, text="Enter MumuPlayer Path:").pack()
mumu_path_entry = ctk.CTkEntry(root, width=300)
mumu_path_entry.pack()

colors = ["red", "orange", "yellow", "green", "blue", "purple"]
index = 0

# load previously entered inputs (called after UI elements are created)
load_previous_inputs()

# button to start the bot
start_button = ctk.CTkButton(root, text="Start Bot", command=start_bot)
start_button.pack(pady=20)

# my promo :)
label = ctk.CTkLabel(root, text="Made by bennnyr. on discord", font=("Arial", 12))
label.pack(pady=20)

def smooth_rainbow():
    while True:
        for i in range(360):
            rgb = colorsys.hsv_to_rgb(i / 360, 1, 1)  
            rgb = tuple(int(c * 255) for c in rgb) 
            hex_color = f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}" 
            label.configure(text_color=hex_color) 
            time.sleep(0.02)  

threading.Thread(target=smooth_rainbow, daemon=True).start()

# run the main loop
root.mainloop()
