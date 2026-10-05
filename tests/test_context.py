from simplecron.context import Context


def test_set_and_get_value():
    context = Context()
    context.set_value("next_page", 1)

    assert context.get_value("next_page") == 1
    assert context.get_value("non_existent_key") is None
