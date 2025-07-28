# PDF Outline Extractor – Round 1A Submission

## Overview

This project is a submission for **Round 1A: Understand Your Document** under the Adobe India Hackathon. The objective is to extract structured outlines (bookmarks/headings) from PDF documents and convert them into machine-readable JSON format using Python and Docker.

---

## Folder Structure

PDFTOJSON/
 - input/ # Place input PDF files here (should be empty for judging)
 - output/ # Output JSON files will be saved here (should be empty for judging)
 - pdfconv.py # Main script that processes PDFs
 - requirements.txt # Python dependencies (PyMuPDF)
 - Dockerfile # Docker setup for building and running the script
 - README.md # This documentation file


---

## Technologies Used

- Python 3.10
- PyMuPDF (fitz) for PDF parsing
- Docker for containerization

---

## How It Works

1. Place one or more PDF files inside the `input/` folder.
2. The script processes each PDF:
   - If outlines (bookmarks) exist, they are extracted.
   - If not, a fallback method extracts bold or large headings heuristically.
3. JSON files corresponding to each input PDF are saved in the `output/` folder.

---

## How to Build and Run the Docker Image

### Step 1: Build the Docker Image

Run this in the terminal from inside the `PDFTOJSON/` folder:

```bash
docker build --platform linux/amd64 -t pdfjsonconverter:latest .
docker run --rm ^
  -v "%cd%\input:/app/input" ^
  -v "%cd%\output:/app/output" ^
  --network none ^
  pdfjsonconverter:latest
