#!/bin/sh

TRIALS=20
PARAMS=sym_lossy05
./experiment.py -t $TRIALS --params $PARAMS --setup control
./experiment.py -t $TRIALS --params $PARAMS --setup nat
./experiment.py -t $TRIALS --params $PARAMS --setup vpn
PARAMS=sym_lossy2
./experiment.py -t $TRIALS --params $PARAMS --setup control
./experiment.py -t $TRIALS --params $PARAMS --setup nat
./experiment.py -t $TRIALS --params $PARAMS --setup vpn
PARAMS=sym_lossy5
./experiment.py -t $TRIALS --params $PARAMS --setup control
./experiment.py -t $TRIALS --params $PARAMS --setup nat
./experiment.py -t $TRIALS --params $PARAMS --setup vpn
PARAMS=lossy05
./experiment.py -t $TRIALS --params $PARAMS --setup control
./experiment.py -t $TRIALS --params $PARAMS --setup nat
./experiment.py -t $TRIALS --params $PARAMS --setup vpn
PARAMS=lossy2
./experiment.py -t $TRIALS --params $PARAMS --setup control
./experiment.py -t $TRIALS --params $PARAMS --setup nat
./experiment.py -t $TRIALS --params $PARAMS --setup vpn
PARAMS=lossy5
./experiment.py -t $TRIALS --params $PARAMS --setup control
./experiment.py -t $TRIALS --params $PARAMS --setup nat
./experiment.py -t $TRIALS --params $PARAMS --setup vpn

PARAMS=sym_delayed20
./experiment.py -t $TRIALS --params $PARAMS --setup control
./experiment.py -t $TRIALS --params $PARAMS --setup nat
./experiment.py -t $TRIALS --params $PARAMS --setup vpn
PARAMS=sym_delayed50
./experiment.py -t $TRIALS --params $PARAMS --setup control
./experiment.py -t $TRIALS --params $PARAMS --setup nat
./experiment.py -t $TRIALS --params $PARAMS --setup vpn
PARAMS=delayed20
./experiment.py -t $TRIALS --params $PARAMS --setup control
./experiment.py -t $TRIALS --params $PARAMS --setup nat
./experiment.py -t $TRIALS --params $PARAMS --setup vpn
PARAMS=delayed50
./experiment.py -t $TRIALS --params $PARAMS --setup control
./experiment.py -t $TRIALS --params $PARAMS --setup nat
./experiment.py -t $TRIALS --params $PARAMS --setup vpn
