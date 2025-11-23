# SkillMiner

## Database Setup

To initialize and build the database, run the following commands:


```bash
cd database
make install
python scripts/download_kaggle.py
make export-sqlite
```

## Test Dataset
To generate or verify test data locally:
```bash
cd database
python scripts/make_test_data.py
make test
```

## Output Structure
```bash
data/raw/                        # Kaggle raw data
data/bornze/jobs.parquet
data/silver/jobs_text.parquet
data/gold/role_skills_by_title.parquet

data/test/tiny_jobs.parquet      # If run test dataset
data/test/tiny_jobs_text.parquet
data/test/tiny_role_skills_by_title.parquet

database/skillminer.db           # Final SQLite database 
```

python version: 3.11.13
(3.11.9 for windows)
