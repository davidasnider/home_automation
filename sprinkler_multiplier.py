"""Primary script for calculating the sprinkler multiplier data and posting
to Indigo.
"""

from home_automation import sprinkler_multiplier, utilities

# Create our multiplier object
sprinkler = sprinkler_multiplier.sprinkler_multiplier()

# Get all of our values
sprinkler.calc_multiplier()

# Update our Home Automation Server
utilities.update_indigo_variable("sprinklerDurationMultiplier", sprinkler.value)

# Generate the chart
sprinkler.get_chart()

# Email html report
email_message = sprinkler.get_email_message()
utilities.send_email(email_message)

# Print Text Report
print(sprinkler.text_report())
