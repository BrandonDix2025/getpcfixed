import winreg
from logger import log_event

def get_startup_programs():
    programs = []

    keys = [
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
        (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run"),
    ]

    for hive, key_path in keys:
        try:
            key = winreg.OpenKey(hive, key_path)
            i = 0
            while True:
                try:
                    name, value, _ = winreg.EnumValue(key, i)
                    programs.append({"name": name, "path": value, "hive": hive, "key_path": key_path})
                    i += 1
                except OSError:
                    break
            winreg.CloseKey(key)
        except OSError:
            pass

    return programs

def disable_startup_program(program):
    try:
        key = winreg.OpenKey(program["hive"], program["key_path"], 0, winreg.KEY_WRITE)
        winreg.DeleteValue(key, program["name"])
        winreg.CloseKey(key)
        return True
    except OSError:
        return False

def undo_startup_disable(name, path, hive, key_path):
    """Re-add a startup entry that was previously disabled."""
    try:
        key = winreg.OpenKey(hive, key_path, 0, winreg.KEY_WRITE)
        winreg.SetValueEx(key, name, 0, winreg.REG_SZ, path)
        winreg.CloseKey(key)
        return True
    except OSError:
        return False

def run_startup_fixer():
    programs = get_startup_programs()

    print("=== GetPCFixed — Startup Programs ===")
    print("")
    for i, prog in enumerate(programs):
        print(f"{i + 1}. {prog['name']}")
        print(f"   {prog['path']}")
    print("")
    print(f"Total: {len(programs)} startup programs found")
    print("")

    choice = input("Enter the number of the program to disable (or 0 to cancel): ")

    if choice == "0":
        print("No changes made. Goodbye!")
        return

    index = int(choice) - 1
    selected = programs[index]

    print("")
    print(f"You selected: {selected['name']}")
    confirm = input("Are you sure you want to disable this? (yes/no): ")

    if confirm.lower() != "yes":
        print("No changes made. Goodbye!")
        return

    success = disable_startup_program(selected)

    print("")
    if success:
        print(f"✅ FIXED — {selected['name']} has been disabled from startup.")
        print("Your PC will boot faster next time.")
        log_event("Startup Fix", f"Disabled {selected['name']} from startup")
    else:
        print(f"❌ Could not disable {selected['name']}. Try running as Administrator.")

if __name__ == "__main__":
    run_startup_fixer()