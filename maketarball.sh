echo "[]" > openbas/private/testrooms.json
cd openbas
which mrt
if [ $? != 0 ]
then
  echo "No MRT, assuming clean repository"
else
  mrt reset
fi
cd ..
rm -f openbas.tgz
tar zcf openbas.tgz openbas upmu-plotter
git checkout openbas/private
echo "Done"
