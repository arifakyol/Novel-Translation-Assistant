# Novel Translation Assistant

A powerful AI-driven tool for translating novels between different languages with advanced features for cultural adaptation, style guide generation, and quality control.

## Features

### Translation Capabilities
- **Multi-language Support**: English, Turkish, German, French, Spanish, Italian, Portuguese, Russian, Japanese, Chinese, Korean, Arabic, Hindi
- **Country-specific Adaptation**: Tailored translations for specific target countries
- **Automatic Language Detection**: Identifies source language automatically
- **Section-by-section Translation**: Breaks down novels into manageable sections
- **Back-translation Verification**: Quality control through reverse translation
- **Translation Memory**: Maintains consistency across translations

### Analysis Features
- **Character Analysis & Management**: Detailed character profiling and relationship mapping
- **Cultural Context Analysis**: Identifies cultural references, idioms, and social norms
- **Theme & Motif Analysis**: Extracts main themes and recurring motifs
- **Setting & Atmosphere Analysis**: Analyzes locations, time periods, and mood
- **Automatic Genre Detection**: Identifies literary genre characteristics

### Style & Quality Control
- **AI-Generated Style Guides**: Creates comprehensive translation style guides
- **Character Consistency**: Maintains character voices and personalities
- **Cultural Adaptation**: Adapts content for target culture while preserving authenticity
- **Line Editing Tools**: Refines translations for flow and readability
- **Quality Assurance**: Multiple verification stages

### User Interface
- **Intuitive GUI**: User-friendly interface built with tkinter
- **Real-time Progress Tracking**: Live updates during translation process
- **Section Editor**: Edit and manage novel sections
- **Character Editor**: Comprehensive character management interface
- **Novel Details Editor**: Edit cultural context, themes, and settings
- **Prompt Editor**: Customize AI prompts for different translation stages

### Data Management
- **JSON5 Format**: Modern JSON format with comments and trailing commas
- **Import/Export**: Character data, novel details, style guides, and sections
- **Multi-language UI**: Internationalization support with language files
- **Configuration Management**: Save and load translation settings

## Installation

### Prerequisites
- Python 3.8 or higher
- Windows, macOS, or Linux

### Setup
1. Clone or download the repository
2. Install required dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root with your API keys:
```env
# Choose your AI model (gemini or chatgpt)
AI_MODEL=gemini

# API Keys (choose based on your AI_MODEL)
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Optional: Specify allowed model variant
ALLOWED_MODEL=gemini-1.5-flash-latest

# Default target country
TARGET_COUNTRY=US
```

## Usage

### Getting Started
1. Launch the application:
```bash
python novel_translator.py
```

2. **Select Novel File**: Choose a text file containing your novel
3. **Configure Settings**:
   - Select target language and country
   - Choose novel genre
   - Set number of retry attempts
4. **Analyze Novel**: Click "Analyze Novel" to process the text
5. **Review Analysis**: Check character analysis, cultural context, themes, and settings
6. **Start Translation**: Begin the translation process
7. **Monitor Progress**: Watch real-time progress updates
8. **Save Results**: Export translated text, back-translation, and style guide

### Advanced Features

#### Character Management
- Edit character details, relationships, and development arcs
- Export/import character data
- Maintain character voice consistency

#### Style Guide Customization
- Generate AI-powered style guides
- Customize translation prompts
- Import/export style guides

#### Section Management
- Edit individual novel sections
- Add or remove sections
- Export/import section data

#### Prompt Customization
- Edit translation prompts for different stages
- Customize analysis prompts
- Reset to default prompts

## Supported File Formats
- **Text files** (.txt)
- **UTF-8 encoding** recommended for international characters

## Supported AI Models

### Google Gemini
- **Model**: gemini-1.5-flash-latest (default)
- **Features**: Fast processing, good for large texts
- **API**: Requires Google AI Studio API key

### OpenAI ChatGPT
- **Model**: gpt-4o-mini (default)
- **Features**: High quality translations, good context understanding
- **API**: Requires OpenAI API key

## Internationalization

The application supports multiple languages through JSON language files in the `lang/` directory:
- `en.json` - English
- `tr.json` - Turkish
- Additional language files can be added

## Project Structure
```
TRANS/
├── novel_translator.py      # Main application file
├── novel_analyzer.py        # Novel analysis engine
├── translator.py           # Translation engine
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── lang/                  # Language files
│   ├── en.json           # English translations
│   └── tr.json           # Turkish translations
└── .env                  # Environment variables (create this)
```

## Dependencies

### Core Dependencies
- `python-dotenv>=1.0.0` - Environment variable management
- `json5>=0.9.14` - Enhanced JSON parsing

### AI/ML Libraries
- `google-generativeai>=0.3.2` - Google Gemini API
- `openai>=1.12.0` - OpenAI API

### Language Processing
- `langdetect>=1.0.9` - Language detection

### Standard Library (included with Python)
- `tkinter` - GUI framework
- `re` - Regular expressions
- `time` - Time utilities
- `typing` - Type hints
- `os` - Operating system interface
- `threading` - Threading support

## Configuration

### Environment Variables
- `AI_MODEL`: Choose between "gemini" or "chatgpt"
- `GEMINI_API_KEY`: Your Google AI Studio API key
- `OPENAI_API_KEY`: Your OpenAI API key
- `ALLOWED_MODEL`: Specific model variant (optional)
- `TARGET_COUNTRY`: Default target country code

### Language Files
Create custom language files in the `lang/` directory following the format of existing files. Each file should contain key-value pairs for UI text translations.

## Troubleshooting

### Common Issues
1. **API Key Errors**: Ensure your API keys are correctly set in the `.env` file
2. **Language Detection**: Some texts may not be detected correctly; manual language selection may be needed
3. **Large Files**: Very large novels may take longer to process; consider breaking them into smaller sections
4. **Network Issues**: Ensure stable internet connection for AI API calls

### Performance Tips
- Use appropriate retry settings for your network conditions
- Consider using Gemini for faster processing of large texts
- Break very large novels into smaller files for better performance

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with Python and tkinter
- Powered by Google Gemini and OpenAI GPT models
- Uses langdetect for language identification
- JSON5 for enhanced JSON handling

## Support

For issues, questions, or contributions, please open an issue on the project repository.
