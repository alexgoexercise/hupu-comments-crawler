# Hupu NBA Crawler

A Scrapy-based web crawler for collecting NBA match statistics and fan comments from Hupu (虎扑), a popular Chinese basketball community.

## Project Structure

```
hupu_crawler/
├── hupu_crawler/
│   ├── spiders/
│   │   ├── nodeid_spider.py      # Spider to collect NBA root node IDs
│   │   └── match_spider.py       # Spider to collect match statistics and comments
│   ├── settings.py               # Scrapy configuration
│   └── pipelines.py              # Data processing pipelines
├── scrapy.cfg                    # Scrapy project configuration
└── README.txt                    # This file
```

## Prerequisites

- Python 3.7+
- Scrapy framework
- Required packages: `scrapy`, `pandas` (optional, for data analysis)

Install Scrapy:
```bash
pip install scrapy
```

## Usage Guide

### Step 1: Collect NBA Root Node IDs

The `nodeid_spider.py` crawls Hupu's API to discover NBA match root node IDs, which are required for collecting detailed statistics and comments.

#### Basic Usage:
```bash
cd hupu_crawler
scrapy crawl nodeid -o nba_root_ids.json
```

#### Advanced Usage with Custom Range:
```bash
# Crawl specific ID range (e.g., IDs 1000-2000)
scrapy crawl nodeid -a min_id=1000 -a max_id=2000 -o nba_root_ids.json

# Crawl from ID 0 to 5000
scrapy crawl nodeid -a min_id=0 -a max_id=5000 -o nba_root_ids.json
```

#### What it does:
- Sends requests to Hupu's API endpoint: `getSubGroups`
- Discovers NBA team matches within the specified ID range
- Filters results to only include basketball matches
- Outputs a JSON file with structure:
  ```json
  [
    {
      "outBizNo": "149",
      "groupName": "76人",
      "rootNodeId": "1549649"
    },
    ...
  ]
  ```

#### Output File: `nba_root_ids.json`
This file contains the mapping between business IDs and root node IDs needed for the next step.

### Step 2: Collect Match Statistics and Comments

The `match_spider.py` uses the collected root node IDs to fetch detailed player statistics and fan comments for each match.

#### Basic Usage:
```bash
cd hupu_crawler
scrapy crawl match -o nba_match_stats.csv
```

#### What it does:
1. Loads the `nba_root_ids.json` file
2. For each root node ID:
   - Fetches player statistics from the `groupAndSubNodes` API
   - Collects up to 3 hottest fan comments for each player
   - Cleans comment text to prevent CSV parsing issues
3. Outputs a CSV file with comprehensive match data

#### Output File: `nba_match_stats.csv`
The CSV contains the following columns:
- `outBizNo`: Business ID for the match
- `team`: Team name in Chinese
- `rootNodeId`: Root node ID for the match
- `playerName`: Player name
- `matchScore`: Match score (e.g., "凯尔特人 114-106 76人")
- `minutes`: Minutes played
- `pts`: Points scored
- `ast`: Assists
- `reb`: Rebounds
- `stl`: Steals
- `blk`: Blocks
- `plusMinus`: Plus/minus rating
- `comment1`, `comment2`, `comment3`: Top 3 fan comments

## Configuration

### Settings (`settings.py`)

Key configuration options:
- `FEED_EXPORT_ENCODING = "utf-8-sig"`: UTF-8 with BOM for Excel compatibility
- `CSV_EXPORT_QUOTING = 1`: Quote all fields to handle commas in comments
- `DOWNLOAD_DELAY = 1`: 1 second delay between requests to be respectful

### Customizing the Crawl

#### Adjusting ID Ranges:
```python
# In nodeid_spider.py, modify the default range:
def __init__(self, min_id=0, max_id=6000, *args, **kwargs):
    self.min_id = int(min_id)
    self.max_id = int(max_id)
```

#### Changing Output Format:
```bash
# Output as JSON instead of CSV
scrapy crawl match -o nba_match_stats.json

# Output as XML
scrapy crawl match -o nba_match_stats.xml
```

## Data Processing

### Comment Cleaning
The `clean_comment_for_csv` method in `match_spider.py` handles:
- Replacing commas with semicolons to prevent CSV parsing issues
- Converting double quotes to single quotes
- Removing newlines and carriage returns
- Trimming whitespace

### CSV Compatibility
- Uses UTF-8 with BOM encoding for Excel compatibility
- Quotes all fields to handle special characters
- Handles Chinese characters properly

## Troubleshooting

### Common Issues:

1. **Encoding Problems**: Ensure your terminal supports UTF-8
2. **Rate Limiting**: If you encounter 429 errors, increase `DOWNLOAD_DELAY` in settings
3. **Missing Data**: Some matches may not have comments or complete statistics
4. **API Changes**: Hupu may update their API endpoints; check the URLs in the spider files

### Debug Mode:
```bash
# Run with debug logging
scrapy crawl match -L DEBUG -o nba_match_stats.csv
```

## Data Analysis

After collecting the data, you can analyze it using pandas:

```python
import pandas as pd

# Read the CSV
df = pd.read_csv('nba_match_stats.csv', encoding='utf-8-sig')

# Basic statistics
print(f"Total records: {len(df)}")
print(f"Unique teams: {df['team'].nunique()}")
print(f"Records with comments: {df['comment1'].notna().sum()}")

# Filter records with comments
comments_df = df[df['comment1'].notna()]
print(f"Records with at least one comment: {len(comments_df)}")
```

## Ethical Considerations

- Respect the website's robots.txt
- Use reasonable delays between requests
- Don't overload the server
- Consider the terms of service of the websites being crawled

## License

This project is for educational and research purposes. Please respect the terms of service of the websites being crawled.

## Support

For issues or questions:
1. Check the Scrapy documentation: https://docs.scrapy.org/
2. Review the spider code for configuration options
3. Ensure all dependencies are properly installed

## Example Workflow

Complete data collection process:
```bash
# 1. Collect root node IDs
cd hupu_crawler
scrapy crawl nodeid -a min_id=0 -a max_id=1000 -o nba_root_ids.json

# 2. Collect match statistics and comments
scrapy crawl match -o nba_match_stats.csv

# 3. Verify the output
head -5 nba_match_stats.csv
```

The crawler will automatically use the generated `nba_root_ids.json` file to collect comprehensive NBA match data for LLM fine-tuning or analysis.
