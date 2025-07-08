import allure
import pytest

from ..pages.main_page import MainPage
from ..pages.profile_page import ProfilePage


@allure.feature("Categories")
@allure.story("Add category")
@pytest.mark.categories
def test_add_category(
    main_page: MainPage,
    profile_page: ProfilePage,
    login,
    spend_db,
    add_and_cleanup_category,
):
    main_page.history_of_spending_title.should_be_visible()
    main_page.no_spending_text.should_be_visible()
    main_page.navbar.open_profile_page()
    profile_page.add_category("Food")
    add_and_cleanup_category("Food")

    category_db = spend_db.get_category_by_name("Food")
    assert category_db[0].name == "Food"
    assert category_db[0].username == login[0]


@allure.feature("Categories")
@allure.story("Edit category")
@pytest.mark.categories
def test_edit_category_db(
    main_page: MainPage,
    profile_page: ProfilePage,
    login,
    spend_db,
    add_and_cleanup_category,
):
    main_page.navbar.open_profile_page()
    old_name = "OldCat"
    new_name = "NewCat"
    profile_page.add_category(old_name)
    add_and_cleanup_category([old_name, new_name])

    profile_page.edit_category_name(old_name, new_name)

    assert not spend_db.get_category_by_name(old_name)
    new_cat = spend_db.get_category_by_name(new_name)
    assert new_cat
    assert new_cat[0].name == new_name
    assert new_cat[0].username == login[0]


@allure.feature("Categories")
@allure.story("Archive category")
@pytest.mark.categories
def test_archive_category_db(
    main_page: MainPage,
    profile_page: ProfilePage,
    login,
    spend_db,
    add_and_cleanup_category,
):
    main_page.navbar.open_profile_page()
    category_name = "TestCategory"
    profile_page.add_category(category_name)
    add_and_cleanup_category([category_name])

    profile_page.archive_category(category_name)

    test_category_db = spend_db.get_category_by_name(category_name)

    assert test_category_db[0].name == category_name
    assert test_category_db[0].username == login[0]
    assert test_category_db[0].archived

    profile_page.unarchive_category(category_name)

    test_category_db_after = spend_db.get_category_by_name(category_name)

    assert test_category_db_after[0].name == category_name
    assert test_category_db_after[0].username == login[0]
    assert not test_category_db_after[0].archived
