# WorkProof Frontend

Modern React + TypeScript admin dashboard for the WorkProof work verification platform.

## Features

- **Authentication**: Secure login with JWT tokens
- **Admin Dashboard**: Real-time employee activity monitoring
- **Reports**: Generate and export PDF/Excel reports
- **Responsive Design**: Mobile-friendly interface
- **Modern UI**: Built with TailwindCSS

## Tech Stack

- **React 18** with TypeScript
- **Vite** for fast development
- **TailwindCSS** for styling
- **React Router** for navigation
- **Axios** for API calls
- **Recharts** for data visualization
- **Lucide React** for icons

## Setup

1. Install dependencies:
```bash
npm install
```

2. Configure environment:
```bash
cp .env.example .env
# Edit .env with your API URL
```

3. Run development server:
```bash
npm run dev
```

The app will be available at `http://localhost:5173`

## Build for Production

```bash
npm run build
```

The production build will be in the `dist` directory.

## Project Structure

```
src/
├── components/          # Reusable components
│   ├── DashboardLayout.tsx
│   └── ProtectedRoute.tsx
├── contexts/            # React contexts
│   └── AuthContext.tsx
├── lib/                 # Utilities
│   └── api.ts
├── pages/               # Page components
│   ├── Login.tsx
│   ├── Dashboard.tsx
│   └── Reports.tsx
├── App.tsx              # Main app component
├── main.tsx             # Entry point
└── index.css            # Global styles
```

## Available Routes

- `/login` - Login page
- `/dashboard` - Main dashboard (protected)
- `/reports` - Reports page (protected)
- `/employees` - Employee management (admin only)
- `/settings` - Settings page (protected)

## Environment Variables

- `VITE_API_URL` - Backend API URL (default: http://localhost:5000)

## Development

The frontend uses Vite's hot module replacement for fast development. Changes will be reflected immediately in the browser.

## API Integration

The frontend communicates with the FastAPI backend through axios. All API calls are defined in `src/lib/api.ts` with automatic token refresh handling.

## Authentication

- Login credentials are stored in localStorage
- JWT tokens are automatically attached to API requests
- Token refresh is handled automatically
- Protected routes redirect to login if not authenticated

## License

Proprietary - Internal use only
