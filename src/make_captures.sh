#!/bin/sh

TRIALS=1
PARAMS=sym
./experiment.py -t $TRIALS --params $PARAMS --setup nat
./experiment.py -t $TRIALS --params $PARAMS --setup vpn

PARAMS=sym_lossy
./experiment.py -t $TRIALS --params $PARAMS --setup nat
./experiment.py -t $TRIALS --params $PARAMS --setup vpn

PARAMS=sym_delayed
./experiment.py -t $TRIALS --params $PARAMS --setup nat
./experiment.py -t $TRIALS --params $PARAMS --setup vpn

PARAMS=easy
./experiment.py -t $TRIALS --params $PARAMS --setup nat
./experiment.py -t $TRIALS --params $PARAMS --setup vpn

PARAMS=lossy
./experiment.py -t $TRIALS --params $PARAMS --setup nat
./experiment.py -t $TRIALS --params $PARAMS --setup vpn

PARAMS=delayed
./experiment.py -t $TRIALS --params $PARAMS --setup nat
./experiment.py -t $TRIALS --params $PARAMS --setup vpn
