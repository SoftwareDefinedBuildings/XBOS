rm openbas/private/*.json
cd openbas
mrt reset
cd ..
rm openbas.tgz
tar zcf openbas.tgz openbas upmu-plotter
git checkout openbas/private
