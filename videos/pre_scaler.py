#!/usr/bin/env python3
"""Pre-scale and pad Minecraft source video to target resolution.

This script processes the Minecraft source video once to the target resolution,
so that FFmpeg doesn't need to do scaling/padding during video assembly (much faster).

Run with:
    uv run python videos/pre_scaler.py
"""
import sys
import subprocess
from pathlib import Path

# Add project root to path (videos/ is one level down from project root)
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.config import Config


def get_video_dimensions(video_path: Path) -> tuple[int, int] | None:
    """Get video width and height using ffprobe.
    
    Args:
        video_path: Path to video file
        
    Returns:
        Tuple of (width, height) or None if probe fails
    """
    try:
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            str(video_path)
        ]
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        lines = result.stdout.strip().split('\n')
        if len(lines) >= 2:
            width = int(lines[0].strip())
            height = int(lines[1].strip())
            return (width, height)
    except (subprocess.CalledProcessError, ValueError, IndexError) as e:
        print(f"⚠️  Failed to probe video dimensions: {e}")
    return None


def needs_scaling_padding(video_path: Path, target_width: int, target_height: int) -> bool:
    """Check if video needs scaling or padding.
    
    Args:
        video_path: Path to source video
        target_width: Target width
        target_height: Target height
        
    Returns:
        True if video needs processing, False if already matches target
    """
    dimensions = get_video_dimensions(video_path)
    
    if dimensions is None:
        print(f"⚠️  Could not determine video dimensions, assuming processing needed")
        return True
    
    width, height = dimensions
    
    print(f"📹 Source video dimensions: {width}x{height}")
    print(f"🎯 Target dimensions: {target_width}x{target_height}")
    
    # Check if dimensions match exactly
    if width == target_width and height == target_height:
        print("✅ Video already matches target resolution - no processing needed")
        return False
    
    # Video needs scaling/padding
    print(f"⚠️  Video dimensions don't match target - processing needed")
    return True


def pre_scale_video(
    source_path: Path,
    output_path: Path,
    target_width: int,
    target_height: int
) -> bool:
    """Pre-scale and pad video to target resolution.
    
    Args:
        source_path: Path to source video
        output_path: Path to save pre-scaled video
        target_width: Target width
        target_height: Target height
        
    Returns:
        True if successful, False otherwise
    """
    print(f"\n🔄 Pre-processing video...")
    print(f"   Source: {source_path}")
    print(f"   Output: {output_path}")
    
    # Video filter: scale to fit, then pad to exact size
    video_filter = (
        f"scale={target_width}:{target_height}:force_original_aspect_ratio=decrease,"
        f"pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2"
    )
    
    cmd = [
        'ffmpeg',
        '-y',  # Overwrite output
        '-i', str(source_path),
        '-vf', video_filter,
        '-c:v', 'libx264',
        '-preset', 'medium',  # Balanced quality/speed
        '-crf', '23',  # Good quality
        '-pix_fmt', 'yuv420p',
        '-an',  # No audio (we'll add audio during assembly)
        str(output_path)
    ]
    
    try:
        print("   Running FFmpeg... (this may take a minute)")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        if output_path.exists():
            file_size = output_path.stat().st_size
            print(f"   ✅ Pre-scaled video created: {file_size / 1_000_000:.2f} MB")
            
            # Verify dimensions
            dimensions = get_video_dimensions(output_path)
            if dimensions:
                width, height = dimensions
                if width == target_width and height == target_height:
                    print(f"   ✅ Verified: Output is {width}x{height} (correct)")
                    return True
                else:
                    print(f"   ⚠️  Warning: Output is {width}x{height} (expected {target_width}x{target_height})")
                    return False
        
        return False
        
    except subprocess.CalledProcessError as e:
        err = e.stderr.decode('utf-8', errors='ignore') if isinstance(e.stderr, bytes) else (e.stderr or "")
        print(f"   ❌ FFmpeg failed: {err[:300]}")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def main():
    """Main function to pre-scale Minecraft source video."""
    print("=" * 70)
    print("MINECRAFT VIDEO PRE-SCALER")
    print("=" * 70)
    print("\nThis script pre-processes the Minecraft source video to the target")
    print("resolution, allowing faster video assembly (no scaling/padding needed).\n")
    
    # Get source video path
    source_path = Path(Config.MINECRAFT_REEL_SOURCE)
    
    if not source_path.exists():
        print(f"❌ Source video not found: {source_path}")
        print(f"   Please ensure MINECRAFT_REEL_SOURCE is set correctly in config")
        return
    
    print(f"✅ Source video found: {source_path}")
    
    # Target dimensions from config
    target_width = Config.VIDEO_WIDTH
    target_height = Config.VIDEO_HEIGHT
    
    # Check if processing is needed
    if not needs_scaling_padding(source_path, target_width, target_height):
        print("\n✅ Source video already matches target resolution - no pre-processing needed!")
        return
    
    # Determine pre-scaled output path
    # Create a pre-scaled version next to the source
    source_dir = source_path.parent
    source_stem = source_path.stem
    pre_scaled_path = source_dir / f"{source_stem}_pre_scaled.mp4"
    
    # Check if pre-scaled version already exists and is correct
    if pre_scaled_path.exists():
        print(f"\n📦 Pre-scaled version found: {pre_scaled_path}")
        if not needs_scaling_padding(pre_scaled_path, target_width, target_height):
            print("✅ Pre-scaled version is correct - no re-processing needed!")
            print(f"   You can use this file directly for faster video assembly")
            return
        else:
            print("⚠️  Pre-scaled version exists but dimensions are wrong - re-processing...")
            pre_scaled_path.unlink()  # Remove incorrect version
    
    # Pre-scale the video
    print(f"\n🔄 Creating pre-scaled version...")
    success = pre_scale_video(source_path, pre_scaled_path, target_width, target_height)
    
    if success:
        print("\n" + "=" * 70)
        print("✅ PRE-SCALING COMPLETE")
        print("=" * 70)
        print(f"\n📁 Pre-scaled video: {pre_scaled_path}")
        print(f"📏 Dimensions: {target_width}x{target_height}")
        print(f"\n💡 The video assembler will automatically use this pre-scaled version")
        print(f"   for faster processing (no scaling/padding needed during encoding)")
    else:
        print("\n" + "=" * 70)
        print("❌ PRE-SCALING FAILED")
        print("=" * 70)
        print(f"\n⚠️  Could not create pre-scaled version")
        print(f"   Video assembly will fall back to scaling/padding during encoding")


if __name__ == "__main__":
    main()
