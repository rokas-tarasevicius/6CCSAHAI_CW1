#!/usr/bin/env python3
"""Verify that the application setup is correct."""

def verify_imports():
    """Test all critical imports."""
    print("🔍 Verifying imports...")
    
    try:
        from src.models.course import CourseStructure
        print("  ✅ Models")
    except ImportError as e:
        print(f"  ❌ Models: {e}")
        return False
    
    try:
        from src.services.llm.mistral_client import MistralClient
        print("  ✅ Mistral client")
    except ImportError as e:
        print(f"  ❌ Mistral client: {e}")
        return False
    
    try:
        from src.services.question.generator import QuestionGenerator
        print("  ✅ Question generator")
    except ImportError as e:
        print(f"  ❌ Question generator: {e}")
        return False
    
    try:
        from src.services.tracking.performance_tracker import PerformanceTracker
        print("  ✅ Performance tracker")
    except ImportError as e:
        print(f"  ❌ Performance tracker: {e}")
        return False
    
    try:
        from src.ui.pages.home import render_home_page
        from src.ui.pages.quiz import render_quiz_page
        from src.ui.pages.video_feed import render_video_feed_page
        print("  ✅ UI pages")
    except ImportError as e:
        print(f"  ❌ UI pages: {e}")
        return False
    
    return True


def verify_course_material():
    """Check that course material exists."""
    print("\n📚 Verifying course material...")
    
    from pathlib import Path
    course_file = Path("data/course_material.json")
    
    if course_file.exists():
        print("  ✅ Course material JSON exists")
        
        try:
            from src.utils.course_loader import CourseLoader
            course = CourseLoader.load_from_file(str(course_file))
            print(f"  ✅ Course loaded: {course.title}")
            print(f"     Topics: {len(course.topics)}")
            total_concepts = sum(
                len(concept) 
                for topic in course.topics 
                for subtopic in topic.subtopics 
                for concept in [subtopic.concepts]
            )
            print(f"     Total concepts: {total_concepts}")
            return True
        except Exception as e:
            print(f"  ❌ Failed to load course: {e}")
            return False
    else:
        print("  ❌ Course material not found")
        return False


def verify_tests():
    """Check test structure."""
    print("\n🧪 Verifying tests...")
    
    from pathlib import Path
    
    unit_tests = list(Path("tests/unit").glob("test_*.py"))
    llm_tests = list(Path("tests/llm").glob("test_*.py"))
    
    print(f"  ✅ Unit test files: {len(unit_tests)}")
    print(f"  ✅ LLM test files: {len(llm_tests)}")
    
    return True


def main():
    """Run all verification checks."""
    print("=" * 60)
    print("Adaptive Learning Platform - Setup Verification")
    print("=" * 60)
    
    all_good = True
    
    all_good &= verify_imports()
    all_good &= verify_course_material()
    all_good &= verify_tests()
    
    print("\n" + "=" * 60)
    if all_good:
        print("✅ All checks passed! Ready to run:")
        print("   uv run streamlit run app.py")
    else:
        print("❌ Some checks failed. Please review the errors above.")
    print("=" * 60)


if __name__ == "__main__":
    main()

