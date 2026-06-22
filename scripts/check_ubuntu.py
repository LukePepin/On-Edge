import platform
import sys

def check_ubuntu_version():
    try:
        if platform.system() != 'Linux':
            print("❌ This is not a Linux system.")
            return False

        with open('/etc/os-release', 'r') as f:
            os_info = {}
            for line in f:
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    os_info[key] = value.strip('"')
            
        if os_info.get('NAME') != 'Ubuntu':
            print(f"❌ OS is not Ubuntu. Found: {os_info.get('NAME')}")
            return False
            
        version = os_info.get('VERSION_ID')
        if version == '22.04':
            print("✅ Success: Running Ubuntu 22.04 LTS (Jammy Jellyfish).")
            return True
        else:
            print(f"❌ Incorrect Ubuntu version. Required: 22.04, Found: {version}")
            return False

    except FileNotFoundError:
        print("❌ /etc/os-release not found. Cannot verify OS details.")
        return False
    except Exception as e:
        print(f"❌ An error occurred while checking OS version: {e}")
        return False

if __name__ == "__main__":
    is_valid = check_ubuntu_version()
    sys.exit(0 if is_valid else 1)
