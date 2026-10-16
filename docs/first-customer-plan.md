# CleanSheet: first-customer plan

This plan is for validating demand before investing in accounts, subscriptions, or a larger hosted product.

## First offer: spreadsheet cleanup pilot

**Promise:** Send a non-sensitive CSV or Excel file and receive a cleaned copy plus a short report explaining what changed.

### Initial scope
- Trim accidental spaces around text.
- Standardize column names when requested.
- Identify missing values and duplicate rows.
- Apply agreed missing-value rules.
- Convert selected columns to numeric values when appropriate.
- Return a cleaned CSV/XLSX file and a change report.

### Explicit exclusions
- Do not promise that every dataset can be cleaned automatically.
- Do not make business decisions about what a missing value should mean.
- Do not infer ambiguous dates or silently delete rows.
- Do not accept passwords, payment-card data, government IDs, health records, or confidential customer data during the initial pilot.
- Keep the original file unchanged and ask the customer to verify the result before relying on it.

## How to validate demand

1. Talk to 5–10 people who regularly use spreadsheets for work, school, a club, or a small business.
2. Ask what they currently do when a spreadsheet is messy, how often this happens, and what mistakes or time costs it causes.
3. Ask whether they would try the service on a small, non-sensitive sample file. Do not ask only whether the idea sounds good.
4. Complete one small pilot manually with the customer’s agreement. Explain every change and let them approve the output.
5. Ask what was useful, what was missing, and whether they would pay for the next file. Record actual behaviour, not just compliments.
6. Only after several people have the same problem, prioritize software features for that workflow.

## Pricing experiment

Do not commit to a permanent price before seeing real jobs. For each pilot, estimate the time required, agree on the exact scope in advance, and test a modest fixed fee with willing customers. Record the quoted price, time spent, revisions requested, and whether the customer would use the service again.

Avoid promising free ongoing work. A small demonstration can be free; the deliverable and scope for paid work should be clear before starting.

## Data-handling checklist

- Ask customers to use a copy of their file and remove sensitive fields.
- Never ask for account passwords or credentials.
- Do not upload customer data to a public demo or third-party service without explicit informed permission.
- Keep customer files only as long as needed to complete the agreed job, then delete working copies.
- Do not claim that the service is secure or compliant with a particular regulation unless that has been properly assessed.
- For public software hosting, document where files are processed, whether anything is retained, and how users can get their data deleted before accepting real customer data.

## When to build more

Prioritize a new feature only when it solves a problem observed in real files or repeatedly requested by prospective customers. First aim for a few successful, well-documented pilot jobs; then decide whether the strongest opportunity is a service, self-service software, or both.
