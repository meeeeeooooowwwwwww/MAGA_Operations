# MAGA Ops Data Migration Summary

## Migration Overview

This document summarizes the data migration process for the MAGA Ops database system. The migration involved importing data from various sources into the SQLite database.

## Data Sources

The following data sources were migrated:

1. **Legislators Data (YAML files)**
   - `legislators-current.yaml`: Current legislators with biographical and term information
   - `legislators-social-media.yaml`: Social media accounts for legislators
   - `legislators-district-offices.yaml`: District office locations for legislators

2. **Committee Data (YAML files)**
   - `committees-current.yaml`: Current committees
   - `committees-historical.yaml`: Historical committees
   - `committee-membership-current.yaml`: Current committee memberships

3. **Executive Branch Data (YAML files)**
   - `executive.yaml`: Presidents and Vice Presidents with term information

4. **Influencer Data (JSON files)**
   - `influencers_export_20250428_152510.json`: Influencer profiles
   - `benny_johnson_names_20250428_145348.json`: Names mentioned in Benny Johnson content
   - `benny_johnson_videos_20250428_145348.json`: Benny Johnson video data

5. **War Room Content (JSON files)**
   - `warroom-headings.json`: Headings from War Room content
   - `warroom-scraped-content.json`: Content scraped from War Room

## Migration Scripts

The following scripts were created for the migration process:

1. `scripts/migrate_committees.py`: Imports committee data from YAML files
2. `scripts/migrate_district_offices.py`: Imports district office locations from YAML files
3. `scripts/migrate_executive.py`: Imports executive branch officials from YAML files
4. `scripts/migrate_office_data.py`: Imports office data for politicians
5. `scripts/migrate_election_year.py`: Extracts and imports election year data

## Database Tables Updated

The migration process populated the following tables:

1. `committees`: 75 records
2. `committee_memberships`: 1,327 records
3. `district_offices`: 2,582 records
4. `politicians`: 541 records
5. `influencers`: 112 records
6. `entities`: 653 records
7. `social_posts`: 64 records

## Migration Results

| Script | Total Records | Updated | New | Skipped | Issues |
|--------|---------------|---------|-----|---------|--------|
| migrate_committees.py | N/A | 51 | 0 | N/A | None |
| migrate_district_offices.py | 1,291 | 0 | 1,291 | 0 | None |
| migrate_office_data.py | 12,759 | 541 | 0 | 12,218 | Missing politicians for some bioguide IDs |
| migrate_election_year.py | 12,759 | 541 | 0 | 12,218 | Missing politicians for some bioguide IDs |
| migrate_executive.py | Incomplete | Incomplete | Incomplete | Incomplete | UNIQUE constraint on politicians.entity_id |

## Known Issues and Future Work

1. **Executive Officials Migration**: The migration script for executive officials encountered a UNIQUE constraint error on the politicians.entity_id field. This needs to be fixed by checking if the entity already exists in the politicians table and updating rather than inserting.

2. **Missing Politician Records**: Many bioguide IDs in the YAML files don't have corresponding records in the politicians table. This could be addressed by importing the complete set of legislators or by creating new records for missing legislators.

3. **Committee Memberships**: The committee membership migration would benefit from a more comprehensive approach to handle historical memberships.

4. **Influencer Data**: More work is needed to properly categorize and relate influencers to other entities in the database.

## Recommendations for Future Migrations

1. Always create a database backup before running migration scripts
2. Run migrations on a test database first
3. Focus on one data field at a time with proper verification
4. Implement rollback mechanisms in case of errors
5. Maintain proper logging for all migration activities
6. Verify data integrity after migration by sampling records 