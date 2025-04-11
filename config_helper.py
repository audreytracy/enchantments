import configparser
from datetime import datetime

def edit_config():
    global params
    config = configparser.ConfigParser()
    config.read('config.ini')

    print("Type 0 to quit edit")
    while True:
        selection = input(
            "Enter number [1 to 4] for the configuration you want to edit:\n"
            "[1] Email Recipients\n"
            "[2] Start Date\n"
            "[3] End Date\n"
            "[4] Zones\n"
            "Type R to run program: "
        )
        if selection == "R" or selection == "r":
            break

        updated = False  # Flag to track if any changes were made

        try:
            selection = int(selection)
            if selection == 1:
                print("Current email recipients are:", config.get('General', 'to_emails'))
                recipients = input("Enter list of email recipients delimited by semicolon with no spaces (e.g. test@gmail.com;test2@example.com) or 0 to return to menu:")
                if recipients != '0':
                    config.set('General', 'to_emails', recipients)
                    updated = True
            elif selection == 2:
                print("Current start date is:", config.get('General', 'start_date'))
                temp = input("Enter start date in form YYYY-MM-DD or 0 to return to menu: ")
                if temp != '0':
                    if is_valid(temp):
                        config.set('General', 'start_date', temp)
                        updated = True
                    else:
                        print("Invalid date format.")
            elif selection == 3:
                print("Current end date is:", config.get('General', 'end_date'))
                temp = input("Enter end date in form YYYY-MM-DD or 0 to return to menu:")
                if temp != '0':
                    if is_valid(temp):
                        config.set('General', 'end_date', temp)
                        updated = True
                    else:
                        print("Invalid date format.")
            elif selection == 4:
                print("Current zones are:", config.get('General', 'zones'))
                temp = input(
                    "Enter list of zones you want to monitor as a comma-delimited list with no spaces (e.g. 1,2) or 0 to return to menu:\n"
                    "[1] Snow Zone\n"
                    "[2] Colchuck Zone\n"
                    "[3] Stuart Zone\n"
                    "[4] Eightmile/Caroline Zone\n"
                    "[5] Core Enchantment Zone\n")
                if temp != '0':
                    try:
                        zones = [int(t) for t in temp.split(",")]
                        if any(zone < 1 or zone > 5 for zone in zones):
                            raise ValueError("Zones must be between 1 and 5.")
                        config.set('General', 'zones', ",".join(map(str, sorted(zones))))
                        updated = True
                    except ValueError as e:
                        print(f"Invalid entry: {e}")
            else:
                print("Enter a valid number from 1 to 4.")
                continue
            if updated:
                # Save changes to config.ini only if something was updated
                with open('config.ini', 'w') as configfile:
                    config.write(configfile)
                print("Configuration updated successfully.")
            else:
                print("No changes were made.")
        except ValueError:
            print("Enter a valid number from 1 to 4.")


def is_valid(string):
    try:
        datetime.strptime(string, '%Y-%m-%d')
    except Exception:
        return False
    return True

def create_config(to_emails, start_date, end_date, zones):
    config = configparser.ConfigParser()
    config['General'] = {'to_emails':to_emails,
                        'start_date':start_date,
                        'end_date':end_date,
                        'zones':zones}
    with open('config.ini', 'w') as configfile:
        config.write(configfile)

def read_config():
    config = configparser.ConfigParser()
    config.read('config.ini')
    start_date = datetime.strptime(config.get('General', 'start_date'), '%Y-%m-%d').date()
    end_date = datetime.strptime(config.get('General', 'end_date'), '%Y-%m-%d').date()
    zones_to_scan = config.get('General', 'zones')
    to_emails = config.get('General', 'to_emails')
    return {
        "start_date": start_date,
        "end_date": end_date,
        "zones": zones_to_scan,
        "to_emails": to_emails,
    }

def start():
    global params
    params = read_config()
    print("Current configuration:")
    print("Start Date:", params["start_date"]) 
    print("End Date:", params["end_date"])
    print("Zones:", params["zones"])
    print("Email Recipients:", params["to_emails"])
    choice = input("Type [E] to edit config or [R] to run the program: ")
    while choice not in ['E', 'e', 'R', 'r']:
        choice = input("Please enter a valid choice [E] or [R]: ")
    if choice in ['E', 'e']:
        edit_config()
    return params
