#!/usr/bin/env python3
"""Debug timing for the Minecraft reel pipeline.

Run with:
    uv run python tests/video/debug_reel_timing.py
"""
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.services.video.script_generator import ScriptGenerator
from src.services.video.tts_service import TTSService
from src.services.video.video_assembler import VideoAssembler
from src.models.course import Concept
from src.utils.config import Config


def main():
    print("=" * 70)
    print("MINECRAFT REEL PIPELINE TIMING DEBUG")
    print("=" * 70)
    
    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------
    print(f"\n[INFO] Project root: {project_root}")
    
    # Output dirs (separate debug folder so it doesn't clash with real videos)
    audio_dir = project_root / "videos" / "debug_audio"
    video_dir = project_root / "videos" / "debug_video"
    temp_dir = project_root / "videos" / "debug_temp"
    
    audio_dir.mkdir(parents=True, exist_ok=True)
    video_dir.mkdir(parents=True, exist_ok=True)
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    # Paths
    audio_path = audio_dir / "reel_timing_raw.mp3"
    subtitles_path = temp_dir / "reel_timing_subs.ass"
    video_output_path = video_dir / "reel_timing_output.mp4"
    
    # Minecraft source clip
    minecraft_source = Path(Config.MINECRAFT_REEL_SOURCE)
    print(f"[INFO] Minecraft source: {minecraft_source}")
    
    if not minecraft_source.exists():
        print("⚠️  Config.MINECRAFT_REEL_SOURCE does not exist – video assembly part will fail.")
        print("    You can still see timings for script + TTS + subtitles.")
    else:
        print("✅ Minecraft source found")
    
    # Services
    script_gen = ScriptGenerator()
    tts = TTSService()
    assembler = VideoAssembler()
    
    if not assembler.ffmpeg_available:
        print("❌ FFmpeg not available (VideoAssembler.ffmpeg_available is False).")
        return
    
    # Check for pre-scaled version (after assembler is created)
    pre_scaled_source = assembler._find_pre_scaled_video(minecraft_source)
    if pre_scaled_source:
        print(f"✅ Pre-scaled version found: {pre_scaled_source}")
        print(f"   Will use pre-scaled version for faster processing (no scaling/padding needed)")
    else:
        print(f"ℹ️  No pre-scaled version found - will use original source with scaling/padding")
    
    # Simple dummy concept just for timing
    concept = Concept(
        name="Transformers and Attention",
        description=(
            "How transformers use self-attention to weigh different parts of the input "
            "sequence when generating the next token."
        ),
    )
    
    topic = "NLP"
    subtopic = "Transformers"
    
    timings = {}
    
    # ------------------------------------------------------------------
    # STEP 1: Script generation (Mistral)
    # ------------------------------------------------------------------
    print("\n" + "-" * 70)
    print("[STEP 1] Script generation (Mistral)")
    print("-" * 70)
    
    t0 = time.perf_counter()
    script = script_gen.generate_script(topic, subtopic, concept)
    t1 = time.perf_counter()
    
    timings["script_generation"] = t1 - t0
    
    word_count = len(script.split())
    print(f"  - Script length: {word_count} words, {len(script)} characters")
    print(f"  ✅ Done in {timings['script_generation']:.3f}s")
    
    # Estimate duration from script
    est_duration = script_gen.estimate_duration(script, words_per_minute=Config.REEL_WORDS_PER_MINUTE)
    print(f"  - Estimated duration: {est_duration:.2f}s (based on WPM={Config.REEL_WORDS_PER_MINUTE})")
    
    # ------------------------------------------------------------------
    # STEP 2: TTS with timestamps (ElevenLabs)
    # ------------------------------------------------------------------
    print("\n" + "-" * 70)
    print("[STEP 2] TTS (ElevenLabs, with timestamps)")
    print("-" * 70)
    
    if not tts.elevenlabs_available:
        print("⚠️  ElevenLabs not configured (no API key) – TTS will use dummy audio.")
    
    t0 = time.perf_counter()
    tts_result = tts.text_to_speech(str(script), str(audio_path), return_timestamps=True)
    t1 = time.perf_counter()
    
    timings["tts"] = t1 - t0
    
    if isinstance(tts_result, tuple):
        audio_success, word_timestamps = tts_result
    else:
        audio_success = tts_result
        word_timestamps = None
    
    print(f"  - TTS success: {audio_success}")
    print(f"  - Word timestamps: {'yes' if word_timestamps else 'no'}")
    if word_timestamps:
        total_words = sum(len(words) for words in word_timestamps.values())
        print(f"  - Timestamps: {len(word_timestamps)} sentences, {total_words} words")
    print(f"  ✅ Done in {timings['tts']:.3f}s")
    
    if not audio_success:
        print("❌ Audio generation failed – aborting further steps.")
        _print_summary(timings)
        return
    
    # Probe raw audio duration
    raw_audio_duration = assembler._get_media_duration(str(audio_path))
    print(f"  - Raw audio duration: {raw_audio_duration:.2f}s")
    
    # Use same target-duration logic as your real pipeline
    estimated_duration = est_duration or raw_audio_duration
    target_duration = min(
        max(estimated_duration, Config.REEL_DURATION_TARGET_MIN),
        Config.REEL_DURATION_TARGET_MAX,
    )
    target_duration = max(target_duration, min(raw_audio_duration, Config.REEL_DURATION_TARGET_MAX))
    
    # ------------------------------------------------------------------
    # STEP 3: Subtitle generation (ASS with word highlighting)
    # ------------------------------------------------------------------
    print("\n" + "-" * 70)
    print("[STEP 3] Subtitle generation (ASS + karaoke)")
    print("-" * 70)
    
    final_duration = min(raw_audio_duration or target_duration, target_duration)
    if final_duration <= 0:
        final_duration = target_duration
    
    print(f"  - Final duration for subtitles: {final_duration:.2f}s")
    print(f"  - Using word timestamps: {'yes' if word_timestamps else 'no (heuristic mode)'}")
    
    t0 = time.perf_counter()
    assembler._write_subtitles_with_word_highlighting(
        script,
        final_duration,
        subtitles_path,
        word_timestamps=word_timestamps,
    )
    t1 = time.perf_counter()
    
    timings["subtitles"] = t1 - t0
    
    print(f"  - Subtitle file: {subtitles_path}")
    if subtitles_path.exists():
        file_size = subtitles_path.stat().st_size
        print(f"  - File size: {file_size:,} bytes")
        
        # Count dialogue lines
        content = subtitles_path.read_text(encoding='utf-8')
        dialogue_count = content.count('Dialogue:')
        karaoke_count = content.count(r'{\k')
        print(f"  - Dialogue events: {dialogue_count}")
        print(f"  - Karaoke tags: {karaoke_count}")
    
    print(f"  ✅ Done in {timings['subtitles']:.3f}s")
    
    # ------------------------------------------------------------------
    # STEP 4: Final video assembly (FFmpeg) - DETAILED BREAKDOWN
    # ------------------------------------------------------------------
    print("\n" + "-" * 70)
    print("[STEP 4] Final video assembly (FFmpeg) - Detailed Breakdown")
    print("-" * 70)
    
    if not minecraft_source.exists():
        print("⚠️  Minecraft source not found, skipping video assembly step.")
        _print_summary(timings)
        return
    
    # Determine which source to use (pre-scaled or original)
    actual_source = pre_scaled_source if pre_scaled_source else minecraft_source
    using_pre_scaled = pre_scaled_source is not None
    
    if using_pre_scaled:
        print(f"\n✅ Using pre-scaled video: {actual_source}")
        print(f"   This should be faster (no scaling/padding during encoding)")
    else:
        print(f"\nℹ️  Using original video: {actual_source}")
        print(f"   Will need to scale/pad during encoding (slower)")
    
    # Sub-timings for video assembly
    video_assembly_timings = {}
    
    # 4.1: Duration probing
    print("\n  [4.1] Probing video duration (ffprobe)")
    t0 = time.perf_counter()
    video_duration = assembler._get_media_duration(str(actual_source))
    t1 = time.perf_counter()
    video_assembly_timings["duration_probe"] = t1 - t0
    print(f"     ✅ Done in {video_assembly_timings['duration_probe']:.3f}s")
    
    if video_duration <= 0:
        print("❌ Invalid video source duration – cannot assemble video.")
        _print_summary(timings)
        return
    
    print(f"     - Video source duration: {video_duration:.2f}s")
    
    # 4.2: Setup and preparation
    print("\n  [4.2] Preparation (calculations, filter setup)")
    t0 = time.perf_counter()
    
    # Choose same cropping duration logic
    final_clip_duration = min(final_duration, video_duration, Config.REEL_DURATION_TARGET_MAX)
    start_max = max(video_duration - final_clip_duration, 0.0)
    start_time = 0.0
    
    if start_max > 0:
        import random
        start_time = random.uniform(0.0, start_max)
    
    # Build video filter - only include scale/pad if not using pre-scaled version
    if using_pre_scaled:
        # Pre-scaled version already has correct dimensions - just add subtitles
        video_filter = f"ass={subtitles_path}"
        print(f"     - Filter: subtitle overlay only (pre-scaled video, no scaling needed)")
    else:
        # Need to scale and pad
        video_filter = (
            f"scale={Config.VIDEO_WIDTH}:{Config.VIDEO_HEIGHT}:force_original_aspect_ratio=decrease,"
            f"pad={Config.VIDEO_WIDTH}:{Config.VIDEO_HEIGHT}:(ow-iw)/2:(oh-ih)/2,"
            f"ass={subtitles_path}"
        )
        print(f"     - Filter: scale + pad + subtitle overlay")
    
    cmd = [
        "ffmpeg",
        "-y",
        "-ss", f"{start_time:.3f}",
        "-i", str(actual_source),  # Use pre-scaled or original source
        "-i", str(audio_path),
        "-t", f"{final_clip_duration:.3f}",
        "-vf", video_filter,
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-c:v", Config.VIDEO_CODEC,
        "-preset", "veryfast",
        "-crf", "23", 
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-shortest",
        str(video_output_path),
    ]

    
    t1 = time.perf_counter()
    video_assembly_timings["preparation"] = t1 - t0
    print(f"     ✅ Done in {video_assembly_timings['preparation']:.3f}s")
    print(f"     - Clip duration: {final_clip_duration:.2f}s")
    print(f"     - Start time: {start_time:.2f}s")
    
    # 4.3: FFmpeg encoding (main operation)
    print("\n  [4.3] FFmpeg encoding (video processing + encoding)")
    if using_pre_scaled:
        print(f"     - Using pre-scaled video (faster - no scaling/padding)")
    else:
        print(f"     - Using original video (slower - scaling/padding during encoding)")
    print(f"     - Codec: {Config.VIDEO_CODEC}")
    print(f"     - Resolution: {Config.VIDEO_WIDTH}x{Config.VIDEO_HEIGHT}")
    
    # Use the original command (stats parsing will work from stderr)
    
    t0 = time.perf_counter()
    success = False
    ffmpeg_output_lines = []
    
    try:
        import subprocess
        # Use verbose logging to get more timing info
        # Capture stderr to see FFmpeg progress
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        stdout, stderr = process.communicate()
        ffmpeg_output_lines = stderr.split('\n') if stderr else []
        
        if process.returncode == 0:
            success = True
            # Parse FFmpeg output for timing info
            frame_count = 0
            fps = 0.0
            total_time = 0.0
            speed = 0.0
            
            for line in ffmpeg_output_lines:
                if 'frame=' in line:
                    # Extract frame info: frame=  123 fps= 30 q=...
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if 'frame=' in part:
                            try:
                                frame_count = int(parts[i].split('=')[1])
                            except (ValueError, IndexError):
                                pass
                        if 'fps=' in part:
                            try:
                                fps = float(parts[i].split('=')[1])
                            except (ValueError, IndexError):
                                pass
                        if 'time=' in part and i + 1 < len(parts):
                            try:
                                time_str = parts[i + 1]  # Time is usually the next token
                                # Parse HH:MM:SS.ms
                                time_parts = time_str.split(':')
                                if len(time_parts) == 3:
                                    total_time = float(time_parts[0]) * 3600 + float(time_parts[1]) * 60 + float(time_parts[2])
                            except (ValueError, IndexError):
                                pass
                        if 'speed=' in part:
                            try:
                                speed = float(parts[i].split('=')[1].replace('x', ''))
                            except (ValueError, IndexError):
                                pass
            
            if frame_count > 0:
                print(f"     - Frames processed: {frame_count}")
            if fps > 0:
                print(f"     - Encoding FPS: {fps:.2f}")
            if speed > 0:
                print(f"     - Encoding speed: {speed:.2f}x realtime")
            if total_time > 0:
                print(f"     - Video duration processed: {total_time:.2f}s")
        else:
            err = stderr or "Unknown error"
            print("     ❌ FFmpeg video assembly failed")
            if err:
                print(f"     Error: {err[:300]}")
    
    except subprocess.CalledProcessError as e:
        err = e.stderr.decode("utf-8", errors="ignore") if isinstance(e.stderr, bytes) else (e.stderr or "")
        print("     ❌ FFmpeg video assembly failed")
        if err:
            print(f"     Error: {err[:300]}")
    except Exception as e:
        print(f"     ❌ Video assembly error: {e}")
    
    t1 = time.perf_counter()
    video_assembly_timings["ffmpeg_encoding"] = t1 - t0
    
    # If encoding took most of the time, break it down further
    print(f"     ✅ Done in {video_assembly_timings['ffmpeg_encoding']:.3f}s")
    
    # 4.3.1: Optional - Test individual filter operations for deeper diagnosis
    # (Only runs if encoding is slow to help identify bottlenecks)
    if video_assembly_timings["ffmpeg_encoding"] > 3.0:  # Only if encoding takes > 3 seconds
        print("\n  [5.3.1] Optional Filter Performance Test")
        print("     ⚠️  This will take extra time but helps identify bottlenecks")
        print("     Testing individual filter operations on 5-second clip...")
        
        test_output_dir = temp_dir / "filter_tests"
        test_output_dir.mkdir(exist_ok=True)
        
        filter_tests = {
            "scale_only": f"scale={Config.VIDEO_WIDTH}:{Config.VIDEO_HEIGHT}:force_original_aspect_ratio=decrease",
            "scale+pad": f"scale={Config.VIDEO_WIDTH}:{Config.VIDEO_HEIGHT}:force_original_aspect_ratio=decrease,pad={Config.VIDEO_WIDTH}:{Config.VIDEO_HEIGHT}:(ow-iw)/2:(oh-ih)/2",
            "subtitles_only": f"ass={subtitles_path}",
            "full_filter": video_filter
        }
        
        filter_test_timings = {}
        
        for filter_name, filter_str in filter_tests.items():
            test_output = test_output_dir / f"test_{filter_name}.mp4"
            test_cmd = [
                "ffmpeg", "-y",
                "-ss", f"{start_time:.3f}",
                "-i", str(actual_source),  # Use same source as main encoding
                "-t", "5.0",  # Test with 5 seconds
                "-vf", filter_str,
                "-c:v", Config.VIDEO_CODEC,
                "-pix_fmt", "yuv420p",
                str(test_output)
            ]
            
            t0_test = time.perf_counter()
            try:
                subprocess.run(test_cmd, check=True, capture_output=True, timeout=30)
                t1_test = time.perf_counter()
                filter_test_timings[filter_name] = t1_test - t0_test
                # Cleanup test file
                if test_output.exists():
                    test_output.unlink()
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired, Exception) as e:
                filter_test_timings[filter_name] = None
                print(f"       ⚠️  {filter_name} test failed")
        
        if filter_test_timings and any(t for t in filter_test_timings.values() if t is not None):
            print("     📊 Filter timing comparison (5-second clip, normalized to per-second):")
            valid_times = [(name, t) for name, t in filter_test_timings.items() if t is not None]
            
            if valid_times:
                base_time = valid_times[0][1]  # Use first valid time as baseline
                for name, t in valid_times:
                    normalized = t / 5.0  # Normalize to per-second
                    relative = (t / base_time) * 100 if base_time > 0 else 0
                    print(f"       - {name:20s}: {t:.3f}s ({normalized:.3f}s/sec, {relative:.1f}% vs baseline)")
                
                # Identify slowest filter
                slowest_name, slowest_time = max(valid_times, key=lambda x: x[1])
                print(f"\n     🐌 Slowest filter: {slowest_name} ({slowest_time:.3f}s for 5s clip)")
                
                if 'subtitle' in slowest_name.lower() or 'ass' in slowest_name.lower():
                    print("     💡 Subtitle rendering is slow - consider:")
                    print("        * Reducing number of dialogue events")
                    print("        * Simplifying subtitle formatting")
                    print("        * Using simpler font rendering")
                elif 'scale' in slowest_name.lower():
                    print("     💡 Scaling is slow - consider:")
                    print("        * Pre-scaling source video to target resolution")
                    print("        * Using hardware acceleration for scaling")
                    print("        * Lower resolution target")
    
    # 4.4: File verification
    print("\n  [4.4] File verification")
    t0 = time.perf_counter()
    
    if video_output_path.exists():
        file_size = video_output_path.stat().st_size
        print(f"     - Output size: {file_size / 1_000_000:.2f} MB")
    else:
        print("     ⚠️  Output file not found")
    
    t1 = time.perf_counter()
    video_assembly_timings["verification"] = t1 - t0
    
    print(f"     ✅ Done in {video_assembly_timings['verification']:.3f}s")
    
    # Total video assembly time
    timings["video_assembly"] = sum(video_assembly_timings.values())
    
    print(f"\n  📊 Video Assembly Breakdown:")
    for name, t in video_assembly_timings.items():
        pct = (t / timings["video_assembly"] * 100) if timings["video_assembly"] > 0 else 0.0
        print(f"     - {name:20s}: {t:7.3f}s  ({pct:5.1f}%)")
    
    print(f"\n  ✅ Total video assembly: {timings['video_assembly']:.3f}s")
    if using_pre_scaled:
        print(f"  - ⚡ Used pre-scaled video (should be faster)")
    else:
        print(f"  - ℹ️  Used original video (scaling/padding during encoding)")
    print(f"  - Video success: {success}")
    print(f"  - Output: {video_output_path}")
    
    # ------------------------------------------------------------------
    # SUMMARY
    # ------------------------------------------------------------------
    _print_summary(timings)


def _print_summary(timings: dict):
    print("\n" + "=" * 70)
    print("TIMING SUMMARY")
    print("=" * 70)
    
    total = sum(timings.values())
    
    for name, t in timings.items():
        pct = (t / total * 100) if total > 0 else 0.0
        print(f" - {name:20s}: {t:7.3f}s  ({pct:5.1f}%)")
    
    print("-" * 70)
    print(f" - {'TOTAL':20s}: {total:7.3f}s  (100.0%)")
    print("=" * 70)
    
    # Identify bottlenecks
    if len(timings) > 0:
        max_time = max(timings.values())
        max_name = max(timings.items(), key=lambda x: x[1])[0]
        max_pct = (max_time / total * 100) if total > 0 else 0.0
        
        print(f"\n🐌 SLOWEST STEP: {max_name} ({max_time:.3f}s, {max_pct:.1f}%)")
        
        # Show optimization suggestions
        if max_pct > 50:
            print(f"\n💡 OPTIMIZATION SUGGESTIONS:")
            if max_name == "tts":
                print("   - TTS is the bottleneck - consider:")
                print("     * Using shorter scripts")
                print("     * Caching TTS results for repeated content")
                print("     * Using faster TTS model if available")
            elif max_name == "video_assembly":
                print("   - Video assembly is the bottleneck - consider:")
                print("     * Using lower resolution for faster encoding")
                print("     * Using hardware acceleration (GPU encoding with -hwaccel)")
                print("     * Reducing subtitle complexity (fewer dialogue events)")
                print("     * Using faster video codec preset (e.g., -preset ultrafast)")
                print("     * Breaking down video assembly sub-steps (see detailed output above)")
            elif max_name == "script_generation":
                print("   - Script generation is the bottleneck - consider:")
                print("     * Using a faster LLM model")
                print("     * Reducing script length requirements")
                print("     * Caching scripts for similar concepts")


if __name__ == "__main__":
    main()

