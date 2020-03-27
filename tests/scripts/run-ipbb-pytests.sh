#!/usr/bin/env bash

HERE=$(cd $(dirname ${BASH_SOURCE}) && pwd)

cd ${HERE}/../pytests

pytest
