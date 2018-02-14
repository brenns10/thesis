#!/bin/sh

TRIALS=1
PARAMS=sym
./experiment.py -t $TRIALS --params $PARAMS --setup nat --trace
./experiment.py -t $TRIALS --params $PARAMS --setup vpn --trace

PARAMS=sym_lossy
./experiment.py -t $TRIALS --params $PARAMS --setup nat --trace
./experiment.py -t $TRIALS --params $PARAMS --setup vpn --trace

PARAMS=sym_delayed
./experiment.py -t $TRIALS --params $PARAMS --setup nat --trace
./experiment.py -t $TRIALS --params $PARAMS --setup vpn --trace

PARAMS=easy
./experiment.py -t $TRIALS --params $PARAMS --setup nat --trace
./experiment.py -t $TRIALS --params $PARAMS --setup vpn --trace

PARAMS=lossy
./experiment.py -t $TRIALS --params $PARAMS --setup nat --trace
./experiment.py -t $TRIALS --params $PARAMS --setup vpn --trace

PARAMS=delayed
./experiment.py -t $TRIALS --params $PARAMS --setup nat --trace
./experiment.py -t $TRIALS --params $PARAMS --setup vpn --trace
