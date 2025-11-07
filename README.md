# Apollo Scraper V2

Production-ready Apollo.io contact scraper with intelligent segmentation and dual file output.

## Features

- ✅ **50 requests per minute** - Controlled API consumption
- ✅ **Dual file output** - Complete data + cleaned subset
- ✅ **Auto-segmentation** - Handles lists over 50k automatically
- ✅ **Multi-threaded** - Fast parallel extraction
- ✅ **Resumable** - Picks up where it left off

## Quick Start

```bash
# 1. Set your API key
export APOLLO_API_KEY="your_apollo_api_key_here"

# 2. Run the scraper
python3 apollo_scraper.py

# 3. Paste your Apollo search URL when prompted
```

## Output Files

Every search creates two files:

1. **Complete file** (`apollo_[timestamp].csv`) - All 40+ fields
2. **Cleaned file** (`apollo_[timestamp]_cleaned.csv`) - 9 essential columns:
   - first_name
   - last_name
   - name
   - title
   - linkedin_url
   - org_name
   - org_website_url
   - org_linkedin_url
   - org_primary_domain

## Documentation

- [Updates & Changes](APOLLO_SCRAPER_UPDATES.md) - What's new in V2
- [Quick Start Guide](APOLLO_SCRAPER_QUICKSTART.md) - Detailed usage

## Requirements

- Python 3.7+
- `requests` library

```bash
pip install requests
```

## Legal & Compliance

This scraper uses the official Apollo.io API with proper authentication. Ensure you:
- Have valid Apollo.io API credentials
- Comply with Apollo.io's Terms of Service
- Follow applicable data protection regulations (GDPR, CCPA, etc.)

---

**Ready to extract!** 🚀

