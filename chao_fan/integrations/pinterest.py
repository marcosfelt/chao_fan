import logging
from dataclasses import dataclass
from typing import List, Optional

from py3pin.Pinterest import Pinterest


@dataclass
class Pin:
    url: str
    site_name: str


def setup_pinterest(email: str, password: str, username: str) -> Pinterest:
    """Setup pinterest"""
    pinterest = Pinterest(email=email, password=password, username=username)
    try:
        pinterest.login()
    except Exception as e:
        raise
    return pinterest


def get_pinterest_board_id(pinterest: Pinterest, name: str) -> Optional[str]:
    """Get pinterest board id

    Parameters
    ----------
    pinterest : Pinterest
        A logged in Pinterest object
    name : str
        The name of the board

    Returns
    -------
    Optional[str]
        The id of the board

    """
    boards = pinterest.boards()
    for board in boards:
        if board["name"] == name:
            return board["id"]
    return None


def get_pin_links(
    pinterest: Pinterest, board_id: str, return_unique: bool = True
) -> List[Pin]:
    """Get links pinterest board

    Parameters
    ----------
    pinterest : Pinterest
        A logged in Pinterest object
    board_id : str
        The id of the board to get links from

    Returns
    -------
    List[Pin]
        Pins from the board

    """
    pins = pinterest.board_feed(board_id=board_id)
    recipes = []
    for pin_dict in pins:
        if "rich_summary" in pin_dict and pin_dict["rich_summary"] is not None:
            recipe_pin = Pin(
                url=pin_dict["rich_summary"].get("url"),
                site_name=pin_dict["rich_summary"].get("site_name"),
            )
            recipes.append(recipe_pin)
    if return_unique:
        recipes = list({recipe.url: recipe for recipe in recipes}.values())
    return recipes
