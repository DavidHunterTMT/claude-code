{
    'name': 'Payroll Summary (QuickBooks Style)',
    'version': '19.0.1.0.0',
    'category': 'Human Resources/Payroll',
    'summary': 'Payroll summary by employee for any date range, laid out like the QuickBooks Payroll Summary',
    'description': """
Payroll Summary by Employee
===========================
Adds *Payroll > Reporting > Payroll Summary*. Pick a date range and get one
column per employee (plus a TOTAL column) and one row per payslip line,
grouped the same way as the QuickBooks Desktop "Payroll Summary" report:

* Gross Pay
* Deductions from Gross Pay (pre-tax)
* Adjusted Gross Pay
* Taxes Withheld
* Deductions from Net Pay (post-tax)
* Additions to Net Pay (reimbursements, mileage, ...)
* Net Pay
* Employer Taxes and Contributions

The report can be viewed on screen, printed to PDF or exported to Excel.
Each salary rule is placed in a section automatically from its category; the
placement can be overridden per rule with the *Payroll Summary Section* field
on the salary rule form.
""",
    'author': 'Tennessee Machine Tool',
    'license': 'LGPL-3',
    'depends': ['hr_payroll'],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_salary_rule_views.xml',
        'wizard/payroll_summary_wizard_views.xml',
        'report/payroll_summary_report.xml',
        'report/payroll_summary_templates.xml',
    ],
    'installable': True,
    'application': False,
}
