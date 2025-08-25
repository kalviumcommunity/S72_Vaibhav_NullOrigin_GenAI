# NullOrigin - AI World & Lore Generator

An advanced AI-powered tool that generates rich, immersive fictional worlds and lore using Chain of Thought reasoning. Built with Node.js and modern AI technologies, this application helps writers, game developers, and worldbuilders create cohesive and detailed fantasy or sci-fi settings through structured AI prompting.

## Features

- **Chain of Thought Prompting**: Breaks down world-building into logical steps for coherent output
- **Modular Architecture**: Easy to extend with new generators and templates
- **Structured JSON Output**: Consistent format for easy integration with games or other applications
- **Customizable Generation**: Control over biome, culture, tone, and other world parameters
- **RESTful API**: Simple endpoints for easy integration with other tools
- **TypeScript Support**: Full type safety and modern JavaScript features
- **Comprehensive Logging**: Built-in logging with different log levels and file rotation
- **Input Validation**: Robust validation for all API endpoints
- **Error Handling**: Graceful error handling and reporting
- **Environment Configuration**: Easy configuration through environment variables

## Tech Stack

### Core Technologies
- **Node.js**: Backend runtime for building fast, modular APIs
- **Express.js**: Lightweight framework for routing and handling HTTP requests
- **Gemini**: Gemini model
-  CoT
- **Axios**: For making HTTP requests to Gemini's local REST API
- **Axios**: For making HTTP requests to Ollama's local REST API
- **dotenv**: For managing environment variables securely

### Development Tools
- **Package Manager**: npm
- **Build Tool**: TypeScript Compiler (tsc)
- **Linting**: ESLint with TypeScript support
- **Code Formatting**: Prettier
- **Testing**: Jest with Supertest
- **Logging**: Winston with daily rotation
- **API Testing**: Postman/Insomnia (recommended)

### Architecture
- **Design Pattern**: MVC (Model-View-Controller)
- **API Style**: RESTful
- **Error Handling**: Custom middleware with proper HTTP status codes
- **Validation**: express-validator
- **Security**: Helmet, CORS, rate limiting

## Getting Started

### Prerequisites
    
- Node.js 18+ and npm
- An OpenAI API key (or other LLM provider)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/ai-world-lore-generator.git
   cd ai-world-lore-generator
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Create a `.env` file in the root directory and add your API key:
   ```env
   # Server Configuration
   PORT=3000
   NODE_ENV=development
   
   # OpenAI Configuration
   OPENAI_API_KEY=your_openai_api_key_here
   OPENAI_MODEL=gpt-4
   
   # Application Settings
   LOG_LEVEL=debug
   MAX_REQUEST_SIZE=10mb
   
   # CORS Configuration
   CORS_ORIGIN=*
   CORS_METHODS=GET,POST,PUT,DELETE,OPTIONS
   
   # Rate Limiting
   RATE_LIMIT_WINDOW_MS=900000  # 15 minutes
   RATE_LIMIT_MAX=100  # 100 requests per window
   ```

### Running the Application

```bash
# Start the development server with hot-reload
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Run tests
npm test

# Lint code
npm run lint

# Format code
npm run format
```

## Project Structure

```
├── src/
│   ├── config/         # Configuration files and environment setup
│   ├── controllers/    # Request handlers
│   ├── middlewares/    # Express middlewares
│   ├── models/         # Data models and schemas (future database models)
│   ├── prompts/        # AI prompt templates
│   ├── routes/         # API route definitions
│   ├── services/       # Business logic and AI services
│   ├── types/          # TypeScript type definitions
│   ├── utils/          # Helper functions and utilities
│   ├── app.ts          # Express app setup and middleware
│   └── server.ts       # Server initialization and error handling
├── tests/              # Test files
├── .env.example        # Example environment variables
├── package.json
└── tsconfig.json
```

## API Endpoints

### World Generation
- `POST /api/v1/worlds` - Generate a new world
  - Body: `{ "biome": "fantasy", "culture": "nordic", "tone": "epic", ... }`
- `GET /api/v1/worlds/:id` - Get a specific world by ID
- `PATCH /api/v1/worlds/:id` - Update a world
- `DELETE /api/v1/worlds/:id` - Delete a world
- `GET /api/v1/worlds` - Get all worlds (with optional filtering)

### Lore Generation
- `POST /api/v1/lore/generate` - Generate lore for a world
- `GET /api/v1/lore/world/:worldId` - Get all lore for a specific world

## How It Works

1. **Input Processing**: The system takes user inputs (biome, culture, tone, etc.)
2. **Chain of Thought Prompting**: These inputs are processed through a structured Chain of Thought prompt
3. **AI Generation**: The AI generates world details step by step
4. **Structured Output**: The output is formatted as JSON for easy integration
5. **Optional Storage**: Worlds and lore can be stored for future reference

## Development

### Available Scripts

- `npm run dev` - Start development server with hot-reload
- `npm run build` - Build the application
- `npm start` - Start production server
- `npm test` - Run tests
- `npm run format` - Format code with Prettier

### Environment Variables

See `.env.example` for all available environment variables and their descriptions.

### Contributing(Github commiting)

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

