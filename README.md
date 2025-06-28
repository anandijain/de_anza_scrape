# de_anza_scrape

get all the classes for a quarter at De Anza College
uses selenium, doesnt need login or anything, but make sure you have a chromedriver on path

```
uv run grab.py online --term "2025 Fall De Anza" --output fall2025.csv --save-html sample.html --debug

uv run grab.py offline sample.html sample_html.csv

uv run postprocess_courses.py -i fall2025.csv -o fall2025_processed.csv


```

