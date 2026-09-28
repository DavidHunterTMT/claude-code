from odoo import fields, models

SUMMARY_SECTIONS = [
    ('gross', 'Gross Pay'),
    ('pretax', 'Deductions from Gross Pay'),
    ('tax', 'Taxes Withheld'),
    ('posttax', 'Deductions from Net Pay'),
    ('addition', 'Additions to Net Pay'),
    ('employer', 'Employer Taxes and Contributions'),
    ('other', 'Other (informational only)'),
    ('exclude', 'Do Not Show'),
]

# Rules that are computed totals of other lines. The summary recomputes these
# itself (Total Gross Pay, Net Pay, ...) so the underlying lines are hidden.
TOTAL_RULE_CODES = {'GROSS', 'NET', 'TAXABLE'}
TOTAL_CATEGORY_CODES = {'NET', 'TAXABLE', 'REF'}


class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    payroll_summary_section = fields.Selection(
        SUMMARY_SECTIONS,
        string='Payroll Summary Section',
        help="Where this rule appears on the Payroll Summary report. "
             "Leave empty to place it automatically from the rule category.")

    def _get_payroll_summary_section(self):
        """Return the Payroll Summary section key for this rule."""
        self.ensure_one()
        if self.payroll_summary_section:
            return self.payroll_summary_section
        category_codes = set()
        category = self.category_id
        while category:
            category_codes.add(category.code)
            category = category.parent_id
        return guess_summary_section(self.code, category_codes, self.sequence)


def guess_summary_section(rule_code, category_codes, sequence):
    """Map a salary rule to a summary section from its code and the codes of
    its category and all parent categories."""
    if rule_code in TOTAL_RULE_CODES or category_codes & TOTAL_CATEGORY_CODES:
        return 'exclude'
    if category_codes & {'COMPANYDED', 'COMP', 'MATCHING'}:
        return 'employer'
    if 'TAXES' in category_codes:
        return 'tax'
    if 'PRETAX' in category_codes:
        return 'pretax'
    if category_codes & {'POSTTAX', 'DED'}:
        return 'posttax'
    if category_codes & {'NT-R', 'REIMB'}:
        return 'addition'
    if category_codes & {'BASIC', 'GROSS', 'GROSS_PAY'}:
        return 'gross'
    if 'ALW' in category_codes:
        # Allowances computed before the GROSS rule (sequence 100) are part of
        # gross pay (commission, ...); the ones after it are added to net pay
        # (expense reimbursement, mileage, ...).
        return 'gross' if sequence < 100 else 'addition'
    return 'other'
