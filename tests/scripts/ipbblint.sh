#!/bin/bash

pylint --msg-template="{category}: {line:3d},{column:2d}: {msg} ({symbol})" -E ipbb.cli