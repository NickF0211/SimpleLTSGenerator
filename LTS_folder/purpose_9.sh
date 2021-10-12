#! /bin/sh
# Tue 18 May 2021 04:52:08 PM EDT

TESTOR_DIR=${TESTOR_DIR:-..}

# check the presence of CADP

if [ "$CADP" = "" ] ; then
	echo "$0: \$CADP should point to the installation directory of CADP"
	exit 1
elif [ ! -d $CADP ] ; then
	echo "$0: directory \$CADP does not exist"
	exit 1
fi

ARCH=`$CADP/com/arch`

echo
echo "compose the bcg"
svl demo

echo
echo "minimize model.bcg"
bcg_min full_graph.bcg

bcg_info -labels full_graph.bcg | cut -d ' ' -f 1 | sort -u > label.io
sed -i '1d;$d' label.io
echo input >> label.io
sed -i '1s/^/input\n/' label.io

echo
echo "generate purpose.bcg"
lnt.open purpose_9.lnt generator -rename tgv.rename purpose_9.bcg


#echo
#echo "compute complete test graph"
bcg_open full_graph.bcg $TESTOR_DIR/bin.$ARCH/testor.a -total -io label.io purpose_9.bcg tc.bcg