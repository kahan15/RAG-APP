import os
import subprocess
import sys

def main():
    """Generate all example data for testing."""
    print("Generating example data...")
    
    # Ensure we're in the right directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Create sample database
    print("\nCreating sample database...")
    try:
        import create_sample_db
        print("✓ Database created successfully")
    except Exception as e:
        print(f"✗ Error creating database: {str(e)}")
    
    # Create sample image
    print("\nCreating sample image...")
    try:
        import create_sample_image
        create_sample_image.create_sample_image()
        print("✓ Image created successfully")
    except Exception as e:
        print(f"✗ Error creating image: {str(e)}")
    
    # Verify sample article exists
    print("\nVerifying sample article...")
    if os.path.exists("sample_article.md"):
        print("✓ Sample article found")
    else:
        print("✗ Sample article not found")
    
    print("\nExample data generation complete!")

if __name__ == "__main__":
    main() 