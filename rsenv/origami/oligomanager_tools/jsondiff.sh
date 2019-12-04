#!/bin/bash

set -x # Xtrace - good for debugging. (use '+' to de-activate)
#set -v # Verbose? (Prints entire script)
set +e # Set exit-on-error. Must be de-activated ('+e'), as diff will return with an error-like value.

## NO SPACES before or after assignment '=':
tempfolder=".jsondifftemp"
if [ ! -d $tempfolder ]; then
  mkdir $tempfolder
fi

#design1='Box.Closed.Jan09'
cp $1 $tempfolder
design1="$tempfolder/${1##*/}"
#design2='Box.Closed.Dec10'
cp $2 $tempfolder
design2="$tempfolder/${2##*/}"

#echo "Copy $design1.json -> $design1.breaked1"
echo "cp $design1 $design1.breaked1"
cp $design1 $design1.breaked1
ls $tempfolder
#echo "search-replace on $design1.breaked1"
perl -pi -w -e 's/},{/},\n{/g;' $design1.breaked1

#echo "cp $design1.breaked1 $design1.breaked2"
cp $design1.breaked1 $design1.breaked2
perl -pi -w -e 's/\],"/\[,\n"/g;' $design1.breaked2
 
cp $design2 $design2.breaked1
perl -pi -w -e 's/},{/},\n{/g;' $design2.breaked1

cp $design2.breaked1 $design2.breaked2
perl -pi -w -e 's/\],"/\[,\n"/g;' $design2.breaked2

#echo "diff1" 
diff $design1.breaked1 $design2.breaked1 > $tempfolder/breaked1.diff
#echo "diff2"
diff $design1.breaked2 $design2.breaked2 > $tempfolder/breaked2.diff
echo "Comparing file:"
echo "   - '$design1'"
echo "to - '$design2'"
echo "You can also find this output in $tempfolder/breaked1.diff together with breaked2.diff."
echo ""
cat $tempfolder/breaked2.diff
