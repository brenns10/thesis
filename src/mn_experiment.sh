#!/bin/sh

PARAMS=sym
./experiment.py -t 20 --params $PARAMS --setup control
./experiment.py -t 20 --params $PARAMS --setup nat
./experiment.py -t 20 --params $PARAMS --setup vpn
PARAMS=sym_lossy
./experiment.py -t 20 --params $PARAMS --setup control
./experiment.py -t 20 --params $PARAMS --setup nat
./experiment.py -t 20 --params $PARAMS --setup vpn
PARAMS=sym_delayed
./experiment.py -t 20 --params $PARAMS --setup control
./experiment.py -t 20 --params $PARAMS --setup nat
./experiment.py -t 20 --params $PARAMS --setup vpn
PARAMS=easy
./experiment.py -t 20 --params $PARAMS --setup control
./experiment.py -t 20 --params $PARAMS --setup nat
./experiment.py -t 20 --params $PARAMS --setup vpn
PARAMS=lossy
./experiment.py -t 20 --params $PARAMS --setup control
./experiment.py -t 20 --params $PARAMS --setup nat
./experiment.py -t 20 --params $PARAMS --setup vpn
PARAMS=delayed
./experiment.py -t 20 --params $PARAMS --setup control
./experiment.py -t 20 --params $PARAMS --setup nat
./experiment.py -t 20 --params $PARAMS --setup vpn
