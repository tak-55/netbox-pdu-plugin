from utilities.choices import ChoiceSet


class VendorChoices(ChoiceSet):
    """PDU vendor / backend selector"""

    RARITAN = "raritan"
    UBIQUITI = "ubiquiti"

    CHOICES = [
        (RARITAN, "Raritan"),
        (UBIQUITI, "Ubiquiti (USP-PDU-Pro)"),
    ]


class OutletStatusChoices(ChoiceSet):
    """Power state of a PDU outlet"""

    ON = "on"
    OFF = "off"
    UNKNOWN = "unknown"

    CHOICES = [
        (ON, "ON", "green"),
        (OFF, "OFF", "red"),
        (UNKNOWN, "Unknown", "grey"),
    ]


class LinePairChoices(ChoiceSet):
    """Line-pair identifier for 3-phase inlet data"""

    L1L2 = "L1L2"
    L2L3 = "L2L3"
    L3L1 = "L3L1"

    CHOICES = [
        (L1L2, "L1-L2"),
        (L2L3, "L2-L3"),
        (L3L1, "L3-L1"),
    ]


class SyncStatusChoices(ChoiceSet):
    """PDU synchronization status"""

    SUCCESS = "success"
    FAILED = "failed"
    NEVER = "never"

    CHOICES = [
        (SUCCESS, "Success", "green"),
        (FAILED, "Failed", "red"),
        (NEVER, "Never synced", "grey"),
    ]
