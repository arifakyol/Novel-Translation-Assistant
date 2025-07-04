# Novel Translation Assistant

A powerful desktop application for analyzing, translating, and localizing novels with advanced AI support. The app provides a rich GUI for managing translation workflows, editing prompts, handling user-defined terminology, and supporting multiple languages and genres.

## Features

- **AI-Powered Novel Analysis**: Detects language, genre, characters, cultural context, main themes, motifs, and setting/atmosphere using Gemini or OpenAI models.
- **Section-Based Translation Workflow**: Splits novels into manageable sections for translation, line editing, cultural localization, and back-translation.
- **Prompt Editing**: Edit and manage all translation and analysis prompts via the GUI.
- **Style Guide Generation**: Automatically generate and update a style guide for consistent translation.
- **User-Defined Terminology**: Import, export, and manage custom term lists for translation consistency.
- **Multi-Language UI**: Supports multiple interface languages (English, Turkish, and more via `lang/` JSON files).
- **Import/Export**: Import/export prompts, style guides, sections, characters, and novel details as JSON or text files.
- **Rich GUI**: Built with Tkinter, featuring tabbed editors, progress bars, and detailed status/logging.
- **Error Handling & Logging**: Detailed error messages and logging for all major actions.

## Requirements

- Python 3.8+
- See `requirements.txt` for all dependencies.
- Gemini or OpenAI API key (for AI features)

## Installation

1. **Clone the repository:**
   ```
   git clone <repo-url>
   cd TRANS
   ```
2. **Install dependencies:**
   ```
   py -m pip install -r requirements.txt
   ```
3. **Set up API keys:**
   - Create a `.env` file in the project root with your API keys:
     ```
     GEMINI_API_KEY=your_gemini_api_key
     OPENAI_API_KEY=your_openai_api_key
     # Optionally restrict allowed model:
     # ALLOWED_MODEL=gemini-1.5-flash-latest
     ```

## Usage

1. **Run the application:**
   ```
   py novel_translator.py
   ```
2. **Select UI language** (top left dropdown, if multiple languages are available).
3. **Load a novel file** (`.txt`).
4. **Analyze the novel**: Detects language, genre, characters, cultural context, themes, and setting.
5. **Edit novel details, characters, and sections** as needed.
6. **Translate**: The app will process each section through initial translation, line editing, cultural localization, and back-translation.
7. **Edit prompts, style guide, and terminology** via the GUI.
8. **Import/export**: Use the menu/buttons to import/export prompts, style guides, sections, and terminology.

## Configuration

- **API Keys**: Required for AI features. Set in `.env` as shown above.
- **Language Files**: Place additional language JSON files in the `lang/` directory. Each file should follow the structure of `en.json` or `tr.json`.
- **Prompts**: Custom prompts can be edited in the GUI or loaded from `prompts.json`.

## Main UI Features

- **Tabbed Editors**: For sections, characters, prompts, and style guide.
- **Progress Bar & Status**: Shows translation progress and logs.
- **Prompt Management**: Edit, reset, import, and export all prompts (translation, analysis, style guide).
- **Section Editor**: Add, delete, and edit novel sections.
- **Character Editor**: Add, delete, and edit character details and relationships.
- **Style Guide Editor**: Generate, update, import, and export style guides.
- **Terminology Editor**: Manage user-defined terms for translation consistency.
- **Import/Export**: JSON/text import/export for all major data types.

## Troubleshooting

- **Missing API Key**: Ensure `.env` contains valid `GEMINI_API_KEY` or `OPENAI_API_KEY`.
- **Tkinter Not Installed**: On some Linux systems, install with `sudo apt-get install python3-tk`.
- **Language File Errors**: Ensure all language files in `lang/` are valid JSON and contain all required keys.
- **Prompt Errors**: If prompt variables are invalid, reset to default via the GUI.
- **Log File**: See `app.log` for detailed logs and error messages.

## License

MIT License. See LICENSE file for details.
