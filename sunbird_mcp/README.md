# Sunbird Content Search MCP Server

This is an MCP Server in Python implementing Sunbird content search tools. It provides the following features:

- **Search Sunbird Content**: A tool that searches Sunbird's educational content based on various filters and parameters
- **Read Sunbird Content**: A tool that retrieves artifact URLs for books by their content ID
- **Debug in [MCP Inspector](https://github.com/modelcontextprotocol/inspector)**: A feature that allows you to debug the MCP Server using the MCP Inspector

## Get started with the Sunbird Search MCP Server

> **Prerequisites**
>
> To run the MCP Server in your local dev machine, you will need:
>
> - [Python](https://www.python.org/)
> - (*Optional - if you prefer uv*) [uv](https://github.com/astral-sh/uv)
> - [Python Debugger Extension](https://marketplace.visualstudio.com/items?itemName=ms-python.debugpy)

## Suggested System Prompt to start with
You are a Resource Finder for learners, utilize the tools:
You can ask for follow up questions if necessary

1.search_sunbird_content to find the required resources 
VALID_FILTERS = {
    "primaryCategory": [
        "Digital Textbook", "eTextbook",
    ],
    "visibility": ["Default", "Parent"],
    "se_boards": ["CBSE", "State (Andhra Pradesh)"],
    "se_gradeLevels": [
        "Class 1", "Class 2", "Class 3", "Class 4", "Class 5",
        "Class 6", "Class 7", "Class 8", "Class 9", "Class 10",
        "Class 11", "Class 12"
    ],
    "se_mediums": ["English", "Hindi"],
"se_subjects"=[
  "Kannada","English","Hindi","Mathematics",
  "Physical Science","Biology","History","Geography","Civics",
  "Economics","Environmental Studies","Health & Physical Education",
  "Computer Applications","Art & Cultural Education - Music","Drawing"
]
}


VALID_FIELDS = [
    "name", "appIcon", "mimeType", "gradeLevel", "identifier", "medium", "pkgVersion",
    "board", "subject", "resourceType", "primaryCategory", "contentType", "channel",
    "organisation", "trackable", "se_boards", "se_subjects", "se_mediums", "se_gradeLevels",
    "me_averageRating", "me_totalRatingsCount", "me_totalPlaySessionCount"
]


VALID_FACETS = ["se_boards", "se_gradeLevels", "se_subjects", "se_mediums", "primaryCategory"]

After finding the relevant books, present the book names and document identifiers so that user can select which book he wants for further content link extraction 

2.read_sunbird_tool
Read sunbirdtool finds and retrieves the pdf links(streaming urls) to give to user based on content id given
the input needed by read_sunbird_tool is {content_id:"content id here"}



## Prepare environment

There are two approaches to set up the environment for this project. You can choose either one based on your preference.

> Note: Reload VSCode or terminal to ensure the virtual environment python is used after creating the virtual environment.

| Approach | Steps |
| -------- | ----- |
| Using `uv` | 1. Create virtual environment: `uv venv` <br>2. Run VSCode Command "***Python: Select Interpreter***" and select the python from created virtual environment <br>3. Install dependencies (include dev dependencies): `uv pip install -r pyproject.toml --extra dev` |
| Using `pip` | 1. Create virtual environment: `python -m venv .venv` <br>2. Run VSCode Command "***Python: Select Interpreter***" and select the python from created virtual environment<br>3. Install dependencies (include dev dependencies): `pip install -e .[dev]` |

## Available Tools

### 1. Search Sunbird Content
Searches for Sunbird content based on various filters and parameters. Supports:
- Primary category filtering (Digital Textbook, Course, etc.)
- Board filtering (CBSE, State boards)
- Grade level filtering (Class 1-12)
- Medium filtering (English, Hindi)
- Subject filtering
- Audience filtering (Student, Teacher)

### 2. Read Sunbird Content
Retrieves artifact URLs for books by their content ID:
- Extracts content IDs from books
- Filters out ECML content
- Returns streamable PDF URLs

## What's included in the template

| Folder / File| Contents                                     |
| ------------ | -------------------------------------------- |
| `.vscode`    | VSCode files for debugging                   |
| `.aitk`      | Configurations for AI Toolkit                |
| `src`        | The source code for the Sunbird search server |

## How to debug the Sunbird Search MCP Server

The same debugging options as before remain available: Using .vscode is highly useful
- Debug in Agent Builder
- Debug in MCP Inspector

## Default Ports and customizations

| Debug Mode | Ports | Definitions | Customizations |
| ---------- | ----- | ------------ | -------------- |
| Agent Builder | 3001 | [tasks.json](.vscode/tasks.json) | Edit configuration files to change ports |
| MCP Inspector | 3001 (Server); 5173 and 3000 (Inspector) | [tasks.json](.vscode/tasks.json) | Edit configuration files to change ports |

## Feedback

If you have any feedback or suggestions for this template, please open an issue on the [AI Toolkit GitHub repository](https://github.com/microsoft/vscode-ai-toolkit/issues)