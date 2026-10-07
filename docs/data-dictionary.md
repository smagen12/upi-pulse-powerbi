# Data dictionary

| Table | Grain / field | Meaning |
|---|---|---|
| Dim_Date | One day; Date | Unique contiguous date key, full calendar years covering fact months |
| Dim_Date | Year, MonthKey, MonthLabel | Calendar year, sortable YYYYMM, YYYY-MM label |
| Dim_Bank | One canonical source label; Bank | Audited name mapping; credit-card channels and merger-era entries can remain distinct |
| Fact_National | One month; Month | First day of month, FK to Dim_Date |
| Fact_National | Transactions | NPCI product volume in millions × 1,000,000 |
| Fact_National | ValueINR | NPCI product value in crore × 10,000,000 INR |
| Fact_National | BanksLive | NPCI live-bank count, snapshot; never sum across months |
| Fact_Remitter | One month × published bank entry | Covered top-50 remitter scope; missing entries are unknown |
| Fact_Remitter | Month, Bank | FKs to conformed dimensions |
| Fact_Remitter | Attempts | Published remitter volume in millions × 1,000,000 |
| Fact_Remitter | ApprovedRate, BDRate, TDRate | Decimal rates (0–1); weight by Attempts |
| bank_aliases.csv | SourceBank → CanonicalBank | Explicit mapping applied in Power Query; unknown names fail refresh |

Relationships: Dim_Date 1→* Fact_National; Dim_Date 1→* Fact_Remitter; Dim_Bank 1→* Fact_Remitter. All filter in one direction. No geography dimension because no geographic data is loaded. No relationship between the facts.

Python processed CSVs support validation and previews; Power Query refreshes the raw CSV extracts and applies its own cleaning. Fact numeric columns are hidden to encourage explicit measures. MonthLabel sorts by MonthKey.
