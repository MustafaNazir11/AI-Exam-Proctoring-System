#!/usr/bin/env python3
"""
Admin Tools for AI Exam Proctoring System
Utilities for database management and admin operations
"""

import os
import sys

def show_menu():
    """Display admin tools menu"""
    print("\n" + "="*50)
    print("AI Exam Proctoring System - Admin Tools")
    print("="*50)
    print("1. Register Admin User (admin_register.py)")
    print("2. Clear Database (clearData.py)")
    print("3. View Database Contents (view_database.py)")
    print("4. Exit")
    print("-"*50)

def run_tool(tool_name):
    """Run a specific admin tool"""
    try:
        os.system(f"python {tool_name}")
    except Exception as e:
        print(f"Error running {tool_name}: {e}")

def main():
    """Main admin tools interface"""
    while True:
        show_menu()
        choice = input("Select an option (1-4): ").strip()
        
        if choice == '1':
            run_tool('admin_register.py')
        elif choice == '2':
            run_tool('clearData.py')
        elif choice == '3':
            run_tool('view_database.py')
        elif choice == '4':
            print("Exiting admin tools...")
            break
        else:
            print("Invalid choice. Please select 1-4.")

if __name__ == "__main__":
    main()