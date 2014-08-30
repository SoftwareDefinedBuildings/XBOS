Installing OpenBAS
===============

Welcome to the installation instructions for OpenBAS! This guide is intended to
walk you through setting up your local OpenBAS server.

## System Requirements

OpenBAS requires either Ubuntu Server 14.04 or Ubuntu Desktop 14.04 (Trusty Tahr). We recommend having at least:

* 1 GHz processor
* 2 GB RAM
* 5 GB disk space

Any relatively recent consumer-grade machine from the past 5 years should have no problem running Ubuntu and OpenBAS.

### Installing Ubuntu 14.04

Ubuntu 14.04 is available for free download from
[http://www.ubuntu.com/download/desktop/](http://www.ubuntu.com/download/desktop/).
The easiest installation methods are either from DVD or from a USB thumbstick
(instructions for how to do this from Ubuntu, Windows or Mac OS X are all
available [here](http://www.ubuntu.com/download/desktop/)).

Once you have your DVD or your USB drive with Ubuntu 14.04 loaded, follow the
directions at
[http://www.ubuntu.com/download/desktop/install-ubuntu-desktop](http://www.ubuntu.com/download/desktop/install-ubuntu-desktop)
to install. The instructions are for the Ubuntu Desktop edition, which includes
a graphical interface that is familiar and easier to use for users newer to
Ubuntu. However, because OpenBAS provides a web-based interface, running a
graphical environment on your OpenBAS server is not necessary. The Ubuntu
Server edition will work just as well, if not better, than the Desktop edition.

**NOTE: do not forget the username and password that you input during the installation process!**

## Installing

1. **Open the Terminal**: If you are on Ubuntu Desktop, open up the Terminal application by pressing
`Ctl-Alt-T` (pressing the 'Control', 'Alt' and the 't' keys at the same time).
If you are on Ubuntu Server, you should already be looking at a terminal. If
you aren't, turn your computer on.

2. **Make sure you have `curl` installed**: type the following command into the Terminal and press 'Enter':

  ```
  which curl
  ```

  If this gives you output, like printing out `/usr/bin/curl`, then you are fine! If not, you will need to install
  it:

  ```
  sudo apt-get install -y curl
  ```

  You will probably need to type in your password.

3. **Install OpenBAS:** We've made this part very easy! Simply type into the terminal the following:

  ```
  curl http://install.openbas.cal-sdb.org/ | sudo bash -
  ```

  which will install and configure your system to run OpenBAS. It will tell you exactly what it is doing,
  and by the end of the process, your computer should have OpenBAS installed and running.

4. **Configure the sMAP Archiver** (this part will soon be integrated into step 3)

   ```
   sudo apt-get install -y powerdb2
   ```

   This will ask if you want to create a superuser (type 'yes' and press enter). Enter a username,
   an optional email, and a password.

5. After `powerdb2` is installed, go to http://servername/admin and type in the username and password you created in the last step. If you are installing on a machine locally, this would be [http://localhost/admin](http://localhost/admin). Click '+Add' next to 'Subscriptions', enter a description (e.g. 'OpenBAS deployment') and replace the 'Key' field with the default key:
  ```
  lVzBMDpnkXApJmpjUDSvm4ceGfpbrLLSd9cq
  ```
  Then click 'Save'.
  
6. At this point, you have now installed all the needed OpenBAS software. You can now proceed to configuration your installation for this building.

## Getting Started

**Note:** if you are running anti-virus software, it can misclassify OpenBAS's discovery service as a malignant process and block your access to OpenBAS. Please disable any anti-virus on your personal computer when installing OpenBAS.

Links generated:

* OpenBAS Building Dashboard: http://servername:3000 e.g [http://localhost:3000](http://localhost:3000)
* Plotting Interace: http://servername e.g [http://localhost](http://localhost)
* Admin Interface: http://servername/admin e.g [http://localhost/admin](http://localhost/admin)

When first bringing up OpenBAS for your installation, follow the following steps:

1. Create rooms: visit http://servername/building e.g [http://localhost:3000/building](http://localhost:3000/building) and create some rooms, making sure to place markers on the map.
2. Plug in devices!
3. Configure devices on the status page http://servername/status e.g [http://localhost:3000/status](http://localhost:3000/status)
