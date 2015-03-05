## ReactJS + Socket.IO + Websockets

I like this setup


### Setting Up

You will need 

* [bower](http://bower.io/)
* [npm](https://docs.npmjs.com/getting-started/installing-node)

which are both fairly standard JS tools. The individual packages we are using
can be found in `package.json` for server-side packages, and `bower.json` for
client-side packages. To install everything, run

```bash
$ cd openbas_reactjs_socketio
$ bower install
$ npm install
```

The ReactJS JSX files (essentially the source files for the client application)
need to be compiled before they can be used. Until I can think of (or find the
standard way of) distributing the compiled JSX files, I run the JSX compiler
in "watch" mode from the `public` directory:

```bash
$ jsx -w ../react_src/ build/
```

This won't terminate; it will continuously compile your JSX files in `react_src`
and report any syntax errors.

To run the server, run

```bash
$ npm start
```

from the repository's root directory. Right now, every time I change the ReactJS
source files, I have to restart the server. There's probably a way round this, but
I don't know what it is yet.

**Make sure you are running Giles as well.**
