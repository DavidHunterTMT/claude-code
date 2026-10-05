from odoo import _, api, fields, models
from odoo.exceptions import UserError

from .stock_picking_batch import split_labels

# Done delivery orders print these from header buttons, so hide them from
# Print in the gear menu there; every other transfer keeps them in the menu.
BUTTON_REPORTS_MENU_DOMAIN = "['|', ('picking_type_code', '!=', 'outgoing'), ('state', '!=', 'done')]"


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    tmt_label_count = fields.Integer(compute='_compute_tmt_label_count')

    def _compute_tmt_label_count(self):
        for picking in self:
            pdf, zpl = picking._tmt_label_attachments()
            picking.tmt_label_count = len(pdf | zpl)

    def _tmt_label_attachments(self):
        """Labels of the latest chatter message that posted any, as (PDF, ZPL).

        The UPS connector posts each shipment's labels (LabelUPS*.pdf/.zpl) on
        one message, so the newest such message is the current shipment, not a
        voided earlier one.
        """
        self.ensure_one()
        for message in self.message_ids.sorted('id', reverse=True):
            labels = message.attachment_ids.filtered(lambda a: (a.name or '').lower().startswith('label'))
            if labels:
                return split_labels(labels)
        return self.env['ir.attachment'], self.env['ir.attachment']

    def _tmt_label_reports(self):
        pdf_report = self.env.ref('tmt_batch_direct_print.action_report_picking_shipping_label_pdf')
        zpl_report = self.env.ref('tmt_batch_direct_print.action_report_picking_shipping_label_zpl')
        return pdf_report | zpl_report

    @api.model
    def _tmt_delivery_iot_label_report(self):
        """delivery_iot's Print > Shipping Labels report, if that module is installed.

        Looked up by report_name: its XML id names the QWeb template (an
        ir.ui.view), not the report action.
        """
        return self.env['ir.actions.report'].search([
            ('model', '=', 'stock.picking'),
            ('report_name', '=', 'delivery_iot.report_shipping_labels'),
        ])

    @api.model
    def _tmt_set_print_menu_domains(self):
        """Hide the slip and shipping-label reports from Print on done deliveries.

        Called on install/upgrade (data/gear_menu_data.xml) and when the
        printer settings are saved, so a report added later is covered too.
        """
        reports = self.env['stock.picking.batch']._tmt_slip_reports() | self._tmt_delivery_iot_label_report()
        reports.filtered(lambda r: r.domain != BUTTON_REPORTS_MENU_DOMAIN).domain = BUTTON_REPORTS_MENU_DOMAIN

    def _tmt_print_delivery_slip(self, report_key):
        self.ensure_one()
        report = self.env['stock.picking.batch']._dip_get_picking_delivery_slip_report(report_key)
        return report.report_action(self)

    def action_tmt_print_standard_delivery_slip(self):
        return self._tmt_print_delivery_slip('standard')

    def action_tmt_print_vending_delivery_slip(self):
        return self._tmt_print_delivery_slip('vending')

    def action_tmt_print_sw_standard_delivery_slip(self):
        return self._tmt_print_delivery_slip('sw_standard')

    def action_tmt_print_sw_vending_delivery_slip(self):
        return self._tmt_print_delivery_slip('sw_vending')

    def action_tmt_print_label(self):
        """Print this delivery's UPS label on the Shipping Label Printer."""
        self.ensure_one()
        pdf, zpl = self._tmt_label_attachments()
        if not pdf and not zpl:
            raise UserError(_("No shipping label is attached to this delivery."))
        if pdf and zpl:
            raise UserError(_("This delivery has both PDF and ZPL labels; print them from the chatter."))
        pdf_report, zpl_report = self._tmt_label_reports()
        return (pdf_report if pdf else zpl_report).report_action(self)
