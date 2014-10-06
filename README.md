OpenBAS
===============

## Deployment Setup

See `INSTALL.md` in this directory

## Development Setup

### Getting Started

Install [Meteorite](http://atmospherejs.com/docs/installing).

To install all the dependencies and run the app:

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

#### Problems Being up to date?

1. from clean openbas install
2. `mrt migrate-app` -- this will fail
3. remove accounts-ui-bootstrap-3 and collectionfs from smart.json, remove trailing comma from line 8
4. `mrt install`
5. `mrt migrate-app`
6. remove `cfs-*`, `collectionfs` from packages, .meteor/packages
7. `meteor remove cmather:iron-router`
8. `meteor add iron:router`
9. `meteor add mizzao:jquery-ui`
10. `meteor remove mizzao:jqueryui`
11. `meteor remove mrt:bootstrap-3`
12. `meteor add mizzao:bootstrap-3`
13. `sed -e 's/^[a-zA-Z0-9]/meteor remove &/' .meteor/packages | sed 's/\@[0-9\.]*//g' > packages-rm.sh`
14. `sed -e 's/ remove / add /' packages-rm.sh > packages-add.sh`
15. `bash packages-rm.sh`
16. `meteor list`
17. `meteor update`
18. `bash packages-add.sh`
19. `meteor add cfs:standard-packages`
20. `meteor add cfs:filesystem`
21. `meteor --settings settings.json` should work


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
