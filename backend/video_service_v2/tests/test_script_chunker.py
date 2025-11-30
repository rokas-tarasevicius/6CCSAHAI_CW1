"""Tests for script chunker."""
import pytest
from backend.video_service_v2.services.script_chunker import ScriptChunker


def test_chunk_script():
    """Test script chunking."""
    chunker = ScriptChunker(chunk_duration=3.0, words_per_minute=150)
    script = "word1 word2 word3 word4 word5 word6 word7 word8 word9 word10"
    
    chunks = chunker.chunk(script)
    
    assert len(chunks) > 0
    assert all(isinstance(chunk, str) for chunk in chunks)


def test_chunk_empty_script():
    """Test chunking empty script."""
    chunker = ScriptChunker()
    chunks = chunker.chunk("")
    
    assert chunks == [""]


def test_chunk_short_script():
    """Test chunking short script."""
    chunker = ScriptChunker(chunk_duration=3.0, words_per_minute=150)
    script = "short script"
    
    chunks = chunker.chunk(script)
    
    assert len(chunks) == 1
    assert chunks[0] == script


def test_chunk_custom_duration():
    """Test chunking with custom duration."""
    chunker = ScriptChunker(chunk_duration=1.0, words_per_minute=60)
    script = "word1 word2 word3 word4 word5"
    
    chunks = chunker.chunk(script)
    
    assert len(chunks) >= 1

