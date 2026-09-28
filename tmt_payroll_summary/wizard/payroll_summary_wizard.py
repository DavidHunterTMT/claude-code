import base64
import io
from collections import defaultdict

import xlsxwriter

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import format_date

DATE_BASIS = [
    ('date_to', 'Pay Period End Date'),
    ('date_from', 'Pay Period Start Date'),
    ('paid_date', 'Payment Date'),
]


def build_summary_rows(employees, rules, amounts, hide_zero_lines=False):
    """Build the QuickBooks style Payroll Summary rows.

    :param employees: list of (employee_id, employee_name), in column order
    :param rules: list of (row_key, label, section, sequence)
    :param amounts: dict {(employee_id, row_key): amount}
    :return: list of row dicts {type, label, level, values, total} where
             type is 'title', 'line', 'subtotal' or 'blank' and values is a
             list of amounts in the same order as employees.
    """
    employee_ids = [emp_id for emp_id, _name in employees]
    rows = []

    def zero():
        return [0.0] * len(employee_ids)

    def add(row_type, label, level, values=None):
        rows.append({
            'type': row_type,
            'label': label,
            'level': level,
            'values': values,
            'total': sum(values) if values is not None else None,
        })

    section_lines = defaultdict(list)
    for key, label, section, _sequence in sorted(rules, key=lambda r: (r[3], r[1])):
        values = [amounts.get((emp_id, key), 0.0) for emp_id in employee_ids]
        if hide_zero_lines and not any(round(v, 2) for v in values):
            continue
        section_lines[section].append((label, values))

    def section(label, key, level, title_type='title', always=True):
        """Add a section title, its lines and its total. Returns the totals."""
        lines = section_lines.get(key, [])
        totals = zero()
        if not lines and not always:
            return totals
        add(title_type, label, level)
        for line_label, values in lines:
            add('line', line_label, level + 1, values)
            totals = [a + b for a, b in zip(totals, values)]
        add('subtotal', _('Total %s', label), level, totals)
        return totals

    add('title', _('Employee Wages, Taxes and Adjustments'), 0)
    gross = section(_('Gross Pay'), 'gross', 2)
    pretax = section(_('Deductions from Gross Pay'), 'pretax', 2)
    adjusted = [a + b for a, b in zip(gross, pretax)]
    add('subtotal', _('Adjusted Gross Pay'), 1, adjusted)
    taxes = section(_('Taxes Withheld'), 'tax', 1)
    posttax = section(_('Deductions from Net Pay'), 'posttax', 1, always=False)
    additions = section(_('Additions to Net Pay'), 'addition', 1)
    net = [a + b + c + d for a, b, c, d in zip(adjusted, taxes, posttax, additions)]
    add('subtotal', _('Net Pay'), 0, net)
    add('blank', '', 0)
    section(_('Employer Taxes and Contributions'), 'employer', 0)
    if section_lines.get('other'):
        add('blank', '', 0)
        section(_('Other Payslip Lines (not included in Net Pay)'), 'other', 0)
    return rows


class PayrollSummaryWizard(models.TransientModel):
    _name = 'tmt.payroll.summary.wizard'
    _description = 'Payroll Summary by Employee'

    @api.model
    def _default_date_from(self):
        return fields.Date.context_today(self).replace(month=1, day=1)

    company_id = fields.Many2one(
        'res.company', required=True, default=lambda self: self.env.company)
    date_from = fields.Date('From', required=True, default=_default_date_from)
    date_to = fields.Date('To', required=True, default=fields.Date.context_today)
    date_basis = fields.Selection(
        DATE_BASIS, string='Filter Payslips By', required=True, default='date_to',
        help="Which payslip date must fall inside the selected range.\n"
             "Payment Date only includes payslips that have been marked as paid.")
    include_unpaid = fields.Boolean(
        'Include Validated (Unpaid) Payslips', default=True,
        help="Also include payslips that are validated but not yet marked as paid. "
             "Draft and cancelled payslips are never included.")
    employee_ids = fields.Many2many(
        'hr.employee', string='Employees',
        help="Leave empty to include every employee paid in the period.")
    department_ids = fields.Many2many(
        'hr.department', string='Departments',
        help="Leave empty to include all departments.")
    hide_zero_lines = fields.Boolean(
        'Hide Lines That Are Zero For Everyone', default=False)
    employees_per_page = fields.Integer(
        'Employees per PDF Page', default=8,
        help="The PDF splits the employee columns over several pages. "
             "The TOTAL column is printed on the last page.")
    xlsx_file = fields.Binary('Excel File', readonly=True, attachment=False)
    xlsx_filename = fields.Char(readonly=True)

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for wizard in self:
            if wizard.date_from > wizard.date_to:
                raise UserError(_("The start date must be before the end date."))

    # ------------------------------------------------------------------
    # Data
    # ------------------------------------------------------------------

    def _get_payslip_domain(self):
        self.ensure_one()
        states = ['paid']
        if self.include_unpaid and self.date_basis != 'paid_date':
            states.append('validated')
        domain = [
            ('state', 'in', states),
            ('company_id', '=', self.company_id.id),
            (self.date_basis, '>=', self.date_from),
            (self.date_basis, '<=', self.date_to),
        ]
        if self.employee_ids:
            domain.append(('employee_id', 'in', self.employee_ids.ids))
        if self.department_ids:
            domain.append(('department_id', 'child_of', self.department_ids.ids))
        return domain

    def _get_report_data(self):
        """Return everything the PDF / HTML / Excel renderers need."""
        self.ensure_one()
        payslips = self.env['hr.payslip'].search(self._get_payslip_domain())
        groups = self.env['hr.payslip.line']._read_group(
            [('slip_id', 'in', payslips.ids)],
            groupby=['employee_id', 'salary_rule_id'],
            aggregates=['total:sum'],
        )

        employees = self.env['hr.employee']
        rule_rows = {}   # row key -> (label, section, sequence)
        amounts = defaultdict(float)
        for employee, rule, total in groups:
            if not employee or not rule:
                continue
            section = rule._get_payroll_summary_section()
            if section == 'exclude':
                continue
            # Rules with the same name (e.g. the same tax in two salary
            # structures) are merged on one row, like QuickBooks payroll items.
            key = (section, rule.name)
            label, _section, sequence = rule_rows.get(key, (rule.name, section, rule.sequence))
            rule_rows[key] = (label, section, min(sequence, rule.sequence))
            employees |= employee
            amounts[(employee.id, key)] += total

        employees = employees.sorted(lambda e: (e.name or '').lower())
        employee_list = [(e.id, e.name) for e in employees]
        rules = [(key, label, section, seq) for key, (label, section, seq) in rule_rows.items()]
        rows = build_summary_rows(employee_list, rules, amounts, self.hide_zero_lines)

        per_page = max(self.employees_per_page, 1)
        column_pages = []
        indexes = list(range(len(employee_list)))
        for start in range(0, len(indexes), per_page):
            column_pages.append(indexes[start:start + per_page])
        if not column_pages:
            column_pages = [[]]

        return {
            'employees': [name for _id, name in employee_list],
            'rows': rows,
            'column_pages': column_pages,
            'payslip_count': len(payslips),
            'date_basis_label': dict(DATE_BASIS)[self.date_basis],
        }

    @api.model
    def _format_amount(self, value):
        if value is None:
            return ''
        value = round(value, 2) or 0.0  # avoid "-0.00"
        return '{:,.2f}'.format(value)

    def _get_title(self):
        self.ensure_one()
        return _('Payroll Summary')

    def _get_period_label(self):
        self.ensure_one()
        return _('%(start)s through %(end)s',
                 start=format_date(self.env, self.date_from),
                 end=format_date(self.env, self.date_to))

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _check_has_data(self, data):
        if not data['employees']:
            raise UserError(_("No payslips were found for the selected period and filters."))

    def action_view(self):
        self.ensure_one()
        self._check_has_data(self._get_report_data())
        action = self.env.ref('tmt_payroll_summary.action_report_payroll_summary').report_action(self)
        action['report_type'] = 'qweb-html'
        return action

    def action_print_pdf(self):
        self.ensure_one()
        self._check_has_data(self._get_report_data())
        return self.env.ref('tmt_payroll_summary.action_report_payroll_summary').report_action(self)

    def action_export_xlsx(self):
        self.ensure_one()
        data = self._get_report_data()
        self._check_has_data(data)
        self.write({
            'xlsx_file': base64.b64encode(self._render_xlsx(data)),
            'xlsx_filename': 'Payroll Summary %s - %s.xlsx' % (
                self.date_from.strftime('%m%d%y'), self.date_to.strftime('%m%d%y')),
        })
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/?model=%s&id=%s&field=xlsx_file&filename_field=xlsx_filename&download=true'
                   % (self._name, self.id),
            'target': 'self',
        }

    def _render_xlsx(self, data):
        self.ensure_one()
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet(_('Payroll Summary')[:31])

        number = '#,##0.00;-#,##0.00;0.00'
        f_title = workbook.add_format({'bold': True, 'font_size': 14})
        f_subtitle = workbook.add_format({'italic': True})
        f_header = workbook.add_format({
            'bold': True, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True,
            'bottom': 1})
        f_label = {}
        f_amount = {}
        for row_type in ('title', 'line', 'subtotal', 'blank'):
            for level in range(4):
                label_fmt = {'indent': level * 2}
                amount_fmt = {'num_format': number}
                if row_type in ('title', 'subtotal'):
                    label_fmt['bold'] = True
                    amount_fmt['bold'] = True
                if row_type == 'subtotal':
                    amount_fmt['top'] = 1
                f_label[(row_type, level)] = workbook.add_format(label_fmt)
                f_amount[(row_type, level)] = workbook.add_format(amount_fmt)
        f_total_col = {
            key: workbook.add_format({**{'num_format': number, 'bold': True},
                                      **({'top': 1} if key == 'subtotal' else {})})
            for key in ('line', 'subtotal')
        }

        employees = data['employees']
        total_col = len(employees) + 1

        sheet.write(0, 0, self.company_id.name, f_title)
        sheet.write(1, 0, self._get_title(), f_title)
        sheet.write(2, 0, '%s (%s)' % (self._get_period_label(), data['date_basis_label']), f_subtitle)

        header_row = 4
        sheet.write(header_row, 0, '', f_header)
        for col, name in enumerate(employees, start=1):
            sheet.write(header_row, col, name, f_header)
        sheet.write(header_row, total_col, _('TOTAL'), f_header)
        sheet.set_row(header_row, 30)

        row_idx = header_row + 1
        for row in data['rows']:
            key = (row['type'], min(row['level'], 3))
            sheet.write(row_idx, 0, row['label'], f_label[key])
            if row['values'] is not None:
                for col, value in enumerate(row['values'], start=1):
                    sheet.write_number(row_idx, col, round(value, 2), f_amount[key])
                sheet.write_number(
                    row_idx, total_col, round(row['total'], 2),
                    f_total_col['subtotal' if row['type'] == 'subtotal' else 'line'])
            row_idx += 1

        sheet.set_column(0, 0, 42)
        sheet.set_column(1, total_col, 14)
        sheet.freeze_panes(header_row + 1, 1)
        sheet.set_landscape()
        sheet.set_paper(5)  # Legal
        sheet.repeat_rows(header_row)
        sheet.repeat_columns(0)

        workbook.close()
        return output.getvalue()
