{
    'name': 'Batch Shipment Direct Printing',
    'version': '19.0.1.2.2',
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

Done delivery orders get the same five buttons, and those reports leave Print
in the gear menu there. The standard Delivery Slip
button moves to Print in the gear menu, and on batches Print and Print Labels
move to the gear menu.

Pick both printers once under *Inventory > Configuration > Settings >
Batch Shipment Printing*. A report with no printer set falls back to the
normal download.

Every PDF sent to an IoT printer prints one-sided. The Windows IoT driver
otherwise forces two-sided printing on printers that have a duplex unit.
""",
    'author': 'Tennessee Machine Tool',
    'license': 'LGPL-3',
    'depends': ['iot', 'iot_base', 'dip_ups_batch_delivery'],
    'data': [
        'report/batch_shipping_label_report.xml',
        'data/gear_menu_data.xml',
        'views/res_config_settings_views.xml',
        'views/stock_picking_views.xml',
        'views/stock_picking_batch_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'tmt_batch_direct_print/static/src/iot_one_sided.js',
        ],
    },
    'installable': True,
    'application': False,
}
