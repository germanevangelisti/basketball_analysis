"""
A module providing utility functions for bounding box calculations and measurements.

This module contains helper functions for working with bounding boxes, including
calculations for centers, widths, and distances between points.
"""
from typing import Tuple, List, Union

def get_center_of_bbox(bbox: Union[Tuple[float, float, float, float], List[float]]) -> Tuple[int, int]:
    """
    Calculate the center coordinates of a bounding box.

    Args:
        bbox (tuple or list): Bounding box coordinates in format (x1, y1, x2, y2).

    Returns:
        tuple: Center coordinates (x, y) of the bounding box.
    """
    x1, y1, x2, y2 = bbox
    return int((x1 + x2) / 2), int((y1 + y2) / 2)

def get_bbox_width(bbox: Union[Tuple[float, float, float, float], List[float]]) -> float:
    """
    Calculate the width of a bounding box.

    Args:
        bbox (tuple or list): Bounding box coordinates in format (x1, y1, x2, y2).

    Returns:
        float: Width of the bounding box.
    """
    return bbox[2] - bbox[0]

def measure_distance(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    """
    Calculate the Euclidean distance between two points.

    Args:
        p1 (tuple): First point coordinates (x, y).
        p2 (tuple): Second point coordinates (x, y).

    Returns:
        float: Euclidean distance between the two points.
    """
    return ((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)**0.5

def measure_xy_distance(p1: Tuple[float, float], p2: Tuple[float, float]) -> Tuple[float, float]:
    """
    Calculate the separate x and y distances between two points.

    Args:
        p1 (tuple): First point coordinates (x, y).
        p2 (tuple): Second point coordinates (x, y).

    Returns:
        tuple: The (x_distance, y_distance) between the points.
    """
    return p1[0] - p2[0], p1[1] - p2[1]

def get_foot_position(bbox: Union[Tuple[float, float, float, float], List[float]]) -> Tuple[int, int]:
    """
    Calculate the position of the bottom center point of a bounding box.

    Args:
        bbox (tuple or list): Bounding box coordinates in format (x1, y1, x2, y2).

    Returns:
        tuple: Coordinates (x, y) of the bottom center point.
    """
    x1, y1, x2, y2 = bbox
    return int((x1 + x2) / 2), int(y2)
