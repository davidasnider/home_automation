"""Tests for the utilities module"""
import random

from home_automation import utilities


# Test updating a variable in indigo
def test_update_indigo_var():
    """Test that the update_indigo_var function works as expected. The same value
    that is passed in will be returned.
    """
    random_number = random.randint(0, 100)
    variable_name = "test_do_not_delete"
    assert utilities.update_indigo_variable(variable_name, random_number)
    return_value = utilities.get_indigo_variable(variable_name)
    assert random_number == return_value
