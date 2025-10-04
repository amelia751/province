# AI-Enhanced Explorer Panel

The AI-Enhanced Explorer Panel is a core component of Province Cursor that provides intelligent matter and case management for professional services. It transforms the traditional file explorer into a smart workspace that understands legal, accounting, tax, and compliance workflows.

## Features

### 🤖 AI-Driven Case Management
- **Smart Matter Organization**: AI-generated folder structures based on practice area and case type
- **Contextual Actions**: Right-click menus with AI-suggested next steps
- **Intelligent Filtering**: Filter by practice area, AI-generated status, deadlines, and more
- **Visual Indicators**: Shows AI-generated content, completion status, and urgency

### 📁 Professional Matter Structure
- **Hierarchical Organization**: Matters → Folders → Documents
- **Practice Area Specialization**: Customized for Legal, Accounting, Tax, and Compliance
- **Progress Tracking**: Visual progress indicators and completion percentages
- **Deadline Management**: Upcoming deadline alerts and priority indicators

### 🔍 Advanced Search & Filtering
- **Full-Text Search**: Search across matter names, clients, descriptions, and documents
- **Multi-Criteria Filtering**: Filter by status, priority, practice area, and more
- **AI-Generated Filter**: Show only AI-created matters and documents
- **Real-Time Results**: Instant filtering and search results

### 💬 Chat Integration
- **Conversational Actions**: "Ask AI for guidance" directly from context menus
- **Matter Creation**: Create new matters through chat requests
- **Contextual Requests**: AI understands current selection and context

## Usage

### Basic Usage

```tsx
import { EnhancedExplorerPanel } from '@/components/explorer-panel';

function MyApp() {
  return (
    <EnhancedExplorerPanel
      currentPracticeArea="legal"
      onMatterSelect={(matter) => console.log('Selected:', matter.name)}
      onDocumentSelect={(doc, matterId) => console.log('Open document:', doc.name)}
      onAIAction={(action) => console.log('AI Action:', action.action.label)}
      onChatRequest={(request) => console.log('Chat:', request.request)}
    />
  );
}
```

### With State Management Hook

```tsx
import { EnhancedExplorerPanel, useExplorerState } from '@/components/explorer-panel';

function MyApp() {
  const explorerState = useExplorerState({
    initialPracticeArea: 'legal',
    onMatterSelect: (matter) => {
      // Handle matter selection
      openMatterInEditor(matter);
    },
    onDocumentSelect: (document, matterId) => {
      // Handle document selection
      openDocumentInEditor(document);
    },
    onAIAction: (action) => {
      // Handle AI actions
      executeAIAction(action);
    },
    onChatRequest: (request) => {
      // Handle chat requests
      sendToChatPanel(request);
    }
  });

  return (
    <EnhancedExplorerPanel
      currentPracticeArea="legal"
      onMatterSelect={explorerState.selectMatter}
      onDocumentSelect={explorerState.selectDocument}
      onAIAction={explorerState.executeAIAction}
      onChatRequest={explorerState.sendChatRequest}
    />
  );
}
```

## Types

### Core Types

- `AIMatter`: Represents a legal case, tax return, audit, or compliance matter
- `AIDocument`: Professional documents with AI-generated metadata
- `AIFolder`: Smart folders with purpose descriptions and suggested templates
- `AIAction`: AI-suggested actions available for each matter
- `ExplorerFilter`: Filtering options for matters and documents

### Practice Areas

- `legal`: Legal cases, contracts, litigation
- `accounting`: Financial statements, audits, bookkeeping
- `tax`: Tax returns, planning, compliance
- `compliance`: Regulatory compliance, risk assessment

### Event Types

- `AIActionEvent`: Triggered when user selects an AI action
- `MatterSelectionEvent`: Triggered when a matter is selected
- `DocumentSelectionEvent`: Triggered when a document is selected
- `ChatRequestEvent`: Triggered when user requests AI assistance

## Mock Data

The component includes comprehensive mock data for development and testing:

- **3 Sample Matters**: Personal injury case, S-Corp tax return, SOX compliance
- **AI-Generated Structures**: Realistic folder hierarchies and documents
- **Deadlines & Actions**: Sample deadlines and AI-suggested actions
- **Multiple Practice Areas**: Examples across all supported domains

## Integration Points

### Chat Panel Integration
The explorer panel integrates seamlessly with the chat interface:
- Right-click "Ask AI for guidance" sends contextual requests
- "New Matter" button triggers chat-driven matter creation
- AI actions can be executed through chat commands

### Main Editor Integration
Document selection automatically opens files in the main editor:
- Document metadata includes AI generation context
- Real-time collaboration indicators
- Professional document type awareness

### Backend Integration
Ready for backend API integration:
- Async state management with loading states
- Error handling and retry logic
- Optimistic updates for better UX

## Customization

### Styling
The component uses Tailwind CSS classes and can be customized through:
- CSS class overrides
- Tailwind configuration
- Custom color schemes for practice areas

### Behavior
Customize behavior through props and hooks:
- Filter options and defaults
- Search behavior and indexing
- AI action handling
- Matter creation workflows

## Development

### Running the Example
```bash
# Start the development server
npm run dev

# Navigate to the explorer example
# The component includes a development debug panel
```

### Testing
```bash
# Run component tests
npm test explorer-panel

# Run type checking
npm run type-check
```

## Future Enhancements

- **Real-time Collaboration**: Live updates when team members modify matters
- **Advanced AI Actions**: More sophisticated AI-driven workflows
- **Custom Templates**: User-defined matter templates and structures
- **Integration APIs**: Connect with external practice management systems
- **Mobile Optimization**: Touch-friendly interface for tablets and phones

## Contributing

When contributing to the explorer panel:

1. Maintain TypeScript strict mode compliance
2. Add comprehensive mock data for new features
3. Update types and interfaces for new functionality
4. Include usage examples in documentation
5. Test across all practice areas

The AI-Enhanced Explorer Panel is designed to be the central hub for professional services workflow management, providing intelligent assistance while maintaining the familiar file explorer paradigm.