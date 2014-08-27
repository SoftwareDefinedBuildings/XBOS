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
  curl http://install.openbas.cal-sdb.org/install.sh | sudo sh
  -- OR --
  curl http://http://54.183.169.17/install.sh | sudo sh 
  ```

  which will install and configure your system to run OpenBAS. It will tell you exactly what it is doing,
  and by the end of the process, your computer should have OpenBAS installed and running.
