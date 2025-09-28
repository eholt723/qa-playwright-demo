def test_checkboxes_toggle(page):
    page.goto("https://the-internet.herokuapp.com/checkboxes")
    boxes = page.locator("input[type='checkbox']")
    assert boxes.count() == 2
    for i in range(2):
        boxes.nth(i).check()
        assert boxes.nth(i).is_checked()

def test_status_codes_200(page):
    page.goto("https://the-internet.herokuapp.com/status_codes")
    page.click("text=200")
    page.wait_for_url("**/status_codes/200")
    assert "200" in page.text_content("body")
