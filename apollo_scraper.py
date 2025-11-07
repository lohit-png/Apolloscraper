"""
Apollo URL Scraper - Simple & Fast
===================================

A clean, user-friendly Apollo scraper that:
- Accepts Apollo search URLs via interactive prompt
- Automatically segments lists over 50,000 (employee ranges → states)
- Uses multi-threading for fast extraction
- Outputs CSV files with clear naming
- Never exposes the API key to users

Usage:
    export APOLLO_API_KEY="your_key_here"
    python apollo_scraper.py
"""

import os
import sys
import time
import json
import csv
import requests
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from urllib.parse import unquote
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# ============================================================================
# CONFIGURATION
# ============================================================================

APOLLO_API_KEY = os.environ.get("APOLLO_API_KEY")
APOLLO_API_URL = "https://api.apollo.io/api/v1/mixed_people/search"

# Rate limits and threading
RECORDS_PER_PAGE = 100
MAX_PAGES_PER_SEARCH = 500
MAX_RESULTS_PER_SEARCH = 50000
NUM_WORKERS = 4
REQUEST_DELAY = 1.2  # seconds between requests (50 requests per minute)

# Cleaned file columns (subset of all fields)
CLEANED_COLUMNS = [
    'first_name',
    'last_name',
    'name',
    'title',
    'linkedin_url',
    'org_name',
    'org_website_url',
    'org_linkedin_url',
    'org_primary_domain'
]

# US States for segmentation
US_STATES = [
    "Alabama", "Alaska", "Arizona", "Arkansas", "California",
    "Colorado", "Connecticut", "Delaware", "Florida", "Georgia",
    "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa",
    "Kansas", "Kentucky", "Louisiana", "Maine", "Maryland",
    "Massachusetts", "Michigan", "Minnesota", "Mississippi", "Missouri",
    "Montana", "Nebraska", "Nevada", "New Hampshire", "New Jersey",
    "New Mexico", "New York", "North Carolina", "North Dakota", "Ohio",
    "Oklahoma", "Oregon", "Pennsylvania", "Rhode Island", "South Carolina",
    "South Dakota", "Tennessee", "Texas", "Utah", "Vermont",
    "Virginia", "Washington", "West Virginia", "Wisconsin", "Wyoming",
    "District of Columbia"
]

# Thread-safe file writing
write_lock = threading.Lock()


# ============================================================================
# MAIN SCRAPER CLASS
# ============================================================================

class ApolloScraper:
    """Apollo URL scraper with automatic segmentation and multi-threading"""
    
    def __init__(self):
        self.validate_config()
        self.request_count = 0
        self.start_time = time.time()
        self.lock = threading.Lock()
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
    def validate_config(self):
        """Validate required environment variables"""
        if not APOLLO_API_KEY:
            print("\n❌ ERROR: APOLLO_API_KEY environment variable is required")
            print("\nPlease set it using:")
            print("  export APOLLO_API_KEY='your_key_here'\n")
            sys.exit(1)
    
    # ========================================================================
    # URL PARSING
    # ========================================================================
    
    def parse_apollo_url(self, url: str) -> Dict:
        """Parse Apollo URL to extract filter parameters from hash fragment"""
        print("\n" + "="*80)
        print("PARSING APOLLO URL")
        print("="*80)
        
        # Apollo uses hash fragments, extract the part after #/people?
        if '#/people?' not in url:
            raise ValueError("Invalid Apollo URL format. Expected: https://app.apollo.io/#/people?...")
        
        query_string = url.split('#/people?')[1].split('&page=')[0]  # Remove page parameter
        
        # Initialize filters
        filters = {
            'person_titles': [],
            'person_locations': [],
            'person_not_locations': [],
            'organization_num_employees_ranges': [],
            'organization_industry_tag_ids': [],
            'organization_not_industry_tag_ids': [],
            'q_organization_keyword_tags': [],
            'not_contact_label_ids': [],
            'prospected_by_current_team': [],
            'market_segments': [],
            'included_organization_keyword_fields': []
        }
        
        # Parse query parameters
        for param_pair in query_string.split('&'):
            if '=' not in param_pair:
                continue
                
            key, value = param_pair.split('=', 1)
            value = unquote(value)
            
            # Map URL parameters to API parameters
            if key == 'personTitles[]':
                filters['person_titles'].append(value)
            elif key == 'personLocations[]':
                filters['person_locations'].append(value)
            elif key == 'personNotLocations[]':
                filters['person_not_locations'].append(value)
            elif key == 'organizationNumEmployeesRanges[]':
                filters['organization_num_employees_ranges'].append(value)
            elif key == 'organizationIndustryTagIds[]':
                filters['organization_industry_tag_ids'].append(value)
            elif key == 'organizationNotIndustryTagIds[]':
                filters['organization_not_industry_tag_ids'].append(value)
            elif key == 'qOrganizationKeywordTags[]':
                filters['q_organization_keyword_tags'].append(value)
            elif key == 'notContactLabelIds[]':
                filters['not_contact_label_ids'].append(value)
            elif key == 'prospectedByCurrentTeam[]':
                filters['prospected_by_current_team'].append(value)
            elif key == 'marketSegments[]':
                filters['market_segments'].append(value)
            elif key == 'includedOrganizationKeywordFields[]':
                filters['included_organization_keyword_fields'].append(value)
            elif key == 'includeSimilarTitles':
                filters['include_similar_titles'] = value.lower() == 'true'
        
        # Print summary (without API key)
        print(f"\nExtracted Filters:")
        print(f"  • Person Titles: {len(filters['person_titles'])} titles")
        print(f"  • Person Locations: {filters['person_locations'] or 'None'}")
        print(f"  • Person NOT Locations: {filters['person_not_locations'] or 'None'}")
        print(f"  • Employee Ranges: {filters['organization_num_employees_ranges'] or 'None'}")
        print(f"  • Industry Tags: {len(filters['organization_industry_tag_ids'])} included, {len(filters['organization_not_industry_tag_ids'])} excluded")
        print(f"  • Keyword Tags: {filters['q_organization_keyword_tags'] or 'None'}")
        print(f"  • Market Segments: {filters['market_segments'] or 'None'}")
        
        return filters
    
    # ========================================================================
    # API INTERACTION
    # ========================================================================
    
    def build_api_params(self, filters: Dict, employee_range: Optional[str] = None, 
                        state: Optional[str] = None) -> Dict:
        """Build Apollo API request parameters from parsed filters"""
        params = {
            "api_key": APOLLO_API_KEY,
            "per_page": RECORDS_PER_PAGE,
        }
        
        # Add filters (only include non-empty arrays)
        if filters.get('person_titles'):
            params['person_titles'] = filters['person_titles']
        
        # Handle state override for segmentation
        if state:
            params['person_locations'] = [state]
        elif filters.get('person_locations'):
            params['person_locations'] = filters['person_locations']
            
        if filters.get('person_not_locations'):
            params['person_not_locations'] = filters['person_not_locations']
        
        # Employee range - use override if provided
        if employee_range:
            params['organization_num_employees_ranges'] = [employee_range]
        elif filters.get('organization_num_employees_ranges'):
            params['organization_num_employees_ranges'] = filters['organization_num_employees_ranges']
        
        if filters.get('organization_industry_tag_ids'):
            params['organization_industry_tag_ids'] = filters['organization_industry_tag_ids']
            
        if filters.get('organization_not_industry_tag_ids'):
            params['organization_not_industry_tag_ids'] = filters['organization_not_industry_tag_ids']
        
        if filters.get('q_organization_keyword_tags'):
            params['q_organization_keyword_tags'] = filters['q_organization_keyword_tags']
            
        if filters.get('included_organization_keyword_fields'):
            params['included_organization_keyword_fields'] = filters['included_organization_keyword_fields']
        
        if filters.get('not_contact_label_ids'):
            params['not_contact_label_ids'] = filters['not_contact_label_ids']
        
        if filters.get('prospected_by_current_team'):
            params['prospected_by_current_team'] = filters['prospected_by_current_team']
            
        if filters.get('market_segments'):
            params['market_segments'] = filters['market_segments']
            
        if 'include_similar_titles' in filters:
            params['include_similar_titles'] = filters['include_similar_titles']
        
        return params
    
    def check_total_results(self, params: Dict) -> int:
        """Make a test request to check total results"""
        test_params = params.copy()
        test_params["page"] = 1
        
        try:
            response = requests.post(APOLLO_API_URL, headers={"Content-Type": "application/json"}, json=test_params)
            response.raise_for_status()
            data = response.json()
            
            with self.lock:
                self.request_count += 1
            
            pagination = data.get("pagination", {})
            total_results = pagination.get("total_entries", 0)
            
            return total_results
        except Exception as e:
            print(f"❌ Error checking results: {e}")
            return 0
    
    # ========================================================================
    # SEGMENTATION LOGIC
    # ========================================================================
    
    def create_segmentation_plan(self, filters: Dict) -> List[Dict]:
        """Create a segmentation plan to keep all searches under 50,000 results"""
        print("\n" + "="*80)
        print("ANALYZING SEARCH SIZE")
        print("="*80)
        
        # First, check the total without any segmentation
        params = self.build_api_params(filters)
        total_results = self.check_total_results(params)
        
        print(f"\nTotal results found: {total_results:,}")
        
        if total_results <= MAX_RESULTS_PER_SEARCH:
            print(f"✅ Under {MAX_RESULTS_PER_SEARCH:,} limit - no segmentation needed")
            return [{
                'filters': filters,
                'employee_range': None,
                'state': None,
                'estimated_results': total_results,
                'filename': f"apollo_{self.timestamp}.csv"
            }]
        
        print(f"\n⚠️  Exceeds {MAX_RESULTS_PER_SEARCH:,} limit - will segment the search")
        
        segments = []
        employee_ranges = filters.get('organization_num_employees_ranges', [])
        
        # Step 1: Try breaking by employee ranges
        if employee_ranges:
            print(f"\n📊 Breaking by {len(employee_ranges)} employee ranges...")
            
            for emp_range in employee_ranges:
                params = self.build_api_params(filters, employee_range=emp_range)
                emp_results = self.check_total_results(params)
                
                print(f"  • {emp_range}: {emp_results:,} results")
                
                if emp_results <= MAX_RESULTS_PER_SEARCH:
                    # This range is fine as-is
                    segments.append({
                        'filters': filters,
                        'employee_range': emp_range,
                        'state': None,
                        'estimated_results': emp_results,
                        'filename': f"apollo_{self.timestamp}_emp_{emp_range.replace(',', '-')}.csv"
                    })
                else:
                    # This range needs state segmentation
                    print(f"    ↳ Still too large, breaking by {len(US_STATES)} states...")
                    
                    for state in US_STATES:
                        params = self.build_api_params(filters, employee_range=emp_range, state=state)
                        state_results = self.check_total_results(params)
                        
                        if state_results > 0:  # Only include states with results
                            segments.append({
                                'filters': filters,
                                'employee_range': emp_range,
                                'state': state,
                                'estimated_results': state_results,
                                'filename': f"apollo_{self.timestamp}_emp_{emp_range.replace(',', '-')}_{state.replace(' ', '_')}.csv"
                            })
                        
                        time.sleep(0.1)  # Small delay between checks
        else:
            # No employee ranges, go straight to state segmentation
            print(f"\n📊 Breaking by {len(US_STATES)} states...")
            
            for state in US_STATES:
                params = self.build_api_params(filters, state=state)
                state_results = self.check_total_results(params)
                
                if state_results > 0:
                    print(f"  • {state}: {state_results:,} results")
                    segments.append({
                        'filters': filters,
                        'employee_range': None,
                        'state': state,
                        'estimated_results': state_results,
                        'filename': f"apollo_{self.timestamp}_{state.replace(' ', '_')}.csv"
                    })
                
                time.sleep(0.1)
        
        return segments
    
    # ========================================================================
    # DATA EXTRACTION
    # ========================================================================
    
    def extract_contact_data(self, person: Dict) -> Dict:
        """Extract and flatten contact data from Apollo API response"""
        org = person.get("organization", {}) or {}
        account = person.get("account", {}) or {}
        
        contact = {
            "apollo_id": person.get("id"),
            "first_name": person.get("first_name"),
            "last_name": person.get("last_name"),
            "name": person.get("name"),
            "title": person.get("title"),
            "headline": person.get("headline"),
            "seniority": person.get("seniority"),
            
            # Contact info
            "email": person.get("email"),
            "email_status": person.get("email_status"),
            "linkedin_url": person.get("linkedin_url"),
            "photo_url": person.get("photo_url"),
            "twitter_url": person.get("twitter_url"),
            "github_url": person.get("github_url"),
            "facebook_url": person.get("facebook_url"),
            
            # Location
            "city": person.get("city"),
            "state": person.get("state"),
            "country": person.get("country"),
            "postal_code": person.get("postal_code"),
            "street_address": person.get("street_address"),
            "formatted_address": person.get("formatted_address"),
            "time_zone": person.get("time_zone"),
            
            # Organization IDs
            "organization_id": person.get("organization_id"),
            "account_id": person.get("account_id"),
            
            # Job categories (as JSON strings)
            "departments": json.dumps(person.get("departments", [])) if person.get("departments") else None,
            "subdepartments": json.dumps(person.get("subdepartments", [])) if person.get("subdepartments") else None,
            "functions": json.dumps(person.get("functions", [])) if person.get("functions") else None,
            "employment_history": json.dumps(person.get("employment_history", [])) if person.get("employment_history") else None,
            
            # Organization details
            "org_name": org.get("name"),
            "org_website_url": org.get("website_url"),
            "org_linkedin_url": org.get("linkedin_url"),
            "org_primary_domain": org.get("primary_domain"),
            "org_logo_url": org.get("logo_url"),
            "org_founded_year": org.get("founded_year"),
            "org_linkedin_uid": org.get("linkedin_uid"),
            "org_headcount_6mo_growth": org.get("organization_headcount_six_month_growth"),
            "org_headcount_12mo_growth": org.get("organization_headcount_twelve_month_growth"),
            "org_headcount_24mo_growth": org.get("organization_headcount_twenty_four_month_growth"),
            
            # Account details
            "account_domain": account.get("domain"),
            "account_city": account.get("city"),
            "account_state": account.get("state"),
            "account_country": account.get("country"),
            "account_hubspot_id": account.get("hubspot_id"),
            "account_salesforce_id": account.get("salesforce_id"),
            
            # Metadata
            "email_domain_catchall": person.get("email_domain_catchall"),
            "revealed_for_current_team": person.get("revealed_for_current_team"),
            "extrapolated_email_confidence": person.get("extrapolated_email_confidence"),
            "intent_strength": person.get("intent_strength"),
            "show_intent": person.get("show_intent"),
            
            # Full JSON dumps for reference
            "organization_json": json.dumps(org) if org else None,
            "account_json": json.dumps(account) if account else None,
        }
        
        return contact
    
    def save_to_csv_threadsafe(self, contacts: List[Dict], filename: str):
        """Thread-safe CSV writing - saves both complete and cleaned files"""
        if not contacts:
            return
        
        with write_lock:
            # Save complete file
            file_exists = os.path.isfile(filename)
            try:
                with open(filename, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=contacts[0].keys())
                    if not file_exists:
                        writer.writeheader()
                    writer.writerows(contacts)
            except Exception as e:
                print(f"⚠️  CSV write error (complete): {e}")
            
            # Save cleaned file (subset of columns)
            cleaned_filename = filename.replace('.csv', '_cleaned.csv')
            cleaned_file_exists = os.path.isfile(cleaned_filename)
            try:
                # Extract only the cleaned columns from each contact
                cleaned_contacts = []
                for contact in contacts:
                    cleaned_contact = {col: contact.get(col) for col in CLEANED_COLUMNS}
                    cleaned_contacts.append(cleaned_contact)
                
                with open(cleaned_filename, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=CLEANED_COLUMNS)
                    if not cleaned_file_exists:
                        writer.writeheader()
                    writer.writerows(cleaned_contacts)
            except Exception as e:
                print(f"⚠️  CSV write error (cleaned): {e}")
    
    def extract_segment(self, segment: Dict) -> Tuple[str, int]:
        """Extract contacts for a single segment (multi-threading safe)"""
        filename = segment['filename']
        filters = segment['filters']
        employee_range = segment['employee_range']
        state = segment['state']
        
        # Build params
        params = self.build_api_params(filters, employee_range, state)
        
        # Get total results
        params["page"] = 1
        try:
            response = requests.post(APOLLO_API_URL, headers={"Content-Type": "application/json"}, json=params)
            response.raise_for_status()
            data = response.json()
            
            with self.lock:
                self.request_count += 1
            
            total_results = data.get("pagination", {}).get("total_entries", 0)
            total_results = min(total_results, MAX_RESULTS_PER_SEARCH)
            total_pages = min((total_results + RECORDS_PER_PAGE - 1) // RECORDS_PER_PAGE, MAX_PAGES_PER_SEARCH)
            
            # Check if already complete (check both files)
            cleaned_filename = filename.replace('.csv', '_cleaned.csv')
            if os.path.exists(filename) and os.path.exists(cleaned_filename):
                with open(filename, 'r') as f:
                    existing_count = sum(1 for _ in f) - 1  # Subtract header
                if existing_count >= total_results - 100:  # Allow small margin
                    print(f"  ✅ {filename}: Already complete ({existing_count:,} contacts)")
                    return (filename, cleaned_filename, existing_count)
            
            print(f"  🚀 Starting: {filename} ({total_results:,} results, {total_pages} pages)")
            
            # Extract all pages
            all_contacts = []
            batch_size = 50
            
            for page in range(1, total_pages + 1):
                params["page"] = page
                
                try:
                    response = requests.post(APOLLO_API_URL, headers={"Content-Type": "application/json"}, json=params)
                    response.raise_for_status()
                    data = response.json()
                    
                    with self.lock:
                        self.request_count += 1
                    
                    people = data.get("people", [])
                    for person in people:
                        contact = self.extract_contact_data(person)
                        all_contacts.append(contact)
                    
                    # Save in batches
                    if len(all_contacts) >= batch_size * RECORDS_PER_PAGE:
                        self.save_to_csv_threadsafe(all_contacts, filename)
                        all_contacts = []
                    
                    # Rate limiting
                    time.sleep(REQUEST_DELAY)
                    
                except Exception as e:
                    print(f"  ❌ {filename} page {page}: {e}")
                    time.sleep(1)
                    continue
            
            # Save remaining
            if all_contacts:
                self.save_to_csv_threadsafe(all_contacts, filename)
            
            # Get final count
            final_count = 0
            if os.path.exists(filename):
                with open(filename, 'r') as f:
                    final_count = sum(1 for _ in f) - 1
            
            print(f"  ✅ Complete: {filename} ({final_count:,} contacts)")
            return (filename, cleaned_filename, final_count)
            
        except Exception as e:
            print(f"  ❌ Failed: {filename} - {e}")
            cleaned_filename = filename.replace('.csv', '_cleaned.csv')
            return (filename, cleaned_filename, 0)
    
    # ========================================================================
    # MAIN EXECUTION
    # ========================================================================
    
    def run(self, url: str):
        """Main execution flow"""
        print("\n" + "="*80)
        print("APOLLO URL SCRAPER - SIMPLE & FAST")
        print("="*80)
        print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        # Parse URL
        filters = self.parse_apollo_url(url)
        
        # Create segmentation plan
        segments = self.create_segmentation_plan(filters)
        
        # Display plan
        print("\n" + "="*80)
        print("SEGMENTATION PLAN")
        print("="*80)
        total_estimated = sum(s['estimated_results'] for s in segments)
        print(f"\nTotal segments: {len(segments)}")
        print(f"Estimated total contacts: {total_estimated:,}")
        print(f"\nFiles to be created:")
        for seg in segments[:10]:  # Show first 10
            info = []
            if seg['employee_range']:
                info.append(f"Employees: {seg['employee_range']}")
            if seg['state']:
                info.append(f"State: {seg['state']}")
            info_str = " | ".join(info) if info else "All results"
            print(f"  • {seg['filename']}")
            print(f"    {info_str} - ~{seg['estimated_results']:,} contacts")
        
        if len(segments) > 10:
            print(f"  ... and {len(segments) - 10} more files")
        
        # Confirm
        print("\n" + "="*80)
        response = input("Continue with extraction? (y/n): ").strip().lower()
        if response != 'y':
            print("\n❌ Extraction cancelled by user")
            return
        
        # Execute extraction with multi-threading
        print("\n" + "="*80)
        print("EXTRACTING CONTACTS")
        print("="*80)
        print(f"Workers: {NUM_WORKERS}")
        print()
        
        results = []
        with ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
            futures = {
                executor.submit(self.extract_segment, segment): segment
                for segment in segments
            }
            
            for future in as_completed(futures):
                try:
                    filename, cleaned_filename, count = future.result()
                    results.append((filename, cleaned_filename, count))
                except Exception as e:
                    print(f"❌ Segment failed: {e}")
        
        # Final summary
        elapsed = time.time() - self.start_time
        total_contacts = sum(r[2] for r in results)  # r[2] is count (third element)
        
        print("\n" + "="*80)
        print("EXTRACTION COMPLETE!")
        print("="*80)
        print(f"Total segments: {len(results)}")
        print(f"Total contacts extracted: {total_contacts:,}")
        print(f"Total API requests: {self.request_count:,}")
        print(f"Total time: {elapsed/60:.1f} minutes")
        print(f"Speed: {self.request_count/elapsed:.1f} requests/sec")
        print(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        print("\n📁 Files created:")
        for filename, cleaned_filename, count in sorted(results, key=lambda x: x[2], reverse=True):
            print(f"  • {filename}: {count:,} contacts (complete)")
            print(f"    {cleaned_filename}: {count:,} contacts (cleaned)")
        
        # Save summary
        summary = {
            'extraction_date': datetime.now().isoformat(),
            'total_segments': len(results),
            'total_contacts': total_contacts,
            'total_requests': self.request_count,
            'elapsed_seconds': elapsed,
            'files': [
                {
                    'filename_complete': f, 
                    'filename_cleaned': c_f,
                    'count': c
                } 
                for f, c_f, c in results
            ]
        }
        
        summary_file = f"apollo_{self.timestamp}_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\n📊 Summary saved to: {summary_file}")
        print("\n✅ All done!\n")


# ============================================================================
# INTERACTIVE CLI
# ============================================================================

def main():
    """Interactive CLI for Apollo scraper"""
    print("\n" + "="*80)
    print("APOLLO URL SCRAPER")
    print("="*80)
    print("\nThis tool will extract contacts from an Apollo search URL.")
    print("It automatically segments large lists to stay under Apollo's 50k limit.")
    print()
    
    # Get URL from user
    url = input("Enter Apollo search URL: ").strip()
    
    if not url:
        print("\n❌ No URL provided. Exiting.")
        return
    
    # Create scraper and run
    try:
        scraper = ApolloScraper()
        scraper.run(url)
    except KeyboardInterrupt:
        print("\n\n❌ Interrupted by user. Exiting.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

