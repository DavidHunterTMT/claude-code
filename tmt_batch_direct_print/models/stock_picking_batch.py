from odoo import models
from odoo.exceptions import UserError

# Keys understood by dip_ups_batch_delivery's _dip_get_picking_delivery_slip_report.
SLIP_REPORT_KEYS = ('standard', 'vending', 'sw_standard', 'sw_vending')


def split_labels(labels):
    """Split label attachments into (PDF, ZPL), oldest first."""
    labels = labels.sorted('id')
    pdf = labels.filtered(
        lambda a: a.mimetype == 'application/pdf' or (a.name or '').lower().endswith('.pdf')
    )
    zpl = (labels - pdf).filtered(lambda a: (a.name or '').lower().endswith('.zpl'))
    return pdf, zpl


class StockPickingBatch(models.Model):
    _inherit = 'stock.picking.batch'

    def _tmt_slip_reports(self):
        """The four delivery slip reports printed from a shipping batch."""
        reports = self.env['ir.actions.report']
        for key in SLIP_REPORT_KEYS:
            try:
                reports |= self._dip_get_picking_delivery_slip_report(key)
            except UserError:
                # A Studio slip report was deleted; the button already errors
                # on its own, so just leave it out of the printer settings.
                continue
        return reports

    def _tmt_label_reports(self):
        pdf_report = self.env.ref('tmt_batch_direct_print.action_report_batch_shipping_label_pdf')
        zpl_report = self.env.ref('tmt_batch_direct_print.action_report_batch_shipping_label_zpl')
        return pdf_report | zpl_report

    def _tmt_label_attachments(self):
        """Split this batch's shipping labels into (PDF, ZPL) attachments."""
        self.ensure_one()
        return split_labels(self.label_attachment_ids)

    def action_print_labels(self):
        """Send the labels to the label printer when one is configured.

        Falls back to the original download when no printer is linked, or when
        the labels are in a format the label printer report cannot send (GIF,
        or a mix of PDF and ZPL).
        """
        self.ensure_one()
        pdf, zpl = self._tmt_label_attachments()
        labels = pdf | zpl
        if not labels or labels != self.label_attachment_ids or (pdf and zpl):
            return super().action_print_labels()
        pdf_report, zpl_report = self._tmt_label_reports()
        report = pdf_report if pdf else zpl_report
        if not report._tmt_get_printer():
            return super().action_print_labels()
        return report.report_action(self)
