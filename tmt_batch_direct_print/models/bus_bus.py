from odoo import models


class BusBus(models.Model):
    _inherit = 'bus.bus'

    def _sendone(self, target, notification_type, message):
        # Print jobs the server relays to an IoT Box. The Windows IoT driver
        # prints PDFs two-sided unless the job carries ``duplex: False``, and
        # the Odoo 19 iot module never sends it. Default every job to one-sided.
        if notification_type == 'iot_action' and isinstance(message, dict) and message.get('document'):
            message = {'duplex': False, **message}
        return super()._sendone(target, notification_type, message)
