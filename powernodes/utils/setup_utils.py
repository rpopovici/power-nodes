import os
import sys
import site

def ensure_user_sitepackages():
    user_site_packages_path = site.getusersitepackages()

    if not os.path.exists(user_site_packages_path):
        print("Create user site packages folder..")
        os.makedirs(user_site_packages_path)
        user_site_packages_path = site.getusersitepackages()

    if os.path.exists(user_site_packages_path) and user_site_packages_path not in sys.path:
        sys.path.append(user_site_packages_path)
