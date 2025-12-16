# AmaniQuery Chat Interface - Redesigned Components

This document describes the new AmaniQuery chat interface components that provide a cleaner, more streamlined user experience with enhanced features.

## Overview

The redesigned interface focuses on:
- **Clean, minimal design** - Reduced visual clutter and better organization
- **Real-time thinking process** - Shows reasoning during message generation
- **Inline citations** - Sources appear within text with hover tooltips
- **Contextual actions** - Actions appear on hover with compact menu options
- **Smooth animations** - Enhanced user experience with thoughtful transitions
- **Better source display** - Improved source presentation and filtering

## Component Architecture

### Core Components

#### 1. `AmaniMessage.tsx`
The main message component with clean design and inline citations.

**Features:**
- Clean avatar design with user/assistant distinction
- Inline citations with hover tooltips
- Markdown rendering with syntax highlighting
- Contextual action buttons (appear on hover)
- Smooth animations and transitions

**Usage:**
```tsx
<AmaniMessage
  message={message}
  onCopy={handleCopy}
  onRegenerate={handleRegenerate}
  onFeedback={handleFeedback}
  isLoading={false}
  showFeedback={true}
/>
```

#### 2. `ThinkingIndicator.tsx`
Real-time thinking process visualization.

**Features:**
- Shows thinking steps during message generation
- Expandable/collapsible with smooth animations
- Step-by-step progress indication
- Compact mode for minimal display
- Animated thinking indicators

**Usage:**
```tsx
<ThinkingIndicator
  isActive={isThinking}
  steps={thinkingSteps}
  currentStep={currentStep}
  defaultExpanded={false}
  onToggle={handleToggle}
/>
```

#### 3. `MessageActions.tsx`
Contextual message actions with compact menu.

**Features:**
- Actions appear on hover
- Compact mode with dropdown menu
- Full mode with all buttons visible
- Feedback integration (like/dislike)
- Export options (PDF/Word)
- Share functionality

**Usage:**
```tsx
<MessageActions
  message={message}
  onCopy={handleCopy}
  onRegenerate={handleRegenerate}
  onFeedback={handleFeedback}
  onShare={handleShare}
  onGeneratePDF={handleGeneratePDF}
  compact={true}
/>
```

#### 4. `AmaniInput.tsx`
Clean, modern input interface.

**Features:**
- Auto-resizing textarea
- Mode switching (Chat/Hybrid/Research)
- File upload with preview
- Autocomplete suggestions
- Voice input support
- Keyboard shortcuts
- Attachment management

**Usage:**
```tsx
<AmaniInput
  value={input}
  onChange={setInput}
  onSend={sendMessage}
  onFileSelect={handleFileSelect}
  onModeChange={handleModeChange}
  placeholder="Ask AmaniQuery anything..."
  mode="chat"
  attachments={attachments}
  showModeSelector={true}
/>
```

#### 5. `SourcePanel.tsx`
Enhanced source display with multiple variants.

**Features:**
- Panel, inline, and minimal display modes
- Category filtering
- Source icons and colors
- Expandable/collapsible sections
- Hover tooltips
- Source summaries

**Usage:**
```tsx
<SourcePanel
  sources={sources}
  isOpen={showSources}
  onToggle={toggleSources}
  variant="inline"
  maxHeight="400px"
/>
```

#### 6. `AmaniMessageList.tsx`
Streamlined message list with conversation grouping.

**Features:**
- Message grouping by conversation turn
- Inline thinking indicators
- Contextual action menus
- Source integration
- Welcome screen
- Loading states
- Smooth scrolling

**Usage:**
```tsx
<AmaniMessageList
  messages={messages}
  isLoading={isLoading}
  isThinking={isThinking}
  onSendMessage={sendMessage}
  onRegenerate={handleRegenerate}
  onFeedback={handleFeedback}
  onCopy={handleCopy}
  onShare={handleShare}
  showWelcomeScreen={true}
  enableThinkingIndicator={true}
  showInlineSources={true}
/>
```

#### 7. `AmaniChat.tsx`
Main chat orchestrator component.

**Features:**
- Complete chat interface
- Session management
- File upload handling
- Streaming responses
- Error handling
- OAuth integration
- Real-time updates

**Usage:**
```tsx
<AmaniChat
  showWelcomeScreen={true}
  enableThinkingIndicator={true}
  showInlineSources={true}
  enableVoice={false}
/>
```

## Key Improvements

### 1. Visual Design
- **Cleaner layout** - Reduced visual noise and better spacing
- **Better typography** - Improved text hierarchy and readability
- **Consistent colors** - Harmonized color scheme across components
- **Modern aesthetics** - Glassmorphism effects and subtle shadows

### 2. User Experience
- **Inline citations** - Sources appear directly in text with hover previews
- **Real-time feedback** - Thinking process visible during generation
- **Contextual actions** - Actions appear when needed, hidden otherwise
- **Smooth interactions** - Thoughtful animations and transitions

### 3. Performance
- **Lazy loading** - Components render only when needed
- **Optimized re-renders** - Efficient state management
- **Debounced inputs** - Improved responsiveness
- **Streaming support** - Real-time message updates

### 4. Accessibility
- **Keyboard navigation** - Full keyboard support
- **Screen reader support** - Proper ARIA labels and roles
- **High contrast** - Good color contrast ratios
- **Focus management** - Clear focus indicators

## Animation System

The interface includes a comprehensive animation system:

### Message Animations
```css
.animate-message-in      /* Slide-in for new messages */
.animate-thinking        /* Pulse for thinking state */
.animate-citation-hover  /* Glow for citation hover */
```

### Interaction Animations
```css
.animate-action-in       /* Fade-in for action buttons */
.animate-tooltip         /* Appear for tooltips */
.animate-input-focus     /* Focus animation for inputs */
```

### Panel Animations
```css
.animate-thinking-expand /* Expand for thinking panel */
.animate-source-slide    /* Slide for source panels */
```

## Usage Examples

### Basic Chat Interface
```tsx
import { AmaniChat } from '@/components/chat/AmaniChat'

export default function ChatPage() {
  return (
    <div className="min-h-screen">
      <AmaniChat 
        showWelcomeScreen={true}
        enableThinkingIndicator={true}
        showInlineSources={true}
      />
    </div>
  )
}
```

### Custom Message List
```tsx
import { AmaniMessageList } from '@/components/chat/AmaniMessageList'

function CustomChat({ messages, onSendMessage }) {
  return (
    <AmaniMessageList
      messages={messages}
      isLoading={false}
      onSendMessage={onSendMessage}
      onRegenerate={handleRegenerate}
      onFeedback={handleFeedback}
      onCopy={handleCopy}
      onShare={handleShare}
      showWelcomeScreen={messages.length === 0}
      enableThinkingIndicator={true}
      showInlineSources={true}
    />
  )
}
```

### Thinking Process Integration
```tsx
import { ThinkingIndicator } from '@/components/chat/ThinkingIndicator'

function ChatWithThinking({ isThinking, thinkingSteps }) {
  return (
    <div className="space-y-4">
      <ThinkingIndicator
        isActive={isThinking}
        steps={thinkingSteps}
        currentStep={currentStep}
        defaultExpanded={false}
        onToggle={handleToggle}
      />
      {/* Other chat components */}
    </div>
  )
}
```

## Testing

The components include comprehensive test coverage:

```bash
# Run all chat component tests
npm test frontend/src/components/chat

# Run specific component tests
npm test AmaniMessage.test.tsx
npm test AmaniChat.test.tsx

# Run with coverage
npm test -- --coverage frontend/src/components/chat
```

## Migration Guide

### From Old Components

1. **Replace MessageList with AmaniMessageList**
   ```tsx
   // Old
   <MessageList {...props} />
   
   // New
   <AmaniMessageList 
     messages={messages}
     isLoading={isLoading}
     onSendMessage={onSendMessage}
     onRegenerate={onRegenerate}
     onFeedback={onFeedback}
     onCopy={onCopy}
     onShare={onShare}
     showInlineSources={true}
     enableThinkingIndicator={true}
   />
   ```

2. **Replace ChatInput with AmaniInput**
   ```tsx
   // Old
   <ChatInput {...props} />
   
   // New
   <AmaniInput
     value={input}
     onChange={setInput}
     onSend={sendMessage}
     onFileSelect={handleFileSelect}
     onModeChange={handleModeChange}
     mode={mode}
     attachments={attachments}
     showModeSelector={true}
   />
   ```

3. **Replace ThinkingProcess with ThinkingIndicator**
   ```tsx
   // Old
   <ThinkingProcess reasoning={reasoning} />
   
   // New
   <ThinkingIndicator
     isActive={isThinking}
     steps={thinkingSteps}
     currentStep={currentStep}
     defaultExpanded={false}
   />
   ```

## Best Practices

### 1. State Management
- Keep message state in parent components
- Use local state for UI interactions (hover, expand, etc.)
- Implement proper cleanup for subscriptions

### 2. Performance
- Use React.memo for expensive components
- Implement proper key props for lists
- Debounce user inputs

### 3. Error Handling
- Always handle API errors gracefully
- Show user-friendly error messages
- Implement retry mechanisms

### 4. Accessibility
- Use semantic HTML elements
- Provide proper ARIA labels
- Ensure keyboard navigation works
- Test with screen readers

## Future Enhancements

### Planned Features
- **Voice input** - Speech-to-text integration
- **Rich media** - Enhanced image/video handling
- **Collaborative features** - Multi-user chat sessions
- **Advanced search** - Better source discovery
- **Mobile optimization** - Enhanced mobile experience

### Performance Improvements
- **Virtual scrolling** - For large message lists
- **Message caching** - Better performance for repeated queries
- **Background sync** - Offline message queuing
- **Progressive loading** - Load components as needed

## Support

For issues, questions, or contributions:
- Check the test files for usage examples
- Review the component props for customization options
- Submit issues through the project's issue tracker
- Follow the coding standards and guidelines

---

The new AmaniQuery chat interface provides a significantly improved user experience with cleaner design, better organization, and enhanced functionality while maintaining all the powerful features of the original implementation.