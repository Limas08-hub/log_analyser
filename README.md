# Log Analyser
Log Analyser is a Python pipeline that reads an SSH `auth.log` file, extracts the connection attempts with regular expressions, locates the source IPs with the ipinfo.io API, and stores everything in a PostgreSQL database. It then displays a dashboard of the results: failed attempts per country, successful attempts per user, and failed attempts with an invalid user. It is intended for system administrators who want to spot brute-force attacks on an SSH server.

## Features
the pipeline step by step :
step 1 :
   input(sources)
step 2 :
   ingestion
step 3 :
   cleaning,validation and extraction
step 4 :
   psycopg2,storage
step 5 :   
   serving ,ai,bi


## Project structure

log_analyser/
├── main.py                       # entry point: loads the logs if needed, then shows the dashboard
├── data/                         # folder with the raw log files read by the pipeline
├── data_ingestion/
│   ├── __init__.py
│   └── raw.py                    # reads the log files and returns the lines
├── data_processing/
│   ├── __init__.py
│   ├── extract_transform.py      # extracts date, host, service, IP, user... from each line (regex)
│   └── geolocation.py            # finds the country and city of an IP with ipinfo.io
├── data_storage/
│   ├── __init__.py
│   └── storage.py                # PostgreSQL connection, table creation, inserts and dashboard queries
├── data_serving/
│   ├── __init__.py
│   └── dashboard.py              # matplotlib charts
├── pyproject.toml                # project settings and dependencies
├── uv.lock                       # locked dependency versions
├── .python-version
├── .gitignore
└── README.md

## Requirements
## Requirements

- Python 3.12
- PostgreSQL, with the service running on `localhost:5432`
- An existing PostgreSQL database named `log_analyser`
- Python packages:
  - `psycopg2` (PostgreSQL connection)
  - `requests` (calls to the ipinfo.io API)
  - `matplotlib` (dashboard charts)
- An internet connection, needed to locate IP addresses with ipinfo.io
- An SSH `auth.log` file placed in the `data/` folder

## Usage
Run from the project root:

python main.py


On the first run, the table is empty, so the logs are read, stored and located before the dashboard opens. On the next runs, the dashboard opens directly from the data already in PostgreSQL.

To reload everything from the log files:

python main.py reload



## Dashboard
The dashboard opens three charts, each in its own window, and also saves them as images next to `main.py`:

- **Failed attempts by country** (`failed_by_country.png`): every country that failed password attempts came from, sorted from most to least.
- **Successful attempts by user** (`success_by_user.png`): the accounts that logged in successfully, with the number of logins.
- **Failed attempts with invalid user** (`failed_invalid_user.png`): every non-existing username that attackers tried, with the number of attempts.

Each bar shows its exact number, 



## Author
khorchef imane, ESISA, 3rd year Software Engineering, 2026