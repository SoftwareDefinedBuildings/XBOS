# Contributions

This is a quick guide on how to contribute to XBOS and where code contributions should go.

## Prerequisites

- Create a free [GitHub account](https://github.com/join)
- Install Git on your computer
    - do this through your favorite package manager if you are familiar with command-line interfaces
    - OR, install the GitHub [desktop application](https://desktop.github.com/) (Mac OS X or Windoze), which has helpful [documentation](https://help.github.com/desktop/guides/). Don't forget to [set it up](https://help.github.com/desktop/guides/getting-started-with-github-desktop/)

## Setting up your copy

Collaboration happens by making edits to your own "fork" of the XBOS project; when your changes are ready for others to use or test, you can submit a "pull request".
This section discusses how to set up the fork the first time. This only needs to be done once.

1. Begin by forking the [XBOS project](https://github.com/softwaredefinedbuildings/XBOS) by clicking the "Fork" button in the top-right.
 This will create a copy of the project under your own account. You can make changes to this copy without affecting the main XBOS project.
2. Clone the new project under your account
    - [directions for desktop](https://help.github.com/desktop/guides/contributing-to-projects/cloning-a-repository-from-github-desktop/#platform-mac)

## Organizing Stuff

The XBOS project has several folders used to organize its various components. Depending on what you are contributing, it should go in a different folder.

- [`apps/`](https://github.com/SoftwareDefinedBuildings/XBOS/tree/master/apps): contains end-use applications for doing control, analysis, etc.
- [`dashboards/`](https://github.com/SoftwareDefinedBuildings/XBOS/tree/master/dashboards): contains code for user-facing dashboards
- [`services/`](https://github.com/SoftwareDefinedBuildings/XBOS/tree/master/services): contains code for applications that are used by other applications

If you are unsure where something should go, just ask!

## Contributing

After making your edits on your local copy, go through a quick checklist:

- have you written documentation on how your code works and how it is intended to be used?
    - this can be done in a `README.md` file
- if you are contributing Python code, have you included a `requirements.txt` file containing the dependencies?
- **make sure you remove all passwords, usernames, IP addresses and other identifying information for the systems you are developing against**

Commit your changes to your local repo ([desktop instructions](https://help.github.com/desktop/guides/contributing-to-projects/committing-and-reviewing-changes-to-your-project/)), and then file a pull request ([desktop instructions](https://help.github.com/desktop/guides/contributing-to-projects/working-with-your-remote-repository-on-github-or-github-enterprise/)).
