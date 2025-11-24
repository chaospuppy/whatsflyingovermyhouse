#!/bin/bash

OPENSKY_REPO="https://github.com/openskynetwork/opensky-api.git"
OPENSKY_REV="master"
OPENSKY_COMMIT="85fdcc1"

vendor_dir="vendor"

mkdir -p "./$vendor_dir"
git clone --branch $OPENSKY_REV $OPENSKY_REPO $vendor_dir
pushd $vendor_dir
git reset --hard $OPENSKY_COMMIT
popd

uv pip install "$vendor_dir/python/"

rm -rf $vendor_dir
