from unittest.mock import MagicMock, patch

import pytest
from chao_fan.db import engine
from chao_fan.integrations.pinterest import Pin
from chao_fan.models import Recipe
from chao_fan.pipelines.update_recipe_db import (enrich_recipes,
                                                 find_pins_not_in_db,
                                                 get_pinterest_links,
                                                 insert_pins_into_db)
from sqlalchemy.engine import Engine
from sqlmodel import Session


@pytest.fixture
def mock_engine():
    with patch.object(engine, "connect") as mock_connect:
        yield mock_connect

@pytest.fixture
def pinterest_pins():
    return [Pin(url="https://pinterest.com/pin1", site_name="Pinterest Site 1"), Pin(url="https://pinterest.com/pin2", site_name="Pinterest Site 2")]

@pytest.fixture
def database_recipes():
    return [Recipe(source_url="https://pinterest.com/pin1", source_name="Pinterest Site 1")]

@pytest.mark.parametrize("board_name,expected_call_count", [("TestBoard", 1), ("", 0)])
def test_get_pinterest_links(board_name, expected_call_count):
    with patch("chao_fan.pipelines.update_recipe_db.setup_pinterest") as mock_setup, \
         patch("chao_fan.pipelines.update_recipe_db.get_pinterest_board_id") as mock_get_board_id, \
         patch("chao_fan.pipelines.update_recipe_db.get_pin_links") as mock_get_links:
        mock_get_board_id.return_value = "123"
        mock_get_links.return_value = pinterest_pins
        links = get_pinterest_links(board_name)
        assert mock_setup.call_count == expected_call_count
        assert mock_get_board_id.call_count == expected_call_count
        assert mock_get_links.call_count == expected_call_count
        if board_name:
            assert len(links) == 2
        else:
            assert len(links) == 0

def test_find_pins_not_in_db(mock_engine, pinterest_pins, database_recipes):
    mock_engine.return_value.execute.return_value.fetchall.return_value = [(recipe.source_url,) for recipe in database_recipes]
    new_pins = find_pins_not_in_db(pinterest_pins, engine)
    assert len(new_pins) == 1
    assert new_pins[0].url == "https://pinterest.com/pin2"

def test_insert_pins_into_db(pinterest_pins):
    with patch.object(Session, "__enter__") as mock_session:
        insert_pins_into_db(pinterest_pins, engine)
        assert mock_session.add.call_count == len(pinterest_pins)

def test_enrich_recipes():
    with patch.object(Session, "__enter__") as mock_session, \
         patch("chao_fan.pipelines.update_recipe_db._enrich_recipes_batch") as mock_enrich_batch:
        enrich_recipes(engine, max_enrichments=10, batch_size=5)
        assert mock_enrich_batch.call_count == 2
