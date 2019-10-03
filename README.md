# Delayed Jobs

This API runs jobs such as generating CSV files or doing substructure and blast searches. 

# How to Run it Locally

```
pip install -r requirements.txt
env FLASK_APP=app/app.py flask run
```

Open http://127.0.0.1:5000/ in your browser

# Running Static Analysis 

```
find . -iname "*.py" | xargs pylint --max-line-length=120
```

# Running Unit Tests

```
python -m unittest
```