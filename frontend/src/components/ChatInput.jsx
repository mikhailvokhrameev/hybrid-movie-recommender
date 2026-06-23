import { useState, useRef } from 'react'

export default function ChatInput({ onSend, disabled }) {
  const [text, setText] = useState('')
  const inputRef = useRef(null)

  function handleSubmit(e) {
    e.preventDefault()
    if (!text.trim() || disabled) return
    onSend(text.trim())
    setText('')
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex gap-3 items-end">
      <textarea
        ref={inputRef}
        value={text}
        onChange={e => setText(e.target.value)}
        onKeyDown={handleKeyDown}
        disabled={disabled}
        rows={1}
        placeholder="Опишите, какой фильм ищете..."
        className="flex-1 resize-none bg-surface text-ink text-sm rounded-xl
                   px-4 py-3 placeholder:text-muted
                   border border-transparent
                   focus:outline-none focus:border-amber/40
                   disabled:opacity-50
                   transition-colors duration-150"
      />
      <button
        type="submit"
        disabled={disabled || !text.trim()}
        className="flex-shrink-0 w-10 h-10 rounded-xl bg-amber text-bg
                   flex items-center justify-center
                   hover:bg-amber-hover active:scale-95
                   disabled:opacity-30 disabled:cursor-not-allowed
                   transition-all duration-150"
        aria-label="Отправить"
      >
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M5 12h14M12 5l7 7-7 7" />
        </svg>
      </button>
    </form>
  )
}
