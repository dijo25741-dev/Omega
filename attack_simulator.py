import argparse
import json
import urllib.request
import urllib.error
import sys

BASE_URL = "http://127.0.0.1:8000"

# ANSI Terminal Colors
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
BOLD = "\033[1m"
RESET = "\033[0m"

def make_post_request(endpoint: str, payload: dict = None) -> dict:
    url = f"{BASE_URL}{endpoint}"
    data = json.dumps(payload or {}).encode("utf-8")
    req = urllib.request.Request(
        url, 
        data=data, 
        headers={"Content-Type": "application/json"}, 
        method="POST"
    )
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"{RED}[ERROR] HTTP Error {e.code}: {e.reason}{RESET}")
        try:
            err_data = json.loads(e.read().decode("utf-8"))
            print(f"Details: {err_data}")
        except Exception:
            pass
        return {}
    except urllib.error.URLError as e:
        print(f"{RED}[ERROR] Connection refused. Is the Omega FastAPI server running at {BASE_URL}?{RESET}")
        print(f"Details: {e.reason}")
        return {}

def show_banner():
    banner = f"""
{RED}{BOLD}======================================================================
                  OMEGA INDUSTRIAL ATTACK SIMULATOR
======================================================================{RESET}
   This application simulates cyber threat signatures on local systems
   and virtual PLCs to test the Omega Cyber Immune System logic.
   {YELLOW}NOTE: No actual malicious activity is performed on this machine.{RESET}
======================================================================
"""
    print(banner)

def run_interactive_menu():
    show_banner()
    while True:
        print(f"{BOLD}Select an attack vector to simulate:{RESET}")
        print(f" 1. {CYAN}Reconnaissance{RESET} (Port scans, network enumeration, device discovery)")
        print(f" 2. {CYAN}Credential Attack{RESET} (Multiple failed brute-force admin logins)")
        print(f" 3. {CYAN}Lateral Movement{RESET} (Suspicious remote sessions, new device communication)")
        print(f" 4. {CYAN}PLC Attack{RESET} (Force STOP ALL PUMPS, CLOSE VALVES, shutdown overrides)")
        print(f" 5. {CYAN}Malware Simulation{RESET} (Spike host CPU/memory, fake encryption threads)")
        print(f" 6. {CYAN}Insider Threat{RESET} (Authorized admin issuing critical commands outside window)")
        print(f" 7. {RED}Force Emergency Lockout{RESET} (Workstation lockout simulation)")
        print(f" 8. {GREEN}Trigger Self-Healing Recovery{RESET} (Launch system restore)")
        print(f" 9. {YELLOW}Reset to Normal Baseline{RESET}")
        print(f" 0. Exit")
        
        try:
            choice = input(f"\n{BOLD}Enter choice (0-9): {RESET}").strip()
            if choice == "1":
                trigger_recon()
            elif choice == "2":
                trigger_credentials()
            elif choice == "3":
                trigger_lateral()
            elif choice == "4":
                trigger_plc()
            elif choice == "5":
                trigger_malware()
            elif choice == "6":
                trigger_insider()
            elif choice == "7":
                trigger_emergency()
            elif choice == "8":
                trigger_recovery()
            elif choice == "9":
                trigger_reset()
            elif choice == "0":
                print("Exiting simulator.")
                sys.exit(0)
            else:
                print(f"{RED}Invalid option. Please try again.{RESET}")
        except KeyboardInterrupt:
            print("\nExiting simulator.")
            sys.exit(0)
        print("-" * 70)

def trigger_recon():
    print(f"\n{YELLOW}[*] Simulating network reconnaissance...{RESET}")
    res = make_post_request("/attack/recon")
    if res:
        print(f"{GREEN}[+] SUCCESS: {res.get('attack')}{RESET}")
        print(f"    Action: {res.get('action_taken')}")

def trigger_credentials():
    print(f"\n{YELLOW}[*] Simulating failed administrative credential sweeps...{RESET}")
    res = make_post_request("/attack/credentials")
    if res:
        print(f"{GREEN}[+] SUCCESS: {res.get('attack')}{RESET}")
        print(f"    Action: {res.get('action_taken')}")

def trigger_lateral():
    print(f"\n{YELLOW}[*] Simulating lateral pivots and suspicious network logins...{RESET}")
    res = make_post_request("/attack/lateral")
    if res:
        print(f"{GREEN}[+] SUCCESS: {res.get('attack')}{RESET}")
        print(f"    Action: {res.get('action_taken')}")

def trigger_plc():
    print(f"\n{YELLOW}[*] Injecting PLC command abuse overrides (STOP PUMPS / CLOSE VALVES)...{RESET}")
    res = make_post_request("/attack/plc")
    if res:
        print(f"{GREEN}[+] SUCCESS: {res.get('attack')}{RESET}")
        print(f"    Action: {res.get('action_taken')}")

def trigger_malware():
    print(f"\n{YELLOW}[*] Loading host malware & ransomware indicators...{RESET}")
    res = make_post_request("/attack/malware")
    if res:
        print(f"{GREEN}[+] SUCCESS: {res.get('attack')}{RESET}")
        print(f"    Action: {res.get('action_taken')}")

def trigger_insider():
    print(f"\n{YELLOW}[*] Simulating out-of-schedule insider operational edits...{RESET}")
    res = make_post_request("/attack/insider")
    if res:
        print(f"{GREEN}[+] SUCCESS: {res.get('attack')}{RESET}")
        print(f"    Action: {res.get('action_taken')}")

def trigger_emergency():
    print(f"\n{RED}[*] Triggering manual workstation console lock...{RESET}")
    res = make_post_request("/attack/emergency")
    if res:
        print(f"{GREEN}[+] SUCCESS: Workstation Interlock Engaged{RESET}")
        print(f"    State: {res.get('status')}")

def trigger_recovery():
    print(f"\n{GREEN}[*] Initiating self-healing automated system recovery...{RESET}")
    res = make_post_request("/attack/recovery")
    if res:
        print(f"{GREEN}[+] SUCCESS: Recovery Process Started{RESET}")
        print(f"    State: {res.get('status')}")

def trigger_reset():
    print(f"\n{YELLOW}[*] Normalizing all systems to baseline operations...{RESET}")
    res = make_post_request("/api/reset")
    if res:
        print(f"{GREEN}[+] SUCCESS: Baseline Restored{RESET}")
        print(f"    State: {res.get('status')}")

def main():
    parser = argparse.ArgumentParser(description="Omega Cyber Defense Attack Simulator CLI")
    parser.add_argument(
        "--attack", 
        type=str, 
        choices=["recon", "credentials", "lateral", "plc", "malware", "insider", "emergency", "recovery", "reset"],
        help="Run a specific attack simulation vector directly"
    )
    args = parser.parse_args()
    
    if args.attack:
        show_banner()
        if args.attack == "recon":
            trigger_recon()
        elif args.attack == "credentials":
            trigger_credentials()
        elif args.attack == "lateral":
            trigger_lateral()
        elif args.attack == "plc":
            trigger_plc()
        elif args.attack == "malware":
            trigger_malware()
        elif args.attack == "insider":
            trigger_insider()
        elif args.attack == "emergency":
            trigger_emergency()
        elif args.attack == "recovery":
            trigger_recovery()
        elif args.attack == "reset":
            trigger_reset()
    else:
        run_interactive_menu()

if __name__ == "__main__":
    main()
