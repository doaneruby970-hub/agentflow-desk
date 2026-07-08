"""Tests for retrieval service."""

import pytest
from uuid import uuid4

from app.services.retrieval import RetrievalService


def test_cosine_similarity():
    """Test cosine similarity calculation."""
    service = RetrievalService()

    # Identical vectors
    a = [1.0, 2.0, 3.0]
    b = [1.0, 2.0, 3.0]
    similarity = service._cosine_similarity(a, b)
    assert abs(similarity - 1.0) < 0.0001

    # Orthogonal vectors
    a = [1.0, 0.0]
    b = [0.0, 1.0]
    similarity = service._cosine_similarity(a, b)
    assert abs(similarity - 0.0) < 0.0001

    # Opposite vectors
    a = [1.0, 0.0]
    b = [-1.0, 0.0]
    similarity = service._cosine_similarity(a, b)
    assert abs(similarity - (-1.0)) < 0.0001
