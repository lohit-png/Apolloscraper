# Apollo Scraper - Quick Start Guide

## What You Have

Three clean, production-ready files:

1. **`apollo_scraper.py`** - The main scraper (400 lines, well-documented)
2. **`README_APOLLO_SCRAPER.md`** - Complete user documentation
3. **`test_apollo_scraper.py`** - Validation tests (all passing ✅)

## Quick Start (30 seconds)

```bash
# 1. Set your API key
export APOLLO_API_KEY="your_apollo_api_key_here"

# 2. Run the scraper
python3 apollo_scraper.py

# 3. Paste your Apollo search URL when prompted
```

That's it!

## How It Works

### Automatic Segmentation

The scraper intelligently handles large searches:

1. **Under 50k results?** → Extracts in one go
2. **Over 50k results?** → Auto-breaks by employee ranges
3. **Still over 50k?** → Auto-breaks by US states (all 51)

You never have to think about Apollo's 50k limit!

### Multi-Threading

- Uses 4 parallel workers for speed
- Thread-safe file operations
- Automatic progress reporting

### Output

Creates timestamped CSV files:
```
apollo_20251101_120000.csv                        # Simple search
apollo_20251101_120000_emp_11-20.csv             # By employee range
apollo_20251101_120000_emp_101-200_Texas.csv     # By range + state
apollo_20251101_120000_summary.json              # Metadata
```

## Validation Tests

Run the included tests to verify everything works:

```bash
python3 test_apollo_scraper.py
```

**Expected output:**
```
✅ ALL TESTS PASSED (5/5)
```

Tests validate:
- ✅ URL parsing
- ✅ Filter extraction
- ✅ API parameter building
- ✅ Contact data extraction
- ✅ State segmentation logic

## Example Usage

### Simple Search (Under 50k)

```bash
$ python3 apollo_scraper.py
Enter Apollo search URL: https://app.apollo.io/#/people?personTitles[]=CEO&personLocations[]=Montana

Total results found: 5,234
✅ Under 50,000 limit - no segmentation needed

Continue with extraction? (y/n): y

[8 minutes later...]

✅ All done!
Files created:
  • apollo_20251101_120000.csv: 5,234 contacts
```

### Large Search (Auto-Segmented)

```bash
$ python3 apollo_scraper.py
Enter Apollo search URL: [paste your URL with multiple employee ranges]

Total results found: 150,000
⚠️  Exceeds 50,000 limit - will segment the search

📊 Breaking by 3 employee ranges...
  • 11,20: 48,000 results
  • 21,50: 52,000 results  
    ↳ Still too large, breaking by 51 states...
  • 51,100: 50,000 results
    ↳ Still too large, breaking by 51 states...

Total segments: 103
Estimated total contacts: 150,000

Continue with extraction? (y/n): y

[Multi-threaded extraction with 4 workers...]

✅ All done!
Total contacts extracted: 149,876
Total time: 45.2 minutes
```

## Key Features

### Security
- ✅ API key never printed to console
- ✅ Uses environment variables
- ✅ Safe for GitHub sharing

### Smart
- ✅ Auto-detects when to segment
- ✅ Skips already-completed files (resumable)
- ✅ Handles all Apollo filter types

### Fast
- ✅ Multi-threaded (4 workers)
- ✅ Minimal rate limiting
- ✅ Batch CSV writing

### Clean
- ✅ PEP 8 compliant
- ✅ Well-commented
- ✅ No external config files needed
- ✅ Only 1 dependency: `requests`

## Sharing on GitHub

The code is ready to share! It:

- Never exposes API keys
- Has clear documentation
- Includes validation tests
- Follows best practices
- Has helpful error messages

## Troubleshooting

### "APOLLO_API_KEY environment variable is required"

Set your API key:
```bash
export APOLLO_API_KEY="your_key_here"
```

To check if it's set:
```bash
echo $APOLLO_API_KEY
```

### "Invalid Apollo URL format"

Make sure your URL includes `#/people?` and looks like:
```
https://app.apollo.io/#/people?personTitles[]=CEO&...
```

### Validation tests fail

Make sure you're using Python 3.7+:
```bash
python3 --version
```

## Performance

Typical extraction speeds:

| Size | Segments | Time |
|------|----------|------|
| 10k contacts | 1 | ~3-5 min |
| 50k contacts | 1-2 | ~15-20 min |
| 100k contacts | 3-5 | ~30-40 min |
| 200k contacts | 10-20 | ~60-90 min |

Speed depends on:
- Apollo API response time
- Your internet connection
- Number of segments required

## What's Included

```
apollo_scraper.py              # Main scraper (400 lines)
README_APOLLO_SCRAPER.md       # Full documentation
test_apollo_scraper.py         # Validation tests
APOLLO_SCRAPER_QUICKSTART.md   # This file
```

## Support

All validation tests passing? You're good to go! 🚀

For questions about Apollo's API limits or filters, check their documentation at https://apolloio.github.io/apollo-api-docs/

---

**Happy scraping!** 🎯

