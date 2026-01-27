# Resume Matcher UI

A modern React frontend for the Resume Matcher AI-powered talent discovery system.

## Features

- 🎯 **Dashboard** - Overview of your resume database with real-time stats
- 🔍 **Match Candidates** - Find best candidates for job vacancies
  - **Fast Mode**: Embedding-based semantic search (instant, free)
  - **AI Mode**: LLM-powered deep analysis with skill matching and explanations
- 📄 **Resume Browser** - Search, filter, and view resume details
- 📤 **Import** - Upload files or batch import from directories
- 🌐 **Multilingual** - Full English and Russian interface support
- 📥 **Export** - Download results as CSV or PDF
- ⌨️ **Keyboard Shortcuts** - Ctrl+Enter to search
- 📧 **One-Click Copy** - Copy candidate emails for outreach
- 🔄 **Duplicate Detection** - Automatic duplicate prevention

## Tech Stack

- **React 18** with TypeScript
- **Vite** for fast development and builds
- **Tailwind CSS** for styling
- **React Router** for navigation
- **react-i18next** for internationalization
- **Lucide** for icons

## Getting Started

### Prerequisites

- Node.js 18+ (or Bun/pnpm)
- The Resume Matcher backend running on `localhost:8000`

### Development

```bash
# Install dependencies
npm install

# Start dev server (with proxy to backend)
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Production Build

```bash
# Build for production
npm run build

# Preview production build
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── api/
│   │   └── client.ts          # API client for backend
│   ├── components/
│   │   ├── Dashboard.tsx      # Main dashboard with stats
│   │   ├── Import.tsx         # Resume import interface
│   │   ├── Layout.tsx         # App layout with sidebar
│   │   ├── LanguageToggle.tsx # EN/RU language switcher
│   │   ├── Match.tsx          # Vacancy matching form
│   │   ├── MatchResults.tsx   # Match results display
│   │   └── ResumeList.tsx     # Resume browser
│   ├── i18n/
│   │   ├── index.ts           # i18n configuration
│   │   └── locales/
│   │       ├── en.json        # English translations
│   │       └── ru.json        # Russian translations
│   ├── utils/
│   │   └── export.ts          # CSV/PDF export utilities
│   ├── App.tsx                # Main app with routing
│   ├── index.css              # Global styles + Tailwind
│   └── main.tsx               # Entry point
├── public/
│   └── favicon.svg
├── index.html
├── package.json
├── tailwind.config.js
├── tsconfig.json
└── vite.config.ts
```

## Features in Detail

### Matching Modes

#### Fast Mode (Embedding Search)
- Instant results using semantic similarity
- No API costs (runs locally)
- Great for quick filtering

#### AI Mode (LLM Analysis)
- Deep candidate analysis
- Skill matching with explanations
- Strengths and concerns identification
- Multilingual output (keeps technical terms in English)

### Export Options

- **CSV**: Spreadsheet-compatible format with all match data
- **PDF**: Formatted report for sharing (coming soon)

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+Enter` | Submit search |
| `Ctrl+K` | Focus search (planned) |

## API Proxy

In development, API requests to `/api/*` are proxied to `http://localhost:8000/*`.

For production, configure your reverse proxy (nginx, Caddy, etc.):

```nginx
location /api/ {
    proxy_pass http://backend:8000/;
}

location / {
    root /var/www/frontend;
    try_files $uri $uri/ /index.html;
}
```

## Design System

The UI features a cyberpunk-inspired dark theme:

### Colors
- **Background**: Void colors (#0a0a0f, #12121a)
- **Accents**: Neon cyan, pink, purple, yellow
- **Cards**: Semi-transparent with subtle borders

### Components
- Grid pattern background for depth
- Smooth animations and transitions
- Responsive design (mobile + desktop)
- Glassmorphism effects on cards

## Environment Variables

Create a `.env` file for custom configuration:

```env
VITE_API_URL=http://localhost:8000  # Backend URL (optional)
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run `npm run build` to ensure it compiles
5. Submit a pull request

## License

MIT
