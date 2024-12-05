# SPARK Text Mining Platform

SPARK is a text mining platform based on the 3R (Rewrite, Retrieve, Reformat) methodology designed to significantly improve the efficiency of literature reviews for scientific research. It can extract and process research data from academic papers related to specific fields such as Solid Polymer Electrolytes (SPEs).

## Overview

A comprehensive literature review is often the first step in a scientific research project. Traditional literature reviews can take days or even weeks. SPARK, powered by the 3R methodology, can automate the entire process in just minutes.

The 3R methodology consists of three main modules:

1. **Rewrite**: Reformulates input queries into structured prompts that are easily understood by Large Language Models (LLMs). It identifies the research domain, key terminology, and context, ensuring relevant content can be easily found.
2. **Retrieve**: Preprocesses the collected literature and retrieves the most relevant paragraphs. It removes redundant content (e.g., headers, footers) and organizes the data into coherent blocks.
3. **Reformat**: Refines the retrieved data, performing text mining and structuring it into standardized formats, ensuring completeness and accuracy.

## Installation

To install the necessary dependencies, run:

```bash
pip install -r requirements.txt
