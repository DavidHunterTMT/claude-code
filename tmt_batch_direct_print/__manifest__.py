{
    'name': 'Batch Shipment Direct Printing',
    'version': '19.0.1.0.0',
    'category': 'Inventory/Delivery',
    'summary': 'Print batch shipment delivery slips and shipping labels straight to IoT printers',
    'description': """
Batch Shipment Direct Printing
==============================
Add-on for *DIP - UPS Batch Delivery*. On a shipping batch, these buttons
print straight to a printer through Odoo IoT instead of downloading a PDF:

* Standard Delivery Slip, Vending Delivery Slip, S&W Standard Delivery Slip
  and S&W Vending Delivery Slip print to the **Delivery Slip Printer**.
* Print Label prints the batch's UPS labels (PDF or ZPL) to the
  **Shipping Label Printer**.

Pick both printers once under *Inventory > Configuration > Settings >
Batch Shipment Printing*. A report with no printer set falls back to the
normal download.
""",
    'author': 'Tennessee Machine Tool',
    'license': 'LGPL-3',
    'depends': ['iot', 'dip_ups_batch_delivery'],
    'data': [
        'report/batch_shipping_label_report.xml',
        'views/res_config_settings_views.xml',
    ],
    'installable': True,
    'application': False,
}
