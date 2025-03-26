# sgbackup - SaveGame Backup

## Install

### Requirements

* Python 3 >= 3.11
* pip
* GObject + GObject Introspection for Python
* Gtk4 + Python bindings
* GIT


### All OSes

````shell
# Download sgbackup
git clonse https://github.com/c9moser/sgbackup.git

# change to sgbackup directory
cd sgbackup

# install requirements
pip install -r requirements.txt

# install sgbackup
pip install .
````

### Windows

 Download *MSYS2* from [the MSys2 site](https://www.msys2.org)
 and install it. To update *MSYS2* to the latest version
 start a MSYS2 terminal and run:

```shell
pacman -Syu
```

If the terminal quits, restart it and run the above command again.

Install git and download *sgbackup* and install it.

```shell
# Install git
pacman -S git

# Download sgbackup.
git clone https://github.com/c9moser/sgbackup.git

# Switch to the sgbackup directory and run the installer.
cd sgbackup
./msys-install.sh
```

### Fedora

````shell
# install git
sudo dnf install -y git

# download sgbackup
git clone https://github.com/c9moser/sgbackup.git

# cd to sgbackup-directory and install sgbackup
cd sgbackup
./fedora-install.sh
````

### Cent OS 10 / Alma Linux 10

````shell
# install git
sudo dnf install -y git

# download sgbackup
git clone https://github.com/c9moser/sgbackup.git

# cd to sgbackup-directory and install sgbackup
cd sgbackup
./centos-install.sh
````
