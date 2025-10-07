#!/usr/bin/python3
import reservationapi
import configparser
import time
import os

# ansi  escape codes for colors
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
BOLD = "\033[1m"
RESET = "\033[0m"

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_welcome_banner():
    banner = f"""
{BOLD}{CYAN}
======================================================
   Welcome to the Wedding Planner Booking System
======================================================
{RESET}
    """
    print(banner)

api_cache = {}  
CACHE_TTL = 2   

def get_cached(key, func, *args, **kwargs):
    now = time.time()
    if key in api_cache:
        result, ts = api_cache[key]
        if now - ts < CACHE_TTL:
            return result
    result = func(*args, **kwargs)
    api_cache[key] = (result, now)
    return result

config = configparser.ConfigParser()
config.read("api.ini")

hotel_api = reservationapi.ReservationApi(
    config['hotel']['url'],
    config['hotel']['key'],
    int(config['global']['retries']),
    float(config['global']['delay'])
)

band_api = reservationapi.ReservationApi(
    config['band']['url'],
    config['band']['key'],
    int(config['global']['retries']),
    float(config['global']['delay'])
)

current_slot = None

def view_current_reservations():
    try:
        hotel_held = get_cached("hotel_held", hotel_api.get_slots_held)
    except Exception as e:
        hotel_held = f"{RED}Error: {e}{RESET}"
    try:
        band_held = get_cached("band_held", band_api.get_slots_held)
    except Exception as e:
        band_held = f"{RED}Error: {e}{RESET}"
    print(f"\n{BOLD}{YELLOW}Current Reservations:{RESET}")
    print(f"{GREEN}Hotel held slots:{RESET} {hotel_held}")
    print(f"{GREEN}Band held slots:{RESET} {band_held}")

def view_available_slots():
    try:
        hotel_avail = get_cached("hotel_avail", hotel_api.get_slots_available)
    except Exception as e:
        hotel_avail = []
        print(f"{RED}Error fetching hotel available slots: {e}{RESET}")
    try:
        band_avail = get_cached("band_avail", band_api.get_slots_available)
    except Exception as e:
        band_avail = []
        print(f"{RED}Error fetching band available slots: {e}{RESET}")
    print(f"\n{BOLD}{YELLOW}Available Slots (first 20):{RESET}")
    print(f"{GREEN}Hotel:{RESET} {hotel_avail[:20]}")
    print(f"{GREEN}Band:{RESET} {band_avail[:20]}")

def view_matching_slots():
    try:
        hotel_avail = get_cached("hotel_avail", hotel_api.get_slots_available)
        band_avail = get_cached("band_avail", band_api.get_slots_available)
        hotel_ids = set(int(slot["id"]) for slot in hotel_avail)
        band_ids = set(int(slot["id"]) for slot in band_avail)
        matching = sorted(hotel_ids.intersection(band_ids))
        if matching:
            print(f"\n{BOLD}{YELLOW}Matching Slots (first 5):{RESET} {matching[:5]}")
        else:
            print(f"\n{RED}No matching slots available.{RESET}")
    except Exception as e:
        print(f"{RED}Error viewing matching slots: {e}{RESET}")

def manually_reserve_slot():
    slot_id = input(f"\n{BOLD}Enter slot ID to reserve: {RESET}").strip()
    hotel_reserved = False
    band_reserved = False
    try:
        hotel_resp = hotel_api.reserve_slot(slot_id)
        hotel_reserved = True
        print(f"{GREEN}Hotel reservation succeeded for slot {slot_id}:{RESET} {hotel_resp}")
    except Exception as e:
        print(f"{RED}Hotel reservation failed for slot {slot_id}:{RESET} {e}")

    time.sleep(1) 

    try:
        band_resp = band_api.reserve_slot(slot_id)
        band_reserved = True
        print(f"{GREEN}Band reservation succeeded for slot {slot_id}:{RESET} {band_resp}")
    except Exception as e:
        print(f"{RED}Band reservation failed for slot {slot_id}:{RESET} {e}")

    if hotel_reserved and band_reserved:
        print(f"{BOLD}{GREEN}Successfully reserved slot {slot_id} for both services.{RESET}")
        return int(slot_id)
    else:
        if hotel_reserved:
            try:
                hotel_api.release_slot(slot_id)
                print(f"{YELLOW}Cancelled hotel reservation for slot {slot_id} due to incomplete booking.{RESET}")
            except Exception as e:
                print(f"{RED}Error cancelling hotel reservation for slot {slot_id}:{RESET} {e}")
        if band_reserved:
            try:
                band_api.release_slot(slot_id)
                print(f"{YELLOW}Cancelled band reservation for slot {slot_id} due to incomplete booking.{RESET}")
            except Exception as e:
                print(f"{RED}Error cancelling band reservation for slot {slot_id}:{RESET} {e}")
        print(f"{RED}Manual reservation aborted due to incomplete booking.{RESET}")
        return None

def cancel_reservation():
    """Cancels a reservation for a given slot by prompting the user for a slot ID."""
    slot_id = input(f"\n{BOLD}Enter slot ID to cancel: {RESET}").strip()
    try:
        hotel_resp = hotel_api.release_slot(slot_id)
        print(f"{GREEN}Hotel reservation for slot {slot_id} cancelled:{RESET} {hotel_resp}")
    except Exception as e:
        print(f"{RED}Error cancelling hotel reservation for slot {slot_id}:{RESET} {e}")

    try:
        band_resp = band_api.release_slot(slot_id)
        print(f"{GREEN}Band reservation for slot {slot_id} cancelled:{RESET} {band_resp}")
    except Exception as e:
        print(f"{RED}Error cancelling band reservation for slot {slot_id}:{RESET} {e}")

def auto_reserve_earliest_matching_slot():
    
    try:
        hotel_avail = get_cached("hotel_avail", hotel_api.get_slots_available)
        band_avail = get_cached("band_avail", band_api.get_slots_available)
        hotel_ids = set(int(slot["id"]) for slot in hotel_avail)
        band_ids = set(int(slot["id"]) for slot in band_avail)
        matching = sorted(hotel_ids.intersection(band_ids))
        if not matching:
            print(f"\n{RED}No matching slots available for auto-reservation.{RESET}")
            return None
        earliest = matching[0]
        print(f"\n{BOLD}Attempting to reserve the earliest matching slot: {earliest}{RESET}")
        hotel_reserved = False
        band_reserved = False
        try:
            hotel_resp = hotel_api.reserve_slot(str(earliest))
            hotel_reserved = True
            print(f"{GREEN}Hotel reservation succeeded for slot {earliest}:{RESET} {hotel_resp}")
        except Exception as e:
            print(f"{RED}Hotel reservation failed for slot {earliest}:{RESET} {e}")

        time.sleep(1)

        try:
            band_resp = band_api.reserve_slot(str(earliest))
            band_reserved = True
            print(f"{GREEN}Band reservation succeeded for slot {earliest}:{RESET} {band_resp}")
        except Exception as e:
            print(f"{RED}Band reservation failed for slot {earliest}:{RESET} {e}")

        if hotel_reserved and band_reserved:
            print(f"{BOLD}{GREEN}Successfully reserved earliest matching slot {earliest} for both services.{RESET}")
            return earliest
        else:
            if hotel_reserved:
                try:
                    hotel_api.release_slot(str(earliest))
                    print(f"{YELLOW}Cancelled hotel reservation for slot {earliest} due to partial booking.{RESET}")
                except Exception as e:
                    print(f"{RED}Error cancelling hotel reservation for slot {earliest}:{RESET} {e}")
            if band_reserved:
                try:
                    band_api.release_slot(str(earliest))
                    print(f"{YELLOW}Cancelled band reservation for slot {earliest} due to partial booking.{RESET}")
                except Exception as e:
                    print(f"{RED}Error cancelling band reservation for slot {earliest}:{RESET} {e}")
            print(f"{RED}Auto-reservation aborted due to incomplete booking.{RESET}")
            return None

    except Exception as e:
        print(f"{RED}Error during auto-reservation: {e}{RESET}")
        return None

def continuous_upgrade_monitoring(current_slot, upgrade_interval=30):
    
    print(f"\n{BOLD}{CYAN}Starting continuous upgrade monitoring...{RESET}")
    print(f"{MAGENTA}Press Ctrl-C to stop monitoring and return to the main menu.{RESET}")
    while True:
        try:
            hotel_avail = get_cached("hotel_avail", hotel_api.get_slots_available)
            band_avail = get_cached("band_avail", band_api.get_slots_available)
            hotel_ids = set(int(slot["id"]) for slot in hotel_avail)
            band_ids = set(int(slot["id"]) for slot in band_avail)
            matching = sorted(hotel_ids.intersection(band_ids))
            
            if not matching:
                print(f"{YELLOW}No matching slots available for upgrade at this time.{RESET}")
            else:
                best_available = matching[0]
                if best_available < current_slot:
                    print(f"\n{BOLD}{CYAN}Better slot found: {best_available} (current reserved: {current_slot}){RESET}")
                    new_hotel_reserved = False
                    new_band_reserved = False
                    try:
                        hotel_resp = hotel_api.reserve_slot(str(best_available))
                        new_hotel_reserved = True
                        print(f"{GREEN}Hotel upgrade reservation succeeded for slot {best_available}:{RESET} {hotel_resp}")
                    except Exception as e:
                        print(f"{RED}Hotel upgrade reservation failed for slot {best_available}:{RESET} {e}")
                    
                    time.sleep(1)
                    
                    try:
                        band_resp = band_api.reserve_slot(str(best_available))
                        new_band_reserved = True
                        print(f"{GREEN}Band upgrade reservation succeeded for slot {best_available}:{RESET} {band_resp}")
                    except Exception as e:
                        print(f"{RED}Band upgrade reservation failed for slot {best_available}:{RESET} {e}")

                    if new_hotel_reserved and new_band_reserved:
                        print(f"{BOLD}{GREEN}Upgrade successful: new slot {best_available} reserved on both services.{RESET}")
                        try:
                            hotel_api.release_slot(str(current_slot))
                            print(f"{YELLOW}Released hotel reservation for old slot {current_slot}.{RESET}")
                        except Exception as e:
                            print(f"{RED}Error releasing hotel old slot {current_slot}:{RESET} {e}")
                        try:
                            band_api.release_slot(str(current_slot))
                            print(f"{YELLOW}Released band reservation for old slot {current_slot}.{RESET}")
                        except Exception as e:
                            print(f"{RED}Error releasing band old slot {current_slot}:{RESET} {e}")
                        current_slot = best_available
                    else:
                        if new_hotel_reserved:
                            try:
                                hotel_api.release_slot(str(best_available))
                                print(f"{YELLOW}Cancelled partial hotel upgrade for slot {best_available}.{RESET}")
                            except Exception as e:
                                print(f"{RED}Error cancelling hotel upgrade for slot {best_available}:{RESET} {e}")
                        if new_band_reserved:
                            try:
                                band_api.release_slot(str(best_available))
                                print(f"{YELLOW}Cancelled partial band upgrade for slot {best_available}.{RESET}")
                            except Exception as e:
                                print(f"{RED}Error cancelling band upgrade for slot {best_available}:{RESET} {e}")
                        print(f"{RED}Upgrade attempt aborted due to partial booking failure.{RESET}")
                else:
                    print(f"{CYAN}No upgrade available. Current slot {current_slot} remains optimal (best available: {matching[0]}).{RESET}")
        except Exception as e:
            print(f"{RED}Error during upgrade monitoring: {e}{RESET}")
        
        time.sleep(upgrade_interval) 

def print_menu():
    menu = f"""
{BOLD}{BLUE}===== Wedding Planner Menu ====={RESET}
{BOLD}1.{RESET} View Current Reservations
{BOLD}2.{RESET} View Available Slots (first 20)
{BOLD}3.{RESET} View Matching Slots (first 5)
{BOLD}4.{RESET} Manually Reserve a Specific Slot
{BOLD}5.{RESET} Cancel a Reservation
{BOLD}6.{RESET} Automatically Reserve the Earliest Matching Slot
{BOLD}7.{RESET} Start Continuous Upgrade Monitoring
{BOLD}8.{RESET} Exit
{BOLD}{BLUE}================================{RESET}
"""
    print(menu)

def main_menu():
    global current_slot
    while True:
        clear_screen()
        print_welcome_banner()
        print_menu()
        choice = input(f"{BOLD}Select an option (1-8): {RESET}").strip()
        if choice == "1":
            view_current_reservations()
        elif choice == "2":
            view_available_slots()
        elif choice == "3":
            view_matching_slots()
        elif choice == "4":
            reserved = manually_reserve_slot()
            if reserved is not None:
                current_slot = reserved
        elif choice == "5":
            cancel_reservation()
        elif choice == "6":
            reserved = auto_reserve_earliest_matching_slot()
            if reserved is not None:
                current_slot = reserved
        elif choice == "7":
            if current_slot is None:
                print(f"{RED}No current reservation available. Please reserve a slot first (option 4 or 6).{RESET}")
            else:
                try:
                    continuous_upgrade_monitoring(current_slot)
                except KeyboardInterrupt:
                    print(f"\n{YELLOW}Continuous upgrade monitoring stopped. Returning to main menu.{RESET}")
        elif choice == "8":
            print(f"{MAGENTA}Exiting. Goodbye!{RESET}")
            break
        else:
            print(f"{RED}Invalid choice, please select a number between 1 and 8.{RESET}")
        time.sleep(1)
        input(f"\n{BOLD}Press Enter to continue...{RESET}")

if __name__ == "__main__":
    clear_screen()
    print_welcome_banner()
    view_current_reservations()  
    input(f"\n{BOLD}Press Enter to proceed to the menu...{RESET}")
    main_menu()
