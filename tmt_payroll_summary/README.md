# Payroll Summary (QuickBooks Style) — Odoo 19

Recreates the QuickBooks Desktop **Payroll Summary** report in Odoo Payroll:
one column per employee plus a **TOTAL** column, one row per payslip line,
for any date range you choose.

## Using it

**Payroll → Reporting → Payroll Summary**

| Field | Meaning |
|---|---|
| From / To | The date range to report on |
| Filter Payslips By | Which payslip date must fall in the range: *Pay Period End Date* (default), *Pay Period Start Date* or *Payment Date* |
| Include Validated (Unpaid) Payslips | Also count payslips that are validated but not yet marked paid. Draft and cancelled payslips are never counted |
| Employees / Departments | Optional filters. Leave them empty to include everyone |
| Hide Lines That Are Zero For Everyone | Drops rows such as *Medicare Additional Tax* when nobody has an amount |
| Employees per PDF Page | The PDF spreads the employee columns over several pages. The TOTAL column prints on the last page |

Buttons: **View** (on screen), **Print PDF**, **Export to Excel** (all
employees on one sheet, frozen headers, like the QuickBooks export).

## Layout

```
Employee Wages, Taxes and Adjustments
    Gross Pay                    Basic Salary, Commission, Bonus Pay …
    Total Gross Pay
    Deductions from Gross Pay    Simple IRA - Employee, BCBS …, AFLAC
    Total Deductions from Gross Pay
  Adjusted Gross Pay
  Taxes Withheld                 Federal Income Tax, Social Security, Medicare …
  Total Taxes Withheld
  Deductions from Net Pay        (post-tax deductions, shown only if there are any)
  Additions to Net Pay           Expenses Reimbursement, Mileage Benefit …
  Total Additions to Net Pay
Net Pay
Employer Taxes and Contributions  Simple IRA - Employer, FUTA, SUI, SS/Medicare Employer
Total Employer Taxes and Contributions
```

Net Pay is recomputed from the sections, so it ties out to each payslip's
*Net Salary* line. Amounts keep Odoo's signs: deductions and taxes negative,
employer costs positive, the same as QuickBooks.

## How lines are placed

Each salary rule goes into a section based on its category:

| Category (or a parent category) | Section |
|---|---|
| BASIC, GROSS | Gross Pay |
| ALW, computed before the Gross rule (sequence < 100) | Gross Pay |
| ALW, computed after it (sequence ≥ 100), NT-R, REIMB | Additions to Net Pay |
| PRETAX | Deductions from Gross Pay |
| TAXES | Taxes Withheld |
| POSTTAX / other DED | Deductions from Net Pay |
| COMPANYDED, COMP, MATCHING | Employer Taxes and Contributions |
| Rules GROSS, NET, TAXABLE and categories NET, TAXABLE, REF | Hidden (they are totals) |

To change where a rule appears, open it (**Payroll → Configuration → Rules**)
and set **Payroll Summary Section**. Rules with the same name in different
salary structures share one row.

## Installation

This is a custom addon, so it has to be installed where your custom modules
live (Odoo.sh or your own server; Odoo Online can't install it):

1. Copy the `tmt_payroll_summary` folder into your addons path (on Odoo.sh,
   commit it to the repository branch).
2. Update the Apps list and install **Payroll Summary (QuickBooks Style)**.

Depends only on `hr_payroll`. Users in the *Payroll / Officer* group or above
can run the report.
