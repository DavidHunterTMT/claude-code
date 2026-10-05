# Batch Shipment Direct Printing

Add-on for `dip_ups_batch_delivery`. On a shipping batch it sends these buttons
straight to a printer through Odoo IoT, with no download or preview:

| Button | Printer |
| --- | --- |
| Standard Delivery Slip | Delivery Slip Printer |
| Vending Delivery Slip | Delivery Slip Printer |
| S&W Standard Delivery Slip | Delivery Slip Printer |
| S&W Vending Delivery Slip | Delivery Slip Printer |
| Print Label | Shipping Label Printer |

If no printer is set for a button, it keeps its old download behavior.

## One-time setup

1. On the shipping station PC (Windows, left on, both printers installed in
   Windows), install Odoo's free **Windows virtual IoT** software and pair it
   with the database. Both printers then appear under *IoT > Devices*.
2. Install this add-on (it installs the *IoT* app with it).
3. Go to *Inventory > Configuration > Settings > Batch Shipment Printing* and
   choose the **Delivery Slip Printer** and **Shipping Label Printer**. Save.
4. The first time each button is used in a browser, Odoo may ask to confirm the
   printer. It remembers that choice in that browser from then on. To change
   it later, use *IoT > Configuration > Reset Linked Printers*.

## How it works

* The slip buttons already print through Odoo's report system, so linking the
  four slip reports to a printer is all they need.
* Print Label used to download the UPS label file. It now prints one of two
  reports, *Batch Shipping Label (PDF)* or *(ZPL)*, picked from the label's
  format. Those reports send the label files UPS returned, unchanged.
* The settings page reads and writes the printer linked to these reports,
  so a change made under *Settings > Technical > Reports > IoT* shows up there
  too.

For a thermal label printer (Zebra and similar), setting the UPS carrier's label
file type to **ZPL** gives faster, sharper labels than PDF.
