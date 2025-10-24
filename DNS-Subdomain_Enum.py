#!/usr/bin/env python3

# -------- Import Libraries ------------
import dns.resolver
import requests
import threading
import os

#------ Setting Up DNS Record Types and Resolver ---------
def dns_enum(domain):
    records_type = ['A', 'AAAA', 'CNAME', 'MX', 'TXT', 'SOA']
    resolver = dns.resolver.Resolver()
    results = []

# ------------------ Querying Records ------------------
    print(f"\n[*] Starting DNS enumeration for {domain}...\n")
    for record_type in records_type:
        try:
            answer = resolver.resolve(domain, record_type)
            results.append(f"{record_type} records for {domain}:")
            for data in answer:
                results.append(f" {data}")
        except dns.resolver.NoAnswer:
            continue
        except dns.resolver.NXDOMAIN:
            results.append(f"The domain '{domain}' does not exist.")
            break
        except dns.resolver.Timeout:
            results.append(f"DNS query for {record_type} timed out.")
            continue
        except Exception as e:
            results.append(f"Error querying {record_type}: {e}")
            continue

    # --------------- Save DNS results ---------------
    safe_domain = domain.replace('.', '_')
    dns_filename = f"dns_results_{safe_domain}.txt"
    with open(dns_filename, 'w', encoding='utf-8') as f:
        for line in results:
            f.write(line + '\n')

    print(f"\n✅ DNS results saved to {dns_filename}")
    return results

# ------------- Subdomain Enumeration -----------------

# ----------- Subdomain Loading Wordlist ---------------
def subdomain_enum(domain):
    # Prompt user for custom subdomain file path
    file_path = input("Enter the path to subdomain.txt (leave blank to use default in script directory): ").strip()
    
    # Default to script directory if no path provided
    if not file_path:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(script_dir, 'subdomain.txt')
    
    # Check if the file exists
    if not os.path.exists(file_path):
        print(f"❌ File not found at {file_path}. Please provide a valid path to subdomain.txt.")
        return

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            subdomains = f.read().splitlines()
    except Exception as e:
        print(f"❌ Error reading subdomain.txt: {e}")
        return

    print(f"\n[*] Loaded {len(subdomains)} subdomains to check...")

# ----------- Subdomain Setting Up Threads -----------------
    discovered_subdomains = []
    lock = threading.Lock()

# -------------- Checking Subdomains -----------------------
    def check_subdomain(subdomain):
        url = f"http://{subdomain}.{domain}"
        try:
            response = requests.get(url, timeout=3)
            if response.status_code < 400:
                print(f"[+] Discovered subdomain: {url}")
                with lock:
                    discovered_subdomains.append(url)
        except requests.RequestException:
            pass
        except:
            url = url.replace("http://", "https://")
            try:
                requests.get(url, timeout=3)
                print(f"[+] Discovered subdomain: {url}")
                with lock:
                    discovered_subdomains.append(url)
            except:
                pass

# --------------- Running Threads ------------------------
    threads = []
    for subdomain in subdomains:
        thread = threading.Thread(target=check_subdomain, args=(subdomain,))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

# ----------- Saving Results ------------------------------
    safe_domain = domain.replace('.', '_')
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, f"discovered_subdomain_{safe_domain}.txt")

    # Avoid overwriting
    if os.path.exists(output_path):
        i = 1
        while True:
            new_path = os.path.join(script_dir, f"discovered_subdomain_{safe_domain}_{i}.txt")
            if not os.path.exists(new_path):
                output_path = new_path
                break
            i += 1

    with open(output_path, 'w', encoding='utf-8') as f:
        for sub in discovered_subdomains:
            f.write(sub + '\n')

    print(f"\n✅ Finished. Found {len(discovered_subdomains)} live subdomains.")
    print(f"Results saved to: {output_path}")

# ---------------- Main Function ----------------------------------
def main():
    domain = input("Enter the target domain (e.g. example.com): ").strip()
    if not domain:
        print("❌ No domain entered.")
        return

    dns_enum(domain)

    choice = input("\nDo you want to run subdomain enumeration? (y/n): ").strip().lower()
    if choice in ('y', 'yes'):
        subdomain_enum(domain)
    else:
        print("Skipping subdomain enumeration.")

if __name__ == "__main__":
    main()