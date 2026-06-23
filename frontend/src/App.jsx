import { useRef, useEffect } from 'react'
import { useChat } from './hooks/useChat'
import Header from './components/Header'
import ChatMessage from './components/ChatMessage'
import ChatInput from './components/ChatInput'
import WelcomeScreen from './components/WelcomeScreen'

export default function App() {
  const { messages, isStreaming, sendMessage, reset } = useChat()
  const scrollRef = useRef(null)
  const isEmpty = messages.length === 0

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages])

  return (
    <div className="flex flex-col h-svh">
      <Header onHomeClick={reset} showHome={!isEmpty} />

      {isEmpty ? (
        <WelcomeScreen onSuggestionClick={sendMessage} />
      ) : (
        <main
          ref={scrollRef}
          className="flex-1 overflow-y-auto px-4 py-6"
        >
          <div className="max-w-2xl mx-auto space-y-6">
            {messages.map((msg, i) => (
              <ChatMessage
                key={msg.id}
                message={msg}
                isStreaming={isStreaming}
                isLast={i === messages.length - 1}
              />
            ))}
          </div>
        </main>
      )}

      <footer className="sticky bottom-0 bg-bg/80 backdrop-blur-sm border-t border-surface px-4 py-3">
        <div className="max-w-2xl mx-auto">
          <ChatInput onSend={sendMessage} disabled={isStreaming} />
        </div>
      </footer>
    </div>
  )
}
