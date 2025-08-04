import sys
import os
from modules import dns, dnscrypt, vpn
from modules.status_check import run_status_check
from modules.utils import clear_terminal, print_banner

def main():
    args = sys.argv[1:]

    # ✅ تنفيذ الخدمات مؤقتًا عند تمرير --status-only
    if "--status-only" in args:
        print("[INFO] Running status check only. Starting VPN, DNS, and DNSCrypt temporarily...")
        dns.run()
        dnscrypt.run()
        vpn.run()
        run_status_check()
        return

    # ❌ تجنب تنفيذ هذه الإجراءات في وضع TEST_MODE
    if os.environ.get("TEST_MODE") != "true":
        clear_terminal()
        print_banner()

    dns.run()
    dnscrypt.run()
    vpn.run()

    run_status_check()

if __name__ == "__main__":
    main()
