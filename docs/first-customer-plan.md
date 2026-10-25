# CleanSheet: first-customer plan

This plan is for validating demand before investing in accounts, subscriptions, or a larger hosted product.

## First offer: spreadsheet cleanup pilot

**Promise:** Use CleanSheet to clean a non-sensitive CSV or Excel file and receive a cleaned copy plus a short report explaining what changed.

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
- Keep the original file unchanged and ask the user to verify the output before relying on it.

## How to validate demand

1. Talk to 5–10 people who regularly use spreadsheets for work, school, a club, or a small business.
2. Ask what they currently do when a spreadsheet is messy, how often this happens, and what mistakes or time costs it causes.
3. Ask whether they would try the app on a small, non-sensitive sample file. Do not ask only whether the idea sounds good.
4. Observe whether they can complete the workflow without help.
5. Ask what was useful, what was missing, and whether they would pay for continued use. Record actual behaviour, not just compliments.
6. Only after several people have the same problem, prioritize software features for that workflow.

## Pricing experiment

Do not commit to a permanent price before seeing real use. Test a modest, clearly explained offer with willing users. Record the quoted price, use frequency, errors, and whether users return.

Avoid promising free ongoing access. Make the scope and any payment terms clear before charging.

## Data-handling checklist

- Ask users to use a copy of their file and remove sensitive fields.
- Never ask for account passwords or credentials.
- Do not upload user data to a public demo or third-party service without explicit informed permission.
- The web app currently limits uploads to 10 MB, 100,000 rows, 500 columns, and 2,000,000 populated cells.
- Formula-like text is prefixed in exported spreadsheet files to reduce formula-injection risk; this can change those text values, so users must inspect important exports.
- The Clear session data control clears app-owned result state and resets the upload widget, but it is not a guarantee that every copy disappears immediately from hosting infrastructure or runtime memory.
- Do not claim that the service is secure or compliant with a particular regulation unless that has been properly assessed.
- For hosted software, document where files are processed, whether anything is retained, and how users can request deletion before accepting real customer data.
- Before taking payment for app access, verify the hosting provider's commercial-use terms and implement proper authentication, payment verification, and access control. A public URL is not a paywall.

## When to build more

Prioritize a feature only when it solves a problem observed during real testing or repeatedly requested by prospective users. First aim for a few successful test sessions; then decide what is necessary for a self-service product.
