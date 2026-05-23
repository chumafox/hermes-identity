---
name: playwright-scraper
description: Tool to automate web scraping using Playwright CLI for dynamic content extraction.
---
# Playwright Scraper Skill

This skill allows the agent to interact with modern, JavaScript-heavy websites (like Hugging Face) by launching a headless browser instance via Playwright.

## Prerequisites
1. Node.js and npm must be installed on the execution environment.
2. Playwright must be installed: `npm install playwright`

## Workflow
1. The agent will use the `playwright-scraper` tool to execute a script that launches Chromium/Firefox.
2. The agent will navigate to the target URL.
3. It will use CSS selectors (which may need manual adjustment based on site changes) to locate and extract dynamic content, such as file download links.
4. The output will be a list of extracted URLs or structured data saved to a file.

## Usage
Use the `playwright-scraper` tool with the target URL and any necessary selectors.

### Example Usage (Conceptual)
playwright-scraper(url="https://huggingface.co/mlx-community/Qwen3.5-9B-OptiQ-4bit", selector="a[href*='/blob/']")
