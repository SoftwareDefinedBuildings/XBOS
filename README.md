# XBOS Setup

I like this setup


## Setting Up

You will need 

* [bower](http://bower.io/)
* [npm](https://docs.npmjs.com/getting-started/installing-node)

which are both fairly standard JS tools. The individual packages we are using
can be found in `package.json` for server-side packages, and `bower.json` for
client-side packages. To install everything, run

```bash
$ bower install
$ npm install
```

On Ubuntu, I found myself needing 

```bash
$ sudo apt-get install libkrb5-dev
```

The ReactJS JSX files (essentially the source files for the client application)
need to be compiled before they can be used. Until I can think of (or find the
standard way of) distributing the compiled JSX files, I run the JSX compiler
in "watch" mode from the `public` directory:

```bash
$ jsx -w react_src/ public/build/
```

This won't terminate; it will continuously compile your JSX files in `react_src`
and report any syntax errors.

To run the server, run

```bash
$ npm start
```

from the repository's root directory.

**Make sure you are running Giles as well.**

## Security

In `config.js`, you will need to replace both the `session_secret` and `salt` fields. `session_secret` should
be any random string, but `salt` should be generated using the `bin/gensalt.js` script.

Users should be created using `bin/newuser.js` and are stored in the mongo database inside the config file.
There are 2 types of users: read-only and admin. Admin users can change data, and read-only users can only view.
There is no public access -- all viewing must be handled through a user account.
