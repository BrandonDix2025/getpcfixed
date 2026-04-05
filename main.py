from logger import show_log, log_event
from scanner import scan_system_data
from diagnose import diagnose
from startup import run_startup_fixer
from cleaner import clean_junk
def show_menu():
    print("=== GetPCFixed ===")
    print("")
    print("1. Scan my PC")
    print("2. AI Diagnosis")
    print("3. Fix Startup Programs")
    print("4. Clean Junk Files")
    print("5. View History")
    print("6. Exit")
    print("")

def main():
    while True:
        show_menu()
        choice = input("What would you like to do? (1-4): ")
        print("")

        if choice == "1":
            from scanner import scan_system
            scan_system()

        elif choice == "2":
            diagnose()

        elif choice == "3":
            run_startup_fixer()

        elif choice == "4":
            clean_junk()

        elif choice == "5":
            show_log()

        elif choice == "6":
            print("Goodbye! Your PC is in good hands. 💪")
            break

        else:
            print("Please enter a number between 1 and 4.")

        if choice != "6":
            print("")
            input("Press Enter to return to the menu...")
            print("")

main()