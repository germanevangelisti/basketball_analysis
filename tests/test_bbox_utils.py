import sys
import os
import pytest
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.bbox_utils import (
    get_center_of_bbox,
    get_bbox_width,
    measure_distance,
    measure_xy_distance,
    get_foot_position
)

def test_get_center_of_bbox():
    bbox = (0, 0, 100, 100)
    center = get_center_of_bbox(bbox)
    assert center == (50, 50)

    bbox = (10, 20, 30, 60) # width=20, height=40. center=(20, 40)
    center = get_center_of_bbox(bbox)
    assert center == (20, 40)

def test_get_bbox_width():
    bbox = (0, 0, 100, 100)
    width = get_bbox_width(bbox)
    assert width == 100

    bbox = (10, 20, 30, 60)
    width = get_bbox_width(bbox)
    assert width == 20

def test_measure_distance():
    p1 = (0, 0)
    p2 = (3, 4)
    dist = measure_distance(p1, p2)
    assert dist == 5.0

    p1 = (0, 0)
    p2 = (0, 10)
    dist = measure_distance(p1, p2)
    assert dist == 10.0

def test_measure_xy_distance():
    p1 = (10, 20)
    p2 = (5, 10)
    xy_dist = measure_xy_distance(p1, p2)
    assert xy_dist == (5, 10)

def test_get_foot_position():
    bbox = (0, 0, 100, 100)
    foot_pos = get_foot_position(bbox)
    assert foot_pos == (50, 100)
