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
#   many files, all starting with capturename. Just read the script

# Fail on first error
set -e
# Fail on unset var
set -u
# Print commands
#set -x

# Requires mptcpparser, a tool which is not publicly available.
MPTCPPARSER=$HOME/code/mptcptools/mptcpparser

FILENAME=$(basename "$1")
BASE="${FILENAME%.*}"
DIR=`mktemp -d`

cp $1 $DIR/input.pcap
pushd $DIR

# packet trace -> xplot file
$MPTCPPARSER input.pcap

popd

# Put output files into place.
mv $DIR/connection_1-ORIGIN.xpl $BASE.xpl
mv $DIR/connection_1-MAPPING.txt $BASE.mapping.txt

# Generate some statistics using good'ole tcptrace
tcptrace $BASE.pcap > $BASE.summary.txt
tcptrace -l $BASE.pcap > $BASE.detail.txt

# Clean up
rm -rf $DIR
