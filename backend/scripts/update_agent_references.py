#!/usr/bin/env python3
"""Update all script references from TaxPlanner to TaxPlannerAgent."""

import os
import glob
import re

def update_file_references(file_path):
    """Update TaxPlanner references in a single file."""
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Replace 'TaxPlannerAgent': with 'TaxPlannerAgent':
        updated_content = re.sub(
            r"'TaxPlannerAgent':",
            "'TaxPlannerAgent':",
            content
        )
        
        # Also replace "TaxPlannerAgent" in comments and strings
        updated_content = re.sub(
            r'"TaxPlannerAgent"',
            '"TaxPlannerAgent"',
            updated_content
        )
        
        # Check if any changes were made
        if updated_content != content:
            with open(file_path, 'w') as f:
                f.write(updated_content)
            return True
        
        return False
        
    except Exception as e:
        print(f"❌ Error updating {file_path}: {e}")
        return False


def main():
    """Update all Python scripts in the scripts directory."""
    
    print("🔄 UPDATING AGENT REFERENCES")
    print("=" * 50)
    print("Changing 'TaxPlanner' → 'TaxPlannerAgent' in all scripts")
    print("=" * 50)
    
    # Find all Python files in scripts directory
    scripts_dir = "/Users/anhlam/province/backend/scripts"
    python_files = glob.glob(os.path.join(scripts_dir, "*.py"))
    
    updated_files = []
    
    for file_path in python_files:
        file_name = os.path.basename(file_path)
        
        if update_file_references(file_path):
            print(f"✅ Updated: {file_name}")
            updated_files.append(file_name)
        else:
            print(f"⚪ No changes: {file_name}")
    
    print("=" * 50)
    print(f"📊 Updated {len(updated_files)} files:")
    
    for file_name in updated_files:
        print(f"   • {file_name}")
    
    print("=" * 50)
    print("✅ All references updated!")
    print("🎯 Agent name is now consistent: TaxPlannerAgent")


if __name__ == "__main__":
    main()
