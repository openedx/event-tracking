"""
This module contains various configuration settings via
waffle switches for the event-tracking app.
"""

from edx_toggles.toggles import SettingToggle

# .. toggle_name: SEND_TRACKING_EVENT_EMITTED_SIGNAL
# .. toggle_implementation: SettingToggle
# .. toggle_default: False
# .. toggle_description: When True, the system will publish `TRACKING_EVENT_EMITTED` signals to the event bus. The
#   `TRACKING_EVENT_EMITTED` signal is emit when a tracking log is emitted.
# .. toggle_use_cases: opt_in
# .. toggle_creation_date: 2023-10-26
SEND_TRACKING_EVENT_EMITTED_SIGNAL = SettingToggle(
    'SEND_TRACKING_EVENT_EMITTED_SIGNAL',
    default=False,
    module_name=__name__
)
