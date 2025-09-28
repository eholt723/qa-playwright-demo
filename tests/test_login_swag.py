def test_login_success(page):
    page.goto("https://www.saucedemo.com/")
    page.fill("#user-name", "standard_user")
    page.fill("#password", "secret_sauce")
    page.click("#login-button")
    page.wait_for_url("**/inventory.html")
    assert "inventory" in page.url

def test_login_bad_password(page):
    page.goto("https://www.saucedemo.com/")
    page.fill("#user-name", "standard_user")
    page.fill("#password", "wrong_password")
    page.click("#login-button")
    err = page.locator("[data-test='error']")
    err.wait_for()
    assert "Epic sadface" in err.text_content()
