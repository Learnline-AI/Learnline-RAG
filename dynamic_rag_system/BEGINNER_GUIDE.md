# 🚀 Beginner's Guide: Testing Your Educational RAG System with Real NCERT PDFs

This guide will walk you through testing the system with your actual NCERT PDF files, step by step, assuming you're new to coding.

## 📋 What You'll Do
1. Find your NCERT PDF files
2. Set up the system to process them
3. Run the processing pipeline
4. See the educational content extracted and organized
5. Explore the results

## 🛠️ Step-by-Step Instructions

### Step 1: Find Your NCERT PDF File
First, you need a NCERT PDF file to test with.

**Option A: If you have NCERT PDFs**
- Look for files like "NCERT_Physics_Class9.pdf" or similar
- Note down the exact file path (we'll need this later)
- Example: `/Users/yourusername/Downloads/NCERT_Physics_Ch8.pdf`

**Option B: If you need a NCERT PDF**
- Go to [NCERT official website](https://ncert.nic.in/textbook.php)
- Download any Class 9 Physics PDF (Chapter 8 "Force and Motion" works great)
- Save it to your Downloads folder

### Step 2: Open Terminal (Command Line)
**On Mac:**
1. Press `Cmd + Space` to open Spotlight
2. Type "Terminal" and press Enter
3. A black window will open - this is where you'll type commands

**On Windows:**
1. Press `Windows key + R`
2. Type "cmd" and press Enter
3. A black window will open

### Step 3: Navigate to Your RAG System
Copy and paste this command (replace the path with your actual path):

```bash
cd "/Users/umangagarwal/Desktop/untitled folder 2/RAG/dynamic_rag_system"
```

**How to find your path:**
- On Mac: Right-click the folder, hold Option, click "Copy as Pathname"
- On Windows: Shift + right-click the folder, select "Copy as path"

### Step 4: Create a Simple Test Script

I'll create a simple script that you can run without knowing any coding:
