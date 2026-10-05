from odoo import _, models
from odoo.exceptions import UserError
from odoo.tools.pdf import merge_pdf

LABEL_PDF_REPORT = 'tmt_batch_direct_print.report_batch_shipping_label_pdf'
LABEL_ZPL_REPORT = 'tmt_batch_direct_print.report_batch_shipping_label_zpl'


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

    def _tmt_batch_label_attachments(self, res_ids, label_format):
        batches = self.env['stock.picking.batch'].browse(res_ids)
        labels = self.env['ir.attachment']
        for batch in batches:
            pdf, zpl = batch._tmt_label_attachments()
            labels |= pdf if label_format == 'pdf' else zpl
        if not labels:
            raise UserError(_("No %s shipping labels are attached to this batch.", label_format.upper()))
        return labels

    def _render_qweb_pdf(self, report_ref, res_ids=None, data=None):
        if self._get_report(report_ref).report_name == LABEL_PDF_REPORT:
            labels = self._tmt_batch_label_attachments(res_ids, 'pdf')
            return merge_pdf([label.raw for label in labels]), 'pdf'
        return super()._render_qweb_pdf(report_ref, res_ids=res_ids, data=data)

    def _render_qweb_text(self, report_ref, docids, data=None):
        if self._get_report(report_ref).report_name == LABEL_ZPL_REPORT:
            labels = self._tmt_batch_label_attachments(docids, 'zpl')
            return b'\n'.join(label.raw for label in labels), 'text'
        return super()._render_qweb_text(report_ref, docids, data=data)
