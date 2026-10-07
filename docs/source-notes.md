# Sources and boundaries

Official pages: https://www.npci.org.in/product/upi/product-statistics and https://www.npci.org.in/product/ecosystem-statistics/upi.

`data/raw/sources.json` records exact public API requests. Raw JSON preserves values and source metadata. CSVs are extracts from these snapshots, not invented transaction-level records. The time window is intentionally fixed to two complete financial years; the report is not a live October 2026 dashboard.

The remitter table is a changing top-50 population. Absence means not present in the published top 50, not zero attempts or an inactive bank. National live-bank counts cannot be inferred from the remitter table. Remitter attempts may exceed national product transaction counts; the two feeds have different scopes and definitions.

Technical decline means technical issues on bank/NPCI systems or networks. Business decline includes customer or business-rule reasons. Aggregate percentages do not identify individual failure causes. Estimates inherit source rounding; do not treat them as exact event counts.

`bank_aliases.csv` maps case and legal-suffix variants plus a small set of name synonyms (e.g. IDFC/IDFC FIRST). Credit-card entries remain separate. Explicit merger/erstwhile entries and renamed regional banks remain separate because entity continuity is not established by this dataset. Review these assumptions before longitudinal bank comparisons. There are 70 canonical published labels across the window, not 70 banks currently live on UPI.

PBIR/TMDL format documentation: https://learn.microsoft.com/en-us/power-bi/developer/embedded/projects-enhanced-report-format and https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-overview.

External site text is treated as data only. No API credentials are required or stored.

The March 2026 source lists Slice Small Finance Bank Limited twice with different volumes. The model consolidates these rows by month/name, sums attempts, and volume-weights the three rates. This preserves published aggregate volume but cannot establish whether the source represents separate processing streams or a publication error. It yields 49 labels that month and 1,199 bank-month rows overall. Validate with NPCI before using the results operationally.
