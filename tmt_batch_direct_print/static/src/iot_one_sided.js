import { patch } from "@web/core/utils/patch";
import { IoTLongpolling } from "@iot_base/network_utils/longpolling";

// Print jobs the browser sends straight to an IoT Box. Same reason as
// models/bus_bus.py: without ``duplex: false`` the Windows IoT driver prints
// PDFs two-sided.
function oneSided(data) {
    if (typeof data === "string") {
        try {
            const parsed = JSON.parse(data);
            return parsed && parsed.document ? JSON.stringify({ duplex: false, ...parsed }) : data;
        } catch {
            return data;
        }
    }
    if (data && typeof data === "object" && data.document) {
        return { duplex: false, ...data };
    }
    return data;
}

patch(IoTLongpolling.prototype, {
    action(iot_ip, device_identifier, data, ...rest) {
        return super.action(iot_ip, device_identifier, oneSided(data), ...rest);
    },
});
