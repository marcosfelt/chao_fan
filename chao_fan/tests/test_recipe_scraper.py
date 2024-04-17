from unittest.mock import Mock

from chao_fan.integrations.recipe_scrapers import (
    RecipeIngredient,
    Session,
    estimate_ingredient_price,
)


def test_estimate_ingredient_price_no_embedding(mocker):
    ingredient = RecipeIngredient(embedding=None)
    session = mocker.Mock(spec=Session)
    result = estimate_ingredient_price(ingredient, session)
    assert result is None


def test_estimate_ingredient_price_with_embedding(mocker):
    ingredient = RecipeIngredient(embedding=[0.1, 0.2, 0.3])
    session = mocker.Mock(spec=Session)
    mock_result = Mock()
    mock_result.embedding.cosine_distance.return_value = 0.7
    mock_result.price_100grams = 1.0
    session.exec().all.return_value = [mock_result] * 5
    result = estimate_ingredient_price(ingredient, session)
    assert result == 1.0  # The average price is 1.0


def test_estimate_ingredient_price_below_cutoff(mocker):
    ingredient = RecipeIngredient(embedding=[0.1, 0.2, 0.3])
    session = mocker.Mock(spec=Session)
    mock_result = Mock()
    mock_result.embedding.cosine_distance.return_value = 0.5
    mock_result.price_100grams = 1.0
    session.exec().all.return_value = [mock_result] * 5
    result = estimate_ingredient_price(ingredient, session)
    assert result is None
