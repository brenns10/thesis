#!/usr/bin/env bash
#
# Create tcpdump capture plots for experiment captures.
#
# This script is very, very particular and very, very hacky. It also depends on
# some exotic tooling, at least one of which is not publicly available. Sorry.
# The script will output a gnuplot script, along with the supporting files. The
# script will in fact be suitable to run in batch, producing a PDF. You can edit
# it after the fact for better titles, etc.
#
# usage: ./capplot.sh capturename.pcap               # must have pcap extension
# output:
#  capturename.pdf
#  capturename.gpl
#  capturename.labels
#  capturename.datasets

# Fail on first error
set -e
# Fail on unset var
set -u
# Print commands
#set -x

# Requires mptcpparser, a tool which is not publicly available.
MPTCPPARSER=$HOME/code/mptcptools/mptcpparser

# Requires xpl2gpl - http://www.tcptrace.org/xpl2gpl/
XPL2GPL=$HOME/code/xpl2gpl

FILENAME=$(basename "$1")
BASE="${FILENAME%.*}"
DIR=`mktemp -d`

cp $1 $DIR/input.pcap
pushd $DIR

# packet trace -> xplot file
$MPTCPPARSER input.pcap

# xplot file -> gnuplot file
$XPL2GPL connection_1-ORIGIN.xpl

# Make PDF output!
sed -i 's/.*set term.*/set term pdf/' connection_1-ORIGIN.gpl
sed -i 's/.*set output.*/set output "'$BASE.pdf'"/' connection_1-ORIGIN.gpl

# Replace names with the original trace name.
sed -i "s/connection_1-ORIGIN/$BASE/g" connection_1-ORIGIN.gpl

# Move the plot command to the end.
grep '^plot.*' connection_1-ORIGIN.gpl >> tmp
sed -i '/.*plot.*/d' connection_1-ORIGIN.gpl
sed -i '/.*replot.*/d' connection_1-ORIGIN.gpl
sed -i '/.*pause.*/d' connection_1-ORIGIN.gpl
cat connection_1-ORIGIN.gpl tmp > $BASE.gpl
# now our finished product is $BASE.gpl

popd

# Put output files into place.
mv $DIR/$BASE.gpl .
mv $DIR/connection_1-ORIGIN.labels $BASE.labels
mv $DIR/connection_1-ORIGIN.datasets $BASE.datasets

# Generate the pdf
gnuplot $BASE.gpl

# Clean up
rm -rf $DIR
