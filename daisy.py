import functions
import os


def main():

    while True:
        os.system("cls" if os.name == "nt" else "clear")           

        if functions.check_internet():
            #Detect a wake word before listening for a prompt
            if functions.listen_for_wake_word() == True:
                functions.notification_sound.play()
                print("LISTENING...");
                #context = chat(context)
                functions.chat()
        else:
            print(f"{colorama.Fore.RED}No Internet connection. {colorama.Fore.WHITE}When a connection is available the script will automatically re-activate.")


main()
