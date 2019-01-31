#!/usr/bin/env bash

# Build docs
cd docs
make clean
make html
cd ..

# Commit and push
git add -A
git commit -m "building and publishing docs"
git push origin master

# Switch branch and pull data
git checkout gh-pages
rm -rf *
touch .nojekyll
git checkout master docs/_build/html
mv ./docs/_build/html/* ./
rm -rf ./docs

# Commit and push
git add -A
git commit -m "publishing updated docs..."
git push origin gh-pages

# Switch back to master
git checkout master
