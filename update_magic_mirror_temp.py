"""Updates the magic mirror indoor temperature setting based on the
office_temperature variable, which is set by a scheduled task named:
'Update Office Temperature'
"""

from home_automation import utilities

variable = "office_temperature"

indoor_temperature = utilities.get_indigo_variable(variable)

utilities.update_magicmirror_internal_temperature(indoor_temperature)
