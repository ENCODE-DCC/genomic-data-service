# Genomic Data Services

## Installation Requirements

* python 3.8 (locally 3.9 and 3.10 work as well)
* postgres (only for RNAGet?)
* elasticsearch (5.6 currently)

## Application Installation

1. Create a virtual env in your work directory.
    This example uses the python module venv. Other options would also work, like conda or pyenv

    ```
    cd your-work-dir
    python3 -m venv genomic-venv
    source genomic-venv/bin/activate
    ```

2. Clone the repo and install requirements

    ```
    # Make sure you are in the genomic-venv
    cd genomic-data-service
    pip3 install -e .
    ```

3. Download our machine learning models

    ```
    python3 ./utils/download_ml_models.py
    ```

4. Run the application:

    ```
    make run
    ```

    It will be available on port 5000.

5. (Optional) Run the indexer (independent of flask application):

* if redis not running, start redis first:

    ```
    brew services start redis
    ```

* in separate windows, with virtualenv

    ```
    # start local ES
    python3 ./utils/dev_server/dev_server.py
    make worker
    make flower
    make index
    ```

* if you just want to index a small number of files for local install, run `make index_local` instead of `make index`.

* Monitoring via flower will be available on port 5555 (localhost unless otherwise set).
