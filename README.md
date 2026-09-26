# Exposure Assessor

An AI Engineering Buildcamp capstone project that turns fragmented environmental data into screening-level chemical exposure risk profiles.

## The Problem

Public health researchers, environmental risk assessors, and community advocates often struggle to rapidly evaluate localized chemical exposure risks because critical data on industrial releases, chemical properties, and environmental transport variables are siloed across multiple disparate databases.

## What It Does

Exposure Assessor unifies public datasets, such as the EPA Toxics Release Inventory (TRI), with phenomenological transport models to automate screening-level exposure assessments. A user provides a location, facility, or chemical of interest, and the system pulls together release data, chemical properties, and transport modeling to return an actionable risk profile — transforming siloed environmental data into a starting point for further investigation.

## Setup

1. Install uv if you don't have it yet: https://docs.astral.sh/uv/getting-started/installation/

2. Clone this repository (or download the zip and extract it).

3. Create a `.env` file from the template and add your API key:

       cp .env.example .env

4. Install dependencies:

       uv sync

5. Start Jupyter:

       uv run jupyter notebook

## Notebooks

- `notebooks/01-setup.ipynb` - smoke test that confirms your environment works
- `notebooks/02-rag.ipynb` - a minimal RAG baseline you can adapt to your own data

## Data

Put your project data in the `data/` folder. See `notebooks/02-rag.ipynb` for how to load it.
