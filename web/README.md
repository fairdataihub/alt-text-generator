# Alt Text Generator - Web Proxy

A simple Nuxt.js web application that acts as a proxy for the Python alt text generator server. The web app provides a user-friendly interface to test the alt text generation API.

## Getting Started

### Prerequisites

You will need the following installed on your system:

- Node.js (v22.20.0 recommended via Volta)
- Yarn
- Python server running (see main project README)

### Setup

1. Install the dependencies

   ```bash
   yarn install
   ```

2. Configure the Python server URL (optional)

   The web app connects to the Python server at `http://localhost:5000` by default. To use a different URL, create a `.env` file:

   ```bash
   cp .env.example .env
   ```

   Then edit `.env` and set `PYTHON_SERVER_URL` to your Python server URL:

   ```env
   PYTHON_SERVER_URL=http://localhost:5000
   ```

3. Start the development server

   ```bash
   yarn dev
   ```

4. Open the application in your browser

   ```bash
   open http://localhost:3000
   ```

## Usage

The web application provides:

- **Index Page** (`/`): A simple form with two input fields:
  - **Image URL**: The URL of the image to generate alt text for (required)
  - **Prompt**: Optional custom prompt for the model (defaults to a standard alt text prompt)

- **API Endpoint** (`/api/generate`): A proxy endpoint that forwards requests to the Python server's `/generate` endpoint.

### API Usage

You can also use the API endpoint directly:

```bash
curl "http://localhost:3000/api/generate?imageUrl=https://example.com/image.jpg&prompt=Describe%20this%20image"
```

## Development

### Available Scripts

- `yarn dev` - Start development server
- `yarn build` - Build for production
- `yarn preview` - Preview production build
- `yarn lint` - Run linter
- `yarn lint:fix` - Fix linting issues

### UI

The application uses [Nuxt UI](https://ui.nuxt.com) and [Tailwind CSS](https://tailwindcss.com) for styling.

## Architecture

This is a minimal Nuxt.js application that:

1. Provides a simple web interface for testing the alt text generator
2. Acts as a proxy, forwarding API requests to the Python server
3. Handles errors and displays results in a user-friendly format

The Python server handles all the actual image processing and alt text generation using Ollama.
