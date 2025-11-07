# Apollo Scraper Updates

## Summary of Changes

The Apollo scraper has been updated with the following enhancements:

### 1. **Speed Adjustment: 50 Requests Per Minute**

- **Previous**: `REQUEST_DELAY = 0.05` seconds (1200 requests/minute)
- **Updated**: `REQUEST_DELAY = 1.2` seconds (50 requests/minute)
- **Why**: More controlled rate limiting to stay within API consumption targets

### 2. **Dual File Output**

The scraper now automatically creates **TWO files** for each search/segment:

#### **Complete File** (all data)
- Filename pattern: `apollo_[timestamp].csv`
- Contains all 40+ fields from the Apollo API
- Full contact details, organization data, metadata, etc.

#### **Cleaned File** (subset of columns)
- Filename pattern: `apollo_[timestamp]_cleaned.csv`
- Contains only the following 9 columns:
  1. `first_name`
  2. `last_name`
  3. `name`
  4. `title`
  5. `linkedin_url`
  6. `org_name`
  7. `org_website_url`
  8. `org_linkedin_url`
  9. `org_primary_domain`

### 3. **Example Output**

When you run a search, you'll see files like:

```
apollo_20251104_120000.csv                    # Complete data
apollo_20251104_120000_cleaned.csv            # Cleaned data (9 columns)
apollo_20251104_120000_summary.json           # Extraction metadata
```

For segmented searches (multiple employee ranges or states):

```
apollo_20251104_120000_emp_11-20.csv
apollo_20251104_120000_emp_11-20_cleaned.csv

apollo_20251104_120000_emp_21-50_California.csv
apollo_20251104_120000_emp_21-50_California_cleaned.csv
...
```

### 4. **Updated Summary Report**

The JSON summary now includes both file types:

```json
{
  "extraction_date": "2025-11-04T12:00:00",
  "total_segments": 3,
  "total_contacts": 15234,
  "files": [
    {
      "filename_complete": "apollo_20251104_120000.csv",
      "filename_cleaned": "apollo_20251104_120000_cleaned.csv",
      "count": 15234
    }
  ]
}
```

## Usage

No changes to usage! Just run as before:

```bash
export APOLLO_API_KEY="your_key_here"
python apollo_scraper.py
```

The scraper will automatically:
- ✅ Run at 50 requests per minute
- ✅ Create both complete and cleaned files
- ✅ Handle segmentation if needed
- ✅ Report on both file types

## Benefits

1. **Complete File**: Keep all data for future reference or advanced analysis
2. **Cleaned File**: Quick import into CRMs, lightweight for sharing, focused on essentials
3. **Controlled Speed**: Predictable API credit consumption at 50 requests/minute
4. **No Breaking Changes**: All existing functionality preserved

## What Your Team Can Do

With Cursor + this repository, your team can:

### Using the Scraper:
- ✅ Extract Apollo leads using search URLs
- ✅ Get both complete and cleaned data automatically
- ✅ Handle lists of any size (auto-segmentation)
- ✅ Resume interrupted extractions
- ✅ Track API usage and timing

### Modifying the Scraper (with AI assistance):
- ✅ Adjust the rate limit (change `REQUEST_DELAY`)
- ✅ Customize cleaned columns (modify `CLEANED_COLUMNS`)
- ✅ Add new data fields to extract
- ✅ Change output formats (JSON, Excel, etc.)
- ✅ Add integrations (CRM uploads, webhooks, etc.)
- ✅ Implement custom filtering logic
- ✅ Add data validation and enrichment

### Understanding the Code:
- ✅ Ask AI to explain any function or logic
- ✅ Debug issues with AI assistance
- ✅ Learn Python best practices from the codebase
- ✅ Understand Apollo API integration patterns

## Notes

- The scraper uses the **official Apollo API** with proper authentication
- API credits are consumed at a predictable rate (50/minute)
- Both files are written simultaneously during extraction
- Thread-safe operations ensure data integrity
- No configuration files needed - just set `APOLLO_API_KEY`

---

**Ready to use!** 🚀

