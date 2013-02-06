#!/bin/sh -x

ROOT=$(cd $(dirname $0); pwd)

if [ -e libgit2 ]; then
    (cd libgit2; git pull origin development)
else
    git clone -b development git://github.com/libgit2/libgit2.git
fi
#(cd libgit2; git reset --hard fb60d268df2272626f48cfed7b2a185413e7e9f4)

rm -rf libgit2/build
mkdir libgit2/build
cd libgit2/build
cmake -DCMAKE_INSTALL_PREFIX:PATH=$ROOT/env ..
make all install
