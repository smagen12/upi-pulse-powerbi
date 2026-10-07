# DAX measures

Definitions live in `UPI-Payments.SemanticModel/definition/tables/Fact_National.tmdl` and `Fact_Remitter.tmdl`.

- 'Bank Attempts'
- 'Covered Banks'
- 'Estimated Technical Declines'
- 'Technical Decline Rate %'
- 'Business Decline Rate %'
- 'Approved Rate %'
- 'Top 5 Share %'
- 'Total Transactions'
- 'Total Value INR'
- 'Avg Transaction Value'
- 'Active Months'
- 'Banks Live Latest'
- 'MoM Growth %'
- 'YoY Growth %'
- 'Rolling 3 Month Avg'
- 'Growth Status'
- 'Average Daily Transactions'

MoM and YoY use the latest selected observed month and remove date filters only for baseline lookup. Missing baselines return blank via DIVIDE. Rolling averages require three observed months. Top-five share is relative to selected covered bank labels; rates and counts refer to the same selected remitter population.
