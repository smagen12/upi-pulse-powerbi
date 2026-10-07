# Required Desktop acceptance

- [ ] Open PBIP in current Windows Power BI Desktop without load errors.
- [ ] Set DataRoot; refresh all four tables without missing aliases or conversion errors.
- [ ] Check 24 national rows, 1,199 remitter bank-month rows, 70 dimension labels and contiguous date table.
- [ ] Confirm marked date table and three 1:* single-direction relationships.
- [ ] Verify all 17 measures, folders, formats, and date/key metadata.
- [ ] Select March 2026: national transactions 22,641,110,000; value INR 29,525,420,500,000; MoM 11.0175%; YoY 23.7117%.
- [ ] March bank TD: 0.225737%; estimated TD 55,113,056; top-five covered share 50.65696%.
- [ ] For April 2024, MoM/YoY return blank where prior periods are unavailable; rolling average is blank until 3 observed months exist.
- [ ] Multi-month total cards aggregate selections; MoM/YoY cards explicitly describe latest selected month.
- [ ] Bank slicer filters reliability visuals; national totals stay on their separate page.
- [ ] Check chart/table/slicer render, sort order, text sizes, tab order, tooltips, contrast and ₹ formatting. Add conditional color for Growth Status if useful.
- [ ] Replace data previews with actual Desktop/model screenshots; save PBIP and rerun checks.
- [ ] Publish to Service and record actual sharing URL only if tenant permits it.

Linux checks validate source JSON/data and static metadata; they do not evaluate DAX, execute M, deserialize the model with Microsoft TOM, or render Desktop visuals. Do not mark these checks complete without opening Desktop.
