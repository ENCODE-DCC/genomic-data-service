# Docker image

## Overview

The image built using the `Dockerfile` in this directory is used for running the tests on [circleCI](https://www.circleci.com). The resulting image is stored in [Dockerhub](https://hub.docker.com/), and the tag of the image used for testing is `encodedcc/gds_test:latest`.

## Building image

You can build the image locally using command `docker build -t encodedcc/gds_test:latest .` in this directory. After building the image you can push the image up to dockerhub with command `docker push encodedcc/gds_test:latest` (You will be asked to authenticate with dockerhub). Note that if you break the image, it will affect tests on all the branches, so take care when modifying the image.
