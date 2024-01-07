"""Tests for the utilities module"""
import random

from home_automation import utilities


# Test updating a variable in indigo
def test_update_indigo_var():
    """Test that the update_indigo_var function works as expected. The same value
    that is passed in will be returned.
    """
    random_number = random.randint(0, 100)
    object_id = 797144911
    assert utilities.update_indigo_variable(object_id=object_id, value=random_number)
    return_value = utilities.get_indigo_variable(object_id=object_id)
    assert str(random_number) == return_value
