from odoo import _, models
from odoo.exceptions import UserError
from odoo.tools.pdf import merge_pdf

# report_name -> label format. Each report's model (stock.picking.batch or
# stock.picking) implements _tmt_label_attachments().
LABEL_REPORTS = {
    'tmt_batch_direct_print.report_batch_shipping_label_pdf': 'pdf',
    'tmt_batch_direct_print.report_batch_shipping_label_zpl': 'zpl',
    'tmt_batch_direct_print.report_picking_shipping_label_pdf': 'pdf',
    'tmt_batch_direct_print.report_picking_shipping_label_zpl': 'zpl',
}


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    # Printer link helpers. The iot module names the field ``device_ids``
    # (Many2many) in recent versions and ``device_id`` (Many2one) in older
    # ones; support both so a version bump does not break the settings page.

    def _tmt_get_printer(self):
        """First IoT printer linked to this report, or an empty recordset."""
        self.ensure_one()
        if 'device_ids' in self._fields:
            return self.device_ids[:1]
        return self.device_id

    def _tmt_set_printer(self, device):
        """Link ``device`` (may be empty) to every report in ``self``.

        Reports already printing to ``device`` first are left alone, so extra
        printers added by hand under Technical > Reports are not wiped out
        every time the settings page is saved.
        """
        for report in self:
            if report._tmt_get_printer() == device:
                continue
            if 'device_ids' in report._fields:
                report.device_ids = [(6, 0, device.ids)]
            else:
                report.device_id = device

    # Label reports: hand back the carrier's label files instead of rendering.

    def _tmt_label_attachments(self, res_ids):
        label_format = LABEL_REPORTS[self.report_name]
        labels = self.env['ir.attachment']
        for record in self.env[self.model].browse(res_ids):
            pdf, zpl = record._tmt_label_attachments()
            labels |= pdf if label_format == 'pdf' else zpl
        if not labels:
            raise UserError(_("No %s shipping labels are attached to this record.", label_format.upper()))
        return labels

    def _render_qweb_pdf(self, report_ref, res_ids=None, data=None):
        report = self._get_report(report_ref)
        if report.report_name in LABEL_REPORTS:
            labels = report._tmt_label_attachments(res_ids)
            return merge_pdf([label.raw for label in labels]), 'pdf'
        return super()._render_qweb_pdf(report_ref, res_ids=res_ids, data=data)

    def _render_qweb_text(self, report_ref, docids, data=None):
        report = self._get_report(report_ref)
        if report.report_name in LABEL_REPORTS:
            labels = report._tmt_label_attachments(docids)
            return b'\n'.join(label.raw for label in labels), 'text'
        return super()._render_qweb_text(report_ref, docids, data=data)
