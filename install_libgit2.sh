#!/bin/sh -x

ROOT=$(cd $(dirname $0); pwd)

if [ -e libgit2 ]; then
    (cd libgit2; git pull origin development)
else
    git clone -b development git://github.com/libgit2/libgit2.git
fi

rm -rf libgit2/build
mkdir libgit2/build
cd libgit2/build
cmake -DCMAKE_INSTALL_PREFIX:PATH=$ROOT/env ..
make all install
