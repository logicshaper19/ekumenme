# Agricultural Chatbot Design System

A comprehensive design system adapted from the Sema design system, specifically tailored for agricultural chatbot applications. This design system provides components, tokens, and styling for building French agricultural AI assistant interfaces.

## 🌾 Features

- **Agricultural Context**: Colors, typography, and components designed for agricultural use cases
- **Voice Interface**: Specialized components for voice input/output in field conditions
- **Multi-Agent Support**: Visual design for 6 specialized agricultural agents
- **French Localization**: UI text and components optimized for French agricultural terminology
- **Responsive Design**: Mobile-first approach for field use
- **Accessibility**: WCAG compliant components for agricultural workers

## 🎨 Design Tokens

### Colors
- **Primary Green**: Agricultural brand colors
- **Earth Tones**: Natural soil and crop colors
- **Weather Colors**: Specific colors for weather conditions
- **Crop Colors**: Individual colors for different crop types
- **Status Colors**: Success, warning, error, and info variants

### Typography
- **Agricultural Scale**: Typography optimized for data display
- **French Support**: Proper font weights and sizes for French text
- **Agent Typography**: Specialized text styles for each agent type

## 🧩 Components

### AgriculturalCard
Specialized card component for displaying agricultural data with contextual styling.

```tsx
import { AgriculturalCard } from '@agricultural-chatbot/design-system'

<AgriculturalCard
  type="weather"
  status="warning"
  title="Conditions Météo"
  subtitle="Attention aux précipitations"
  icon={<WeatherIcon />}
>
  <WeatherData />
</AgriculturalCard>
```

### VoiceInterface
Voice input/output component optimized for field use.

```tsx
import { VoiceInterface } from '@agricultural-chatbot/design-system'

<VoiceInterface
  state="listening"
  transcript="J'ai appliqué 40 litres de Karate Zeon"
  onStartListening={() => startRecording()}
  onStopListening={() => stopRecording()}
/>
```

## 🚀 Installation

```bash
npm install @agricultural-chatbot/design-system
```

## 📖 Usage

### Basic Setup

```tsx
import '@agricultural-chatbot/design-system/dist/styles.css'
import { AgriculturalCard, VoiceInterface } from '@agricultural-chatbot/design-system'

function App() {
  return (
    <div className="agricultural-app">
      <AgriculturalCard type="farm-data" title="Données Exploitation">
        <FarmData />
      </AgriculturalCard>
      
      <VoiceInterface 
        state="idle"
        onToggle={() => console.log('Voice toggled')}
      />
    </div>
  )
}
```

### Tailwind CSS Integration

The design system is built on Tailwind CSS. Include the agricultural components in your Tailwind config:

```js
// tailwind.config.js
module.exports = {
  content: [
    './src/**/*.{js,ts,jsx,tsx}',
    './node_modules/@agricultural-chatbot/design-system/dist/**/*.js'
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f0fdf4',
          500: '#22c55e',
          600: '#16a34a',
          // ... other shades
        },
        earth: {
          50: '#fafaf9',
          500: '#78716c',
          // ... other shades
        },
        // ... other color extensions
      }
    }
  },
  plugins: [
    require('@agricultural-chatbot/design-system/tailwind')
  ]
}
```

## 🎯 Agent-Specific Styling

The design system includes specialized styling for each of the 6 agricultural agents:

### Farm Data Manager
- **Color**: Primary green
- **Icon**: Farm/house icon
- **Use Case**: Farm information, parcel data, interventions

### Regulatory & Product Compliance Advisor
- **Color**: Warning amber
- **Icon**: Shield/checkmark icon
- **Use Case**: AMM validation, regulatory compliance

### Weather Intelligence Advisor
- **Color**: Info blue
- **Icon**: Cloud/weather icon
- **Use Case**: Weather data, forecasts, conditions

### Crop Health Monitor
- **Color**: Success green
- **Icon**: Leaf/plant icon
- **Use Case**: Disease detection, crop health

### Operational Planning Coordinator
- **Color**: Primary green (darker)
- **Icon**: Calendar/planning icon
- **Use Case**: Work planning, scheduling

### Sustainability & Analytics Advisor
- **Color**: Earth brown
- **Icon**: Chart/analytics icon
- **Use Case**: Sustainability metrics, analytics

## 🎤 Voice Interface Features

### States
- **Idle**: Ready to listen
- **Listening**: Recording voice input
- **Processing**: Analyzing speech
- **Speaking**: Playing response
- **Error**: Recognition error

### Field Optimization
- Large touch targets for gloved hands
- High contrast colors for outdoor visibility
- Voice-first interaction design
- Offline-capable components

## 📱 Mobile-First Design

All components are designed mobile-first for field use:

- **Touch Targets**: Minimum 44px for gloved hands
- **Contrast**: High contrast for outdoor visibility
- **Typography**: Readable in various lighting conditions
- **Spacing**: Generous spacing for easy interaction

## 🌍 French Localization

The design system includes French text and terminology:

- **Voice Prompts**: "Appuyez pour parler", "Écoute en cours..."
- **Status Messages**: French agricultural terminology
- **Component Labels**: Proper French agricultural terms

## 🧪 Development

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Run tests
npm test

# Type checking
npm run type-check

# Linting
npm run lint
```

## 📄 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

For questions or support, please contact the Agricultural Chatbot team.
