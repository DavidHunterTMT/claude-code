from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # Not stored anywhere of their own: the printer linked to the reports is
    # the setting, so changing it under Technical > Reports shows up here too.
    tmt_batch_slip_printer_id = fields.Many2one(
        'iot.device',
        string="Delivery Slip Printer",
        domain=[('type', '=', 'printer')],
    )
    tmt_batch_label_printer_id = fields.Many2one(
        'iot.device',
        string="Shipping Label Printer",
        domain=[('type', '=', 'printer')],
    )

    @api.model
    def get_values(self):
        res = super().get_values()
        batch = self.env['stock.picking.batch']
        slip_reports = batch._tmt_slip_reports()
        res.update(
            tmt_batch_slip_printer_id=slip_reports[:1]._tmt_get_printer().id if slip_reports else False,
            tmt_batch_label_printer_id=batch._tmt_label_reports()[:1]._tmt_get_printer().id,
        )
        return res

    def set_values(self):
        super().set_values()
        batch = self.env['stock.picking.batch']
        batch._tmt_slip_reports()._tmt_set_printer(self.tmt_batch_slip_printer_id)
        label_reports = batch._tmt_label_reports() | self.env['stock.picking']._tmt_label_reports()
        # delivery_iot (auto-installed with IoT) adds Print > Shipping Labels on
        # deliveries, which errors until the report is linked to a printer.
        shipping_labels = self.env.ref('delivery_iot.report_shipping_labels', raise_if_not_found=False)
        if shipping_labels:
            label_reports |= shipping_labels
        label_reports._tmt_set_printer(self.tmt_batch_label_printer_id)
        self.env['stock.picking']._tmt_set_print_menu_domains()
