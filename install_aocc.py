#!/usr/bin/python3

import os
import subprocess
import sys

def usage():
    print("Usage: python install_aocc.py")
    print("Example: python install_aocc.py")
    sys.exit(1)

def check_command(command):
    return subprocess.call(f"command -v {command}", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0

def install_packages():
    print("Installing required packages...")
    try:
        subprocess.run(["sudo", "apt", "update"], check=True)
        subprocess.run(["sudo", "apt", "install", "wget", "-y"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error installing packages: {e}")
        sys.exit(1)

def install_environment_modules():
    if not check_command("module"):
        print("Installing environment-modules...")
        try:
            subprocess.run(["sudo", "apt", "install", "--no-install-recommends", "environment-modules", "-y"], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error installing environment-modules: {e}")
            sys.exit(1)

def download_aocc():
    tarball = "aocc-compiler-5.0.0.tar"
    if not os.path.isfile(tarball):
        print(f"Downloading AOCC compiler version 5.0.0...")
        url = "https://download.amd.com/developer/eula/aocc/aocc-5-0/aocc-compiler-5.0.0.tar"

        try:
            subprocess.run(["wget", url], check=True)
            print("Download completed.")
        except subprocess.CalledProcessError as e:
            print(f"Error downloading AOCC: {e}")
            sys.exit(1)
    else:
        print(f"AOCC tarball '{tarball}' already exists. Skipping download.")

def extract_aocc():
    print("Extracting AOCC...")
    try:
        subprocess.run(["tar", "-xvf", "aocc-compiler-5.0.0.tar", "-C", os.path.expanduser("~/compiler_installation")], check=True)
    except Exception as e:
        print(f"Error extracting AOCC: {e}")
        sys.exit(1)

def create_module_file(version, install_dir):
    modulefile_dir = os.path.expanduser(f"~/compiler_modulefiles/aocc")
    os.makedirs(modulefile_dir, exist_ok=True)

    modulefile_path = os.path.join(modulefile_dir, f"aocc-{version}")

    try:
        with open(modulefile_path, 'w') as f:
            f.write(f"""#%Module1.0

proc ModulesHelp {{ }} {{
    global version modroot
    puts stderr "AOCC version {version} - sets the environment for aocc-{version}"
}}

module-whatis "Sets the environment for AOCC version {version}"

    set             root                   {install_dir}
    setenv          COMPILERROOT           {install_dir}
    setenv          AOCCROOT               {install_dir}
    setenv          CC                     $root/bin/clang
    setenv          CXX                    $root/bin/clang++
    setenv          FC                     $root/bin/flang
    setenv          F90                    $root/bin/flang
    prepend-path    PATH                   $root/bin
    prepend-path    LIBRARY_PATH           $root/lib
    prepend-path    LD_LIBRARY_PATH        $root/lib
    prepend-path    C_INCLUDE_PATH         $root/include
    prepend-path    CPLUS_INCLUDE_PATH     $root/include
""")
    except IOError as e:
        print(f"Error creating module file: {e}")
        sys.exit(1)

def update_bashrc():
    bashrc_path = os.path.expanduser("~/.bashrc")

    try:
        # Read existing .bashrc content to check for MODULEPATH
        with open(bashrc_path, 'r') as bashrc:
            content = bashrc.read()

        # Append MODULEPATH if it doesn't exist
        if 'export MODULEPATH' not in content:
            with open(bashrc_path, 'a') as bashrc:
                bashrc.write('export MODULEPATH=${MODULEPATH}:$HOME/compiler_modulefiles\n')
                print("Added MODULEPATH to .bashrc.")

                # Inform user to source .bashrc
                print("Please run 'source ~/.bashrc' or restart your terminal to update your environment.")

                return True
        else:
            print("MODULEPATH already exists in .bashrc.")
            return False

    except IOError as e:
        print(f"Error updating .bashrc: {e}")
        sys.exit(1)

def main():
   # No version argument needed for AOCC installation
   version = "5.0.0"
   install_dir = os.path.expanduser(f"~/compiler_installation/aocc-compiler-{version}")

   # Create installation directory if it doesn't exist
   os.makedirs(install_dir, exist_ok=True)

   # Install environment modules
   install_environment_modules()

   # Install required packages
   install_packages()

   # Download and extract AOCC.
   download_aocc()
   extract_aocc()

   # Create module file after installation.
   create_module_file(version, install_dir)
   update_bashrc()

   print(f"AOCC version {version} has been installed successfully in {install_dir}.")
   print(f"Module file created at ~/compiler_modulefiles/aocc/aocc-{version}.")

if __name__ == "__main__":
   main()
