OpenBAS
===============

## Deployment Setup

See `INSTALL.md` in this directory

## Development Setup

### Getting Started

Install [Meteorite](http://atmospherejs.com/docs/installing).

To install all the dependencies and run the app,

```
cd openbas
mrt --settings settings.json
```

When cloning this for the first time, make sure that you have the `upmu-plotter` submodule updated. To do this,
run the following command from the same directory as this README:

```
git submodule update --init
git submodule foreach git pull origin master
```

#### If on Ubuntu system:

Install Meteor

```
curl https://install.meteor.com | sh
```

Put Meteor's node on the path
```
export PATH=~/.meteor/tools/latest/bin:$PATH
```

Install NPM, Node's package manager
```
sudo apt-get install npm
```

Install meteorite

```
sudo -H npm install -g meteorite
```

From within the openbas folder, run the following to install dependencies
and run the app

```
mrt --settings settings.json
```


#### Running OpenBAS

* change subscription key in building.ini for your local archiver
* change archiver location in settings.json for local archiver
* change public.site in settings.json to be Metadata/Site for building.ini
* install pymongo:
  ```
  sudo pip install pymongo
  ```
  OR
  ```
  sudo apt-get install python-pymongo
  ```

  then run the source:

  ```
  twistd -n smap building.ini
  ```
