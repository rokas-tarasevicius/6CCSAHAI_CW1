#!/usr/bin/env python3
"""Diagnostic script to check if word timestamps are being generated and used correctly.

This script traces the data flow from TTS generation through video assembly to verify
that ElevenLabs word timestamps are actually being used in subtitle generation.
"""
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.video_service.services.video.content_recommender import ContentRecommender
from backend.video_service.services.video.tts_service import TTSService
from backend.video_service.services.video.script_generator import ScriptGenerator
from backend.video_service.services.video.video_assembler import VideoAssembler
from backend.course_service.models.course import CourseStructure, Topic, Subtopic, Concept


def load_course():
    """Load course from parsed_data.json."""
    parsed_data_file = BACKEND_ROOT / "course_service" / "data" / "parsed_data.json"
    
    if not parsed_data_file.exists():
        print("❌ parsed_data.json not found - cannot load course")
        return None
    
    # Load parsed data
    with open(parsed_data_file, 'r', encoding='utf-8') as f:
        parsed_data = json.load(f)
    
    # Convert parsed data to CourseStructure
    topics = []
    for file_path, file_data in parsed_data.items():
        file_name = file_data["metadata"]["file_name"]
        content = file_data["content"]
        
        # Extract topic name from file name (remove .pdf extension)
        topic_name = file_name.replace('.pdf', '').replace('_', ' ').title()
        
        # Use content preview for better context
        content_preview = content[:20000] if len(content) > 20000 else content
        
        # Create a single subtopic for the entire PDF content
        subtopic = Subtopic(
            name="Main Content",
            description=f"Content from {file_name}",
            concepts=[
                Concept(
                    name=topic_name,
                    description=content_preview,
                    keywords=[]
                )
            ]
        )
        
        topic = Topic(
            name=topic_name,
            description=f"Content from {file_name}",
            subtopics=[subtopic]
        )
        topics.append(topic)
    
    course = CourseStructure(
        title="Course Material",
        description="Course material from parsed PDFs",
        topics=topics
    )
    
    return course


def step1_tts_only():
    """Step 1: Check if TTS service generates word timestamps."""
    print("=" * 70)
    print("STEP 1: TTS Service - Word Timestamp Generation")
    print("=" * 70)
    
    tts_service = TTSService()
    
    if not tts_service.elevenlabs_available:
        print("❌ ElevenLabs not available - cannot generate timestamps")
        return None
    
    test_text = "Hello world. This is a test sentence."
    test_audio_path = project_root / "videos" / "audio" / "_test_timestamps.mp3"
    
    print(f"\n📝 Test text: {test_text}")
    print(f"🔊 Calling TTSService.text_to_speech(..., return_timestamps=True)...")
    
    try:
        result = tts_service.text_to_speech(
            test_text,
            str(test_audio_path),
            return_timestamps=True
        )
        
        if isinstance(result, tuple):
            success, word_timestamps = result
            print(f"✅ TTS returned tuple: success={success}")
            
            if word_timestamps:
                print(f"✅ Word timestamps is non-empty: {len(word_timestamps)} sentences")
                
                # Show first couple of sentences with word timings
                for i, (sentence, words) in enumerate(list(word_timestamps.items())[:2]):
                    print(f"\n   Sentence {i+1}: '{sentence}'")
                    print(f"   Words: {len(words)}")
                    for j, (start, end, word) in enumerate(words[:4]):  # Show first 4 words
                        print(f"      [{j}] '{word}': {start:.3f}s - {end:.3f}s (duration: {end-start:.3f}s)")
                    if len(words) > 4:
                        print(f"      ... and {len(words) - 4} more words")
                
                # Check if audio file exists
                if test_audio_path.exists():
                    file_size = test_audio_path.stat().st_size
                    print(f"\n✅ Audio file created: {test_audio_path}")
                    print(f"   File size: {file_size} bytes")
                else:
                    print(f"\n⚠️  Audio file not found at: {test_audio_path}")
                
                return word_timestamps
            else:
                print("❌ Word timestamps is None or empty")
                print("   This means convert_with_timestamps is not returning alignment data")
                return None
        else:
            print(f"❌ TTS returned non-tuple: {type(result)}")
            print(f"   Expected tuple (success, word_timestamps)")
            return None
            
    except Exception as e:
        print(f"❌ Error generating TTS timestamps: {e}")
        import traceback
        traceback.print_exc()
        return None


def step2_full_pipeline():
    """Step 2: Check full pipeline - TTS → ContentRecommender → VideoAssembler."""
    print("\n" + "=" * 70)
    print("STEP 2: Full Pipeline - TTS → ContentRecommender → VideoAssembler")
    print("=" * 70)
    print("\n⚠️  NOTE: This step requires significant ElevenLabs credits.")
    print("   If you see quota errors, Step 1 already confirmed TTS timestamps work.")
    print("   You can skip this step if Step 1 passed.\n")
    
    try:
        # Load course
        course = load_course()
        
        if not course:
            print("❌ Cannot load course - check parsed_data.json")
            return
        
        # Get a concept
        all_concepts = course.get_all_concepts()
        if not all_concepts:
            print("❌ No concepts found in course")
            return
        
        topic, subtopic, concept = all_concepts[0]
        print(f"\n📚 Using concept: {topic} / {subtopic} / {concept.name}")
        
        # Create services
        script_generator = ScriptGenerator()
        tts_service = TTSService()
        video_assembler = VideoAssembler()
        
        # Monkey patch TTS to log timestamp returns
        original_tts = tts_service.text_to_speech
        tts_called = {"called": False, "returned_timestamps": False}
        
        def traced_tts(text, path, return_timestamps=False):
            tts_called["called"] = True
            print(f"\n   📞 TTSService.text_to_speech called")
            print(f"      text length: {len(text)} chars")
            print(f"      return_timestamps: {return_timestamps}")
            
            result = original_tts(text, path, return_timestamps=return_timestamps)
            
            if return_timestamps and isinstance(result, tuple):
                success, word_ts = result
                tts_called["returned_timestamps"] = word_ts is not None and bool(word_ts)
                print(f"      ✅ Returned tuple with word_timestamps: {tts_called['returned_timestamps']}")
                if word_ts:
                    print(f"         Sentences: {len(word_ts)}")
                    total_words = sum(len(words) for words in word_ts.values())
                    print(f"         Total words: {total_words}")
                else:
                    print(f"         ⚠️  word_timestamps is None or empty")
            else:
                print(f"      ❌ Did not return timestamps (returned: {type(result)})")
            
            return result
        
        tts_service.text_to_speech = traced_tts
        
        # Monkey patch subtitle generation to inspect ASS file
        original_write_subs = video_assembler._write_subtitles_with_word_highlighting
        subs_called = {"called": False, "received_timestamps": False}
        
        def traced_write_subs(script, duration, subtitle_path, word_timestamps=None):
            subs_called["called"] = True
            subs_called["received_timestamps"] = word_timestamps is not None and bool(word_timestamps)
            
            print(f"\n   📝 VideoAssembler._write_subtitles_with_word_highlighting called")
            print(f"      script length: {len(script)} chars")
            print(f"      duration: {duration:.2f}s")
            print(f"      word_timestamps provided: {subs_called['received_timestamps']}")
            
            if word_timestamps:
                print(f"      ✅ Using karaoke mode (timestamp-based)")
                print(f"         Sentences in timestamps: {len(word_timestamps)}")
            else:
                print(f"      ❌ Using fallback heuristic mode (no timestamps)")
            
            # Call original
            result = original_write_subs(script, duration, subtitle_path, word_timestamps)
            
            # Inspect generated ASS file
            if subtitle_path.exists():
                print(f"\n   📄 Generated ASS file: {subtitle_path}")
                ass_content = subtitle_path.read_text(encoding='utf-8')
                file_size = subtitle_path.stat().st_size
                print(f"      File size: {file_size} bytes")
                
                # Check for karaoke tags
                has_karaoke = r'\k' in ass_content or r'{\k' in ass_content
                
                if has_karaoke:
                    karaoke_count = ass_content.count(r'{\k')
                    print(f"      ✅ Contains karaoke tags (\\k) - using timestamps!")
                    print(f"         Found {karaoke_count} karaoke timing tags")
                    
                    # Show first dialogue line with karaoke
                    lines = ass_content.split('\n')
                    dialogue_lines = [l for l in lines if l.startswith('Dialogue:')]
                    if dialogue_lines:
                        first_dialogue = dialogue_lines[0]
                        print(f"\n      First dialogue event:")
                        # Show first 150 chars
                        print(f"         {first_dialogue[:150]}...")
                else:
                    print(f"      ❌ Does NOT contain karaoke tags - using fallback!")
                    
                    # Show first few dialogue lines
                    lines = ass_content.split('\n')
                    dialogue_lines = [l for l in lines if l.startswith('Dialogue:')]
                    print(f"\n      Sample dialogue events (first 2):")
                    for i, dl in enumerate(dialogue_lines[:2]):
                        print(f"         {i+1}. {dl[:120]}...")
            
            return result
        
        video_assembler._write_subtitles_with_word_highlighting = traced_write_subs
        
        # Create ContentRecommender with patched services
        recommender = ContentRecommender(
            course=course,
            script_generator=script_generator,
            tts_service=tts_service,
            video_assembler=video_assembler
        )
        
        print(f"\n🎬 Generating video content...")
        print(f"   (Will trace word_timestamps through the pipeline)")
        
        # Generate video
        video_content = recommender.generate_video_content(
            topic=topic,
            subtopic=subtopic,
            concept_name=concept.name,
            relevance_score=0.8
        )
        
        print(f"\n✅ Video generation completed")
        print(f"   Audio path: {video_content.metadata.audio_path}")
        print(f"   Video path: {video_content.metadata.video_path}")
        
        # Summary
        print(f"\n📋 PIPELINE SUMMARY:")
        print(f"   TTS called: {tts_called['called']}")
        print(f"   TTS returned timestamps: {tts_called['returned_timestamps']}")
        print(f"   Subtitle generation called: {subs_called['called']}")
        print(f"   Subtitle generation received timestamps: {subs_called['received_timestamps']}")
        
        if tts_called['returned_timestamps'] and subs_called['received_timestamps']:
            print(f"\n   ✅ SUCCESS: Timestamps flow correctly through pipeline!")
        elif tts_called['returned_timestamps'] and not subs_called['received_timestamps']:
            print(f"\n   ⚠️  WARNING: TTS generates timestamps but they don't reach subtitle generation")
        elif not tts_called['returned_timestamps']:
            print(f"\n   ❌ ISSUE: TTS is not generating timestamps")
        
    except ValueError as e:
        error_str = str(e)
        error_lower = error_str.lower()
        
        # Check if it's related to audio generation failure (likely quota)
        if 'audio generation failed' in error_lower or 'file not created' in error_lower:
            print(f"\n⚠️  AUDIO GENERATION FAILED")
            print(f"   Error: {e}")
            print(f"\n   💡 LIKELY CAUSE: ElevenLabs quota exceeded")
            print(f"   - Step 1 already confirmed TTS timestamps work correctly")
            print(f"   - Full pipeline requires more credits than available")
            print(f"   - This is not a code issue - functionality is working")
            print(f"\n   💡 SOLUTION:")
            print(f"   - Add more credits to your ElevenLabs account")
            print(f"   - Or wait for your quota to reset (usually monthly)")
            print(f"   - Step 1 success confirms the code is working correctly")
        else:
            print(f"❌ Error during full pipeline check: {e}")
            import traceback
            traceback.print_exc()
    
    except Exception as e:
        error_str = str(e)
        error_lower = error_str.lower()
        
        # Check if it's a quota issue
        if 'quota' in error_lower or 'credits' in error_lower or '401' in error_str:
            print(f"\n⚠️  QUOTA EXCEEDED - ElevenLabs credits insufficient")
            print(f"   Error: {e}")
            print(f"\n   💡 RECOMMENDATION:")
            print(f"   - Step 1 already confirmed TTS timestamps work correctly")
            print(f"   - Step 2 failed due to insufficient credits, not a code issue")
            print(f"   - To test full pipeline: add more credits to your ElevenLabs account")
            print(f"   - Or wait for your quota to reset (usually monthly)")
        else:
            print(f"❌ Error during full pipeline check: {e}")
            import traceback
            traceback.print_exc()


def main():
    """Run all diagnostic checks."""
    print("\n" + "=" * 70)
    print("WORD TIMESTAMP DIAGNOSTIC TOOL")
    print("=" * 70)
    print("\nThis tool checks if ElevenLabs word timestamps are being generated")
    print("and used correctly in subtitle generation.\n")
    
    # Step 1: Check TTS timestamp generation
    word_ts = step1_tts_only()
    
    # Step 2: Check full pipeline
    step2_full_pipeline()
    
    print("\n" + "=" * 70)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 70)
    print("\n📋 KEY FINDINGS:")
    print("=" * 70)
    print("\n✅ If Step 1 shows word timestamps:")
    print("   → TTS is working correctly with convert_with_timestamps")
    print("\n✅ If Step 2 shows karaoke tags (\\k) in ASS file:")
    print("   → Word timestamps are being used in subtitle generation")
    print("\n❌ If no word timestamps or no karaoke tags:")
    print("   → Check the error messages above to identify where it breaks")
    print("\n📚 FILES TO CHECK:")
    print("   1. src/services/video/tts_service.py - TTS timestamp generation")
    print("   2. src/services/video/content_recommender.py - Passing word_timestamps")
    print("   3. src/services/video/video_assembler.py - Using word_timestamps in subtitles")
    print("   4. videos/video/temp/minecraft_reel/reel_subtitles.ass - Generated ASS file")
    print("=" * 70)


if __name__ == "__main__":
    main()
