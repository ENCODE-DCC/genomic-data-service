# Docker image

## Overview

The image built using the `Dockerfile` is used for running the test on [circleCI](https://www.circleci.com). The resulting image is stored in [Dockerhub](https://hub.docker.com/), and the tag of the image used for testing is `encodedcc/gds_test:latest`.

## Building image

You can build the image locally using command `docker build -t encodedcc/gds_test:latest .` in this directory. After building the image you can push the image up to dockerhub with command `docker push encodedcc/gds_test:latest`. 
