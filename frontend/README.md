# Frontend - Laundromat Tycoon

Executive War Room themed frontend for the Laundromat Tycoon simulation.

## Tech Stack

- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS v4 with custom design tokens
- **Animations**: Framer Motion
- **State Management**: Zustand
- **HTTP Client**: Axios

## Directory Structure

```
frontend/
├── src/
│   ├── components/     # Reusable UI components
│   │   ├── ui/         # Base UI primitives (modals, buttons)
│   │   ├── GlobalHUD.tsx       # Top navigation and status bar
│   │   ├── TacticalMap.tsx     # Isometric city map
│   │   ├── NeuralFeed.tsx      # AI thought stream display
│   │   ├── SocialFeed.tsx      # Event feed and reviews
│   │   ├── EquipmentCard.tsx   # Machine status cards
│   │   └── ...
│   ├── views/          # Page-level components
│   │   ├── OperationsView.tsx  # Equipment and inventory management
│   │   ├── FinanceView.tsx     # P&L and debt facility
│   │   ├── StrategyView.tsx    # Strategic planning
│   │   └── LegalView.tsx       # Regulatory compliance
│   ├── store/          # Zustand state stores
│   │   ├── gameStore.ts        # Game state (cash, locations, etc.)
│   │   └── eventStore.ts       # Event history and AI thoughts
│   ├── services/       # API communication
│   │   └── gameService.ts      # Backend API calls
│   ├── hooks/          # Custom React hooks
│   │   └── usePolling.ts       # Auto-refresh state/events
│   ├── App.tsx         # Main application component
│   ├── main.tsx        # Entry point
│   └── index.css       # Design system tokens and utilities
├── public/             # Static assets
├── index.html          # HTML template
├── vite.config.ts      # Vite configuration
└── package.json        # Dependencies
```

## Development

```bash
# Install dependencies
npm install

# Start dev server (proxies API to localhost:8000)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Design System

The frontend uses a **cyberpunk "Executive War Room"** aesthetic:

### Colors (HSL-based)
- `--color-void`: Deep black (#030508)
- `--color-neon-cyan`: Primary accent (#00f5ff)
- `--color-neon-green`: Success/positive (#39ff14)
- `--color-neon-pink`: Danger/accent (#ff006e)
- `--color-neon-purple`: Secondary accent (#bf00ff)

### Key Components
- `.glass-card`: Frosted glass panels with blur effect
- `.btn-primary`: Neon-bordered buttons
- `.data-value`: Tabular numeric displays
- `.terminal-text`: Monospace terminal styling

### Fonts
- **Display**: Outfit (headings)
- **Body**: Inter (text)
- **Mono**: JetBrains Mono (data, code)

## API Integration

The frontend communicates with the backend via REST API:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/state/{agent_id}` | GET | Fetch current game state |
| `/history/{agent_id}` | GET | Fetch event log |
| `/api/advance_day` | POST | Run simulation tick |
| `/api/start_game` | POST | Initialize new game |

API calls are handled by `gameService.ts` and state is managed by Zustand stores.

## Environment Variables

Create `.env.local` for local overrides:

```env
VITE_API_BASE_URL=http://localhost:8000
```

## Contributing

1. Follow the component patterns in existing files
2. Use TypeScript interfaces for all props
3. Add aria-labels to interactive elements
4. Use Framer Motion for all animations
