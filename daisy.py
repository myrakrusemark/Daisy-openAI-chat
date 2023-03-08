import functions
import os
import constants
import asyncio
import play_sound
import logging
import logging_setup

def main():

    while True:
        if not constants.args.verbose:
            os.system("cls" if os.name == "nt" else "clear")           

        if functions.check_internet():
            #Detect a wake word before listening for a prompt
            if functions.listen_for_wake_word() == True:
                functions.chat()
        else:
            print(f"{colorama.Fore.RED}No Internet connection. {colorama.Fore.WHITE}When a connection is available the script will automatically re-activate.")

if __name__ == '__main__':
    main()
