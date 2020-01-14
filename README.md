# Delayed Jobs

This API runs jobs such as generating CSV files or doing substructure and blast searches. 

# How to Run it Locally

**python version:** 3.7
You must create a configuration file and set its path to CONFIG_FILE_PATH. For examples, see the configurations folder.
```
pip install -r requirements.txt
CONFIG_FILE_PATH=<Path to your configuration file> FLASK_APP=app/app.py flask run
```

Open http://127.0.0.1:5000/ in your browser

# Running Static Analysis 

```bash
find . -iname "*.py" | xargs pylint
```

# Running Unit Tests

```bash
python -m unittest
```

# Running Functional Tests

1. Start a server locally

```bash
pushd app/functional_tests
 ./run_functional_tests.py
popd
```

2. Stop the server